#!/usr/bin/env python3
"""
Prepare translation note prompts from an issue TSV.

Takes an issue TSV and produces a JSON file with everything Claude needs to
generate translation notes. No AI, no API calls -- pure data assembly.

Ported from tnwriter-dev pipeline (tsv_processor.py, ai_service.py,
language_converter.py, prompt_manager.py).

Usage:
    python3 prepare_notes.py output/issues/PSA-065.tsv \
        --ult-usfm /tmp/ult_plain.usfm \
        --ust-usfm /tmp/ust_plain.usfm \
        --output /tmp/prepared_notes.json
"""

import argparse
import csv
import html
import json
import os
import re
import subprocess
import sys

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
SKILL_DIR = os.path.dirname(SCRIPT_DIR)
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(SKILL_DIR)))

TEMPLATES_CSV = os.path.join(PROJECT_ROOT, 'data', 'templates.csv')
FETCH_TEMPLATES_SCRIPT = os.path.join(
    PROJECT_ROOT, '.claude', 'skills', 'create-issue-description', 'scripts', 'fetch_templates.py'
)
LANG_CONVERT_SCRIPT = os.path.join(SCRIPT_DIR, 'lang_convert.js')
GENERATE_IDS_SCRIPT = os.path.join(SCRIPT_DIR, 'generate_ids.py')
HEBREW_DIR = os.path.join(PROJECT_ROOT, 'data', 'hebrew_bible')

# Prompt templates (from tnwriter-dev/config/prompts.yaml)
WRITES_AT_PROMPT = """Return only the note.

Create a note to help Bible translators understand and address the issue identified `{sref}`.
Here is the text where the issue occurs: `{gl_quote}`.
Here is the full text of the verse: `{ult_verse}`.
Here is {book} {ref} in its context: `{ult_context}`

Here is where you are in the Bible (standard 3-character abbreviation): `{book} {ref}`.

The following input may or may not occur:

- Here is an explanation of the issue that will help you write the note. Information which must be included will be prefixed with `i:`. Information about which template to use will be prefixed with `t:`. If there are no prefixes, consider whether the text indicates a template type, something to include in the note, or context to help you understand the issue: `{explanation}`

{info}

If there is any data here, it is a previous note written by AI that the human editor did not find sufficient. Attempt to analyze the issue and return a different note: `{ai_tn}`

When you make the alternate translation, it should fit seamlessly back into the ULT such that if you remove the GLQuote `{gl_quote}` and replace it with the alternate translation it reads correctly. Here is the ULT for this verse: `{ult_verse}`

Check the UST for the same verse to make sure that your alternate translation is not the same as the UST. If it is, come up with another alternate translation idea. Here is the UST for that verse: `{ust_verse}`

Use the template(s) provided below. There may be more than one template; if so, discern which particular template is needed in this instance and use it. The explanation of the issue may indicate what template to use.

{templates}

Return only the note."""

GIVEN_AT_PROMPT = """Create a note to help Bible translators understand and address the issue identified `{sref}`.
Here is the text where the issue occurs: `{gl_quote}`. Return only the note, without an alternate translation.

Here is where you are in the Bible (standard 3-character abbreviation): `{book} {ref}`.
Here is the verse in context in a literal translation: `{ult_context}`.
Here is the verse in context in a simplified/amplified translation: `{ust_context}`

Here is an alternate translation that will help you identify the issue: `{at}`

The following input may or may not occur:
- Here is an explanation of the issue that will help you write the note. Information which must be included will be prefixed with `i:`. Information about which template to use will be prefixed with `t:`. If there are no prefixes, consider whether the text indicates a template type, something to include, or context: `{explanation}`

{info}

- If there is any data here, it is a previous note written by AI that the human editor did not find sufficient: `{ai_tn}`

Use the template(s) provided below. There may be more than one template; if so, discern which particular template is needed in this instance and use it.

{templates}

Return only the note."""

SEE_HOW_AT_PROMPT = """I need you to make an alternate translation, it should fit seamlessly back into the ULT (`{ult_verse}`) such that if you remove the GLQuote `{gl_quote}` and replace it with the alternate translation it reads correctly.

Here is where you are in the Bible (standard 3-character abbreviation): `{book} {ref}`.
Here is the verse in context in a literal translation: `{ult_context}`.
Here is the verse in context in a simplified/amplified translation: `{ust_context}`

Check the UST for the same verse to make sure that your alternate translation is not the same as the UST. If it is, come up with another alternate translation idea. Here is the UST for that verse: `{ust_verse}`

For reference here is a hint at the type of translation issue that we are addressing as well as a blank template:
issue type: {sref}

blank template: {template}

Return only the text of the generated alternate translation."""

TCM_INSTRUCTION = """IMPORTANT: This note should present multiple interpretations.
Format as: "This could mean: (1) [first interpretation]. Alternate translation: [AT for option 1] or (2) [second interpretation]. Alternate translation: [AT for option 2]"

Use the template below for context on what aspect needs explanation, but structure the note as a "this could mean" with numbered options."""


# ---------------------------------------------------------------------------
# 1. Parse input TSV
# ---------------------------------------------------------------------------

def parse_input_tsv(filepath):
    """Parse headerless 7-column issue TSV.

    Columns: Book, Ref, SRef, GLQuote, Go?, AT, Explanation

    Intro rows (reference like 'N:intro') are separated out and returned
    as a second list for passthrough to assembly.
    """
    items = []
    intro_rows = []
    book_code = None

    with open(filepath, 'r', encoding='utf-8') as f:
        for line_num, line in enumerate(f, start=1):
            line = line.rstrip('\n')
            if not line.strip():
                continue
            cols = line.split('\t')
            while len(cols) < 7:
                cols.append('')

            # Skip header row
            if line_num == 1 and cols[0].lower() == 'book':
                continue

            if book_code is None:
                book_code = cols[0].upper()

            # Detect intro rows and store separately
            if ':intro' in cols[1]:
                intro_rows.append({
                    'book': cols[0],
                    'reference': cols[1].strip(),
                    'content': cols[6].strip(),
                })
                continue

            items.append({
                'book': cols[0].upper() if cols[0] else book_code,
                'ref': cols[1].strip(),
                'sref': cols[2].strip(),
                'gl_quote': cols[3].strip(),
                'go': cols[4].strip(),
                'at': cols[5].strip(),
                'explanation': cols[6].strip(),
                'ai_tn': '',
                'line_num': line_num,
            })

    # Detect book/chapter from filename as fallback
    if not book_code:
        basename = os.path.basename(filepath)
        parts = basename.replace('_', '-').split('-')
        if parts and len(parts[0]) == 3 and parts[0].isalpha():
            book_code = parts[0].upper()

    return items, intro_rows, book_code


# ---------------------------------------------------------------------------
# 2. Load templates from CSV
# ---------------------------------------------------------------------------

def load_templates(templates_csv):
    """Load templates.csv with csv.DictReader (handles multi-line quoted fields).

    Returns dict: support_reference -> list of {type, note_template}
    """
    templates = {}

    with open(templates_csv, 'r', encoding='utf-8') as f:
        # Skip the date-stamp comment line
        first_line = f.readline()
        if not first_line.startswith('#'):
            f.seek(0)  # Not a comment, re-read

        reader = csv.DictReader(f)
        for row in reader:
            sref = row.get('support reference', '').strip()
            if not sref:
                continue
            entry = {
                'type': row.get('type', '').strip(),
                'note_template': row.get('note template', '').strip(),
            }
            templates.setdefault(sref, []).append(entry)

    return templates


def ensure_templates():
    """Fetch templates if not already fetched today."""
    if os.path.exists(FETCH_TEMPLATES_SCRIPT):
        subprocess.run(
            [sys.executable, FETCH_TEMPLATES_SCRIPT],
            capture_output=True, text=True
        )
    if not os.path.exists(TEMPLATES_CSV):
        print("ERROR: templates.csv not found at", TEMPLATES_CSV, file=sys.stderr)
        sys.exit(1)


# ---------------------------------------------------------------------------
# 3. Parse USFM files
# ---------------------------------------------------------------------------

def clean_usfm_text(text):
    """Strip USFM markers from text."""
    text = re.sub(r'\\zaln-[se][^\\]*', '', text)
    text = re.sub(r'\\\+?w\s+', '', text)
    text = re.sub(r'\\\+?w\*', '', text)
    text = re.sub(r'\\[a-z]+\d*\*?\s*', '', text)
    text = re.sub(r'\\\*', '', text)
    text = re.sub(r'\|[^\\|\s]*', '', text)
    text = re.sub(r'[{}]', '', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text


def parse_usfm_verses(usfm_path):
    """Parse USFM file and extract verses keyed by chapter:verse.

    Returns (verses_dict, context_dict):
        verses: {chapter:verse -> text}
        context: {chapter:verse -> text with surrounding verses}
    """
    if not os.path.exists(usfm_path):
        return {}, {}

    with open(usfm_path, 'r', encoding='utf-8') as f:
        content = f.read()

    current_chapter = None
    current_verse = None
    current_text_lines = []
    pending_front_matter = None

    # First pass: collect all verses
    all_verses = {}  # chapter -> [(verse_id, text)]
    verse_map = {}   # "chapter:verse" -> text

    def save_current_verse():
        nonlocal current_verse, current_text_lines, pending_front_matter
        if current_chapter and current_verse and current_text_lines:
            text = ' '.join(current_text_lines)
            text = clean_usfm_text(text)
            if current_verse == 'front':
                pending_front_matter = text
            else:
                key = f"{current_chapter}:{current_verse}"
                verse_map[key] = text
                all_verses.setdefault(current_chapter, []).append((current_verse, text))
        current_text_lines = []

    for line in content.split('\n'):
        chapter_match = re.match(r'\\c\s+(\d+)', line)
        if chapter_match:
            save_current_verse()
            current_chapter = chapter_match.group(1)
            current_verse = None
            if pending_front_matter:
                key = f"{current_chapter}:front"
                verse_map[key] = pending_front_matter
                all_verses.setdefault(current_chapter, []).append(('front', pending_front_matter))
                pending_front_matter = None
            continue

        verse_match = re.match(r'\\v\s+(\d+[-\d]*|front)\s*(.*)', line)
        if verse_match and current_chapter:
            save_current_verse()
            current_verse = verse_match.group(1)
            rest = verse_match.group(2).strip()
            if rest:
                current_text_lines.append(rest)
            continue

        if current_verse is None:
            continue

        stripped = line.strip()
        if stripped and not stripped.startswith('\\c ') and not stripped.startswith('\\v '):
            if stripped.startswith('\\') and re.match(r'^\\[a-z]+\s*$', stripped):
                continue
            current_text_lines.append(stripped)

    save_current_verse()

    # Build context dict (verse + surrounding 5 verses)
    context_map = {}
    for chapter, verse_list in all_verses.items():
        for idx, (verse_id, text) in enumerate(verse_list):
            start = max(0, idx - 5)
            end = min(len(verse_list) - 1, idx + 5)
            context_parts = []
            for ci in range(start, end + 1):
                v_id, v_text = verse_list[ci]
                context_parts.append(f"[{v_id}] {v_text}")
            key = f"{chapter}:{verse_id}"
            context_map[key] = ' '.join(context_parts)

    return verse_map, context_map


# ---------------------------------------------------------------------------
# 4. Language conversion
# ---------------------------------------------------------------------------

def prepare_converter_tsv(items):
    """Convert items to TSV format for lang_convert.js.

    Format: Reference\tID\tTags\tQuote\tOccurrence\tNote
    """
    lines = ['Reference\tID\tTags\tQuote\tOccurrence\tNote']
    for item in items:
        ref = item['ref']
        item_id = ''
        tags = item['sref']
        quote = html.unescape(item['gl_quote'])
        occurrence = '1'
        note_parts = []
        if item['explanation']:
            note_parts.append(item['explanation'])
        if item['at']:
            note_parts.append(f"AT: {item['at']}")
        note = ' '.join(note_parts)
        lines.append(f"{ref}\t{item_id}\t{tags}\t{quote}\t{occurrence}\t{note}")
    return '\n'.join(lines)


def run_language_conversion(items, book_code, aligned_usfm_path=None):
    """Run roundtrip language conversion via lang_convert.js.

    Returns list of dicts with OrigQuote and GLQuote per item.
    If aligned_usfm_path is provided, uses local file instead of remote API.
    """
    tsv_content = prepare_converter_tsv(items)
    if aligned_usfm_path:
        bible_link = f'file://{aligned_usfm_path}'
    else:
        bible_link = 'unfoldingWord/en_ult/master'

    try:
        result = subprocess.run(
            ['node', LANG_CONVERT_SCRIPT, 'roundtrip', bible_link, book_code, '-'],
            input=tsv_content,
            capture_output=True,
            text=True,
            timeout=120
        )
    except subprocess.TimeoutExpired:
        print("ERROR: Language conversion timed out", file=sys.stderr)
        return None

    if result.returncode != 0:
        print(f"ERROR: Language conversion failed: {result.stderr}", file=sys.stderr)
        return None

    try:
        parsed = json.loads(result.stdout)
    except json.JSONDecodeError:
        print(f"ERROR: Could not parse lang_convert output as JSON", file=sys.stderr)
        print(f"stdout: {result.stdout[:500]}", file=sys.stderr)
        return None

    # Parse the output TSV from the JSON result
    output_tsv = parsed.get('output', '')
    if not output_tsv:
        print("ERROR: No output from language conversion", file=sys.stderr)
        return None

    lines = output_tsv.strip().split('\n')
    if len(lines) < 2:
        return None

    headers = lines[0].split('\t')
    results = []
    for line in lines[1:]:
        if not line.strip():
            continue
        cols = line.split('\t')
        row = {}
        for i, h in enumerate(headers):
            row[h] = cols[i] if i < len(cols) else ''
        results.append(row)

    return results


# ---------------------------------------------------------------------------
# 5. Generate IDs
# ---------------------------------------------------------------------------

def generate_ids(book_code, count):
    """Generate unique IDs via generate_ids.py."""
    try:
        result = subprocess.run(
            [sys.executable, GENERATE_IDS_SCRIPT, book_code, str(count)],
            capture_output=True, text=True, timeout=30
        )
    except subprocess.TimeoutExpired:
        print("ERROR: ID generation timed out", file=sys.stderr)
        return None

    if result.returncode != 0:
        print(f"ERROR: ID generation failed: {result.stderr}", file=sys.stderr)
        return None

    ids = [line.strip() for line in result.stdout.strip().split('\n') if line.strip()]
    return ids


# ---------------------------------------------------------------------------
# 6. Template matching and prompt assembly
# ---------------------------------------------------------------------------

def get_templates_for_item(item, templates_db):
    """Get matching templates for an item by SRef."""
    sref = item['sref']
    return templates_db.get(sref, [])


def templates_have_at(templates):
    """Check if any of the matched templates contain 'Alternate translation:'."""
    for t in templates:
        if 'Alternate translation:' in t.get('note_template', ''):
            return True
    return False


def determine_note_type(item, needs_at):
    """Determine what type of note to create.

    Returns: 'writes_at', 'given_at', 'see_how_at', 'see_how'
    """
    explanation = item['explanation'].strip()
    at = item['at'].strip()

    if explanation.lower().startswith('see how'):
        if not at:
            return 'see_how_at'
        else:
            return 'see_how'

    if at:
        return 'given_at'
    else:
        return 'writes_at'


def parse_explanation(explanation):
    """Parse explanation for info prefix, template hint, and TCM mode.

    Returns: (clean_explanation, info_text, template_text, tcm_mode)
    """
    if not explanation:
        return "", "", "", False

    tcm_mode = False
    working = explanation.strip()
    if working.upper().startswith('TCM'):
        tcm_mode = True
        working = working[3:].strip()

    parts = re.split(r"\s*(?=[it]:)", working)
    info_segments = []
    template_segments = []
    remaining = []

    for part in parts:
        if part.startswith("i:"):
            info_segments.append(part[2:].strip())
        elif part.startswith("t:"):
            template_segments.append(part[2:].strip())
        else:
            if part.strip():
                remaining.append(part.strip())

    info_text = ""
    if info_segments:
        info_text = (
            "Be sure the note includes this information: " + " ".join(info_segments)
            + "\n If this information references another chapter and verse, format it "
            "according to these patterns: for a verse of the same chapter use "
            "[verse 2](../../jos/2/2.md), for same book different chapter use "
            "[chapter 3:3](../../jos/3/3.md), and for a different book use "
            "[Exodus 2:2](../../exo/2/2.md). Note that no zero-padding is used in the paths."
        )

    template_text = ""
    if template_segments:
        template_text = (
            "IMPORTANT: Use the template with type '"
            + " and ".join(template_segments)
            + "' from the templates below. Look for the template type that matches '"
            + " and ".join(template_segments) + "' and use that specific template."
        )

    clean_explanation = " ".join(remaining)
    return clean_explanation, info_text, template_text, tcm_mode


def format_templates(templates):
    """Format template list for inclusion in prompts.

    Strips the "Alternate translation" section from each template since the AT
    will be generated fresh by Claude.
    """
    if not templates:
        return "No templates available"

    formatted = []
    for t in templates:
        issue_type = t.get('type', '')
        note_template = t.get('note_template', '')
        # Strip AT section
        if 'Alternate translation' in note_template:
            note_template = note_template.split('Alternate translation')[0].strip()
        formatted.append(f"{issue_type}: {note_template}")

    return '\n\n'.join(formatted)


def assemble_prompt(item, templates, ult_verses, ult_context, ust_verses, ust_context):
    """Assemble the full prompt for a single item.

    Returns: (prompt_text, system_prompt_key, note_type, needs_at, tcm_mode)
    """
    matched = get_templates_for_item(item, templates)
    needs_at = templates_have_at(matched)
    note_type = determine_note_type(item, needs_at)

    clean_explanation, info_text, template_text, tcm_mode = parse_explanation(item['explanation'])

    # Format templates
    formatted_templates = format_templates(matched)
    if tcm_mode:
        formatted_templates = TCM_INSTRUCTION + "\n\n" + formatted_templates

    # Look up verse text
    ref = item['ref']
    ult_verse = ult_verses.get(ref, '')
    ult_ctx = ult_context.get(ref, ult_verse)
    ust_verse = ust_verses.get(ref, '')
    ust_ctx = ust_context.get(ref, ust_verse)

    # If GLQuote is empty, use the entire verse text
    gl_quote = item['gl_quote']
    if not gl_quote and ult_verse:
        gl_quote = ult_verse

    # Template variables
    tvars = {
        'book': item['book'],
        'ref': ref,
        'sref': item['sref'],
        'gl_quote': gl_quote,
        'at': item['at'],
        'explanation': clean_explanation,
        'info': info_text,
        'ai_tn': item['ai_tn'],
        'templates': formatted_templates,
        'ult_verse': ult_verse,
        'ult_context': ult_ctx,
        'ust_verse': ust_verse,
        'ust_context': ust_ctx,
        'template': formatted_templates,  # alias for see_how_at
    }

    # Clean None values
    for k, v in tvars.items():
        if v is None:
            tvars[k] = ''

    # Select prompt template
    prompt_map = {
        'writes_at': WRITES_AT_PROMPT,
        'given_at': GIVEN_AT_PROMPT,
        'see_how_at': SEE_HOW_AT_PROMPT,
        'see_how': GIVEN_AT_PROMPT,
    }
    prompt_template = prompt_map.get(note_type, WRITES_AT_PROMPT)

    try:
        prompt = prompt_template.format(**tvars)
    except KeyError as e:
        print(f"WARNING: Missing template variable {e} for {ref}", file=sys.stderr)
        prompt = prompt_template

    # Determine system prompt key
    if note_type in ('given_at', 'see_how'):
        system_prompt_key = 'given_at_agent'
    elif needs_at:
        system_prompt_key = 'ai_writes_at_agent'
    else:
        system_prompt_key = 'given_at_agent'

    return prompt, system_prompt_key, note_type, needs_at, tcm_mode


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description='Prepare translation note prompts from issue TSV',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    parser.add_argument('input_tsv', help='Input issue TSV file')
    parser.add_argument('--ult-usfm', required=True, help='Path to plain ULT USFM')
    parser.add_argument('--ust-usfm', required=True, help='Path to plain UST USFM')
    parser.add_argument('--output', '-o', default='/tmp/claude/prepared_notes.json',
                        help='Output JSON file (default: /tmp/claude/prepared_notes.json)')
    parser.add_argument('--skip-lang', action='store_true',
                        help='Skip language conversion (use original GLQuote)')
    parser.add_argument('--skip-ids', action='store_true',
                        help='Skip ID generation')

    args = parser.parse_args()

    # 1. Parse input
    print(f"Parsing input TSV: {args.input_tsv}", file=sys.stderr)
    items, intro_rows, book_code = parse_input_tsv(args.input_tsv)
    print(f"  Found {len(items)} items for {book_code}", file=sys.stderr)
    if intro_rows:
        print(f"  Found {len(intro_rows)} intro row(s) (will pass through to assembly)", file=sys.stderr)

    # Filter out items with tW articles (no note needed -- tW covers them)
    tw_filtered = [i for i in items if 'has tw article' not in i['explanation'].lower()]
    if len(tw_filtered) < len(items):
        print(f"  Filtered {len(items) - len(tw_filtered)} items with tW articles", file=sys.stderr)
        items = tw_filtered

    # Extract chapter from filename for output metadata
    basename = os.path.basename(args.input_tsv)
    chapter_match = re.search(r'-(\d+)', basename)
    chapter = chapter_match.group(1) if chapter_match else ''

    # 2. Fetch templates
    print("Ensuring templates are up to date...", file=sys.stderr)
    ensure_templates()
    templates_db = load_templates(TEMPLATES_CSV)
    print(f"  Loaded templates for {len(templates_db)} issue types", file=sys.stderr)

    # 3. Parse USFM
    print(f"Parsing ULT USFM: {args.ult_usfm}", file=sys.stderr)
    ult_verses, ult_context = parse_usfm_verses(args.ult_usfm)
    print(f"  Parsed {len(ult_verses)} ULT verses", file=sys.stderr)

    print(f"Parsing UST USFM: {args.ust_usfm}", file=sys.stderr)
    ust_verses, ust_context = parse_usfm_verses(args.ust_usfm)
    print(f"  Parsed {len(ust_verses)} UST verses", file=sys.stderr)

    # 4. Language conversion
    conversion_results = None
    if not args.skip_lang:
        # Check for local aligned ULT (from ULT-alignment phase)
        aligned_path = None
        aligned_candidate = os.path.join(PROJECT_ROOT, 'output', 'AI-ULT',
                                          f'{book_code}-{chapter}-aligned.usfm')
        if os.path.exists(aligned_candidate):
            aligned_path = aligned_candidate
            print(f"Using local aligned ULT: {aligned_path}", file=sys.stderr)
        else:
            print(f"No local aligned ULT found at {aligned_candidate}, using remote", file=sys.stderr)
        print(f"Running language conversion for {book_code}...", file=sys.stderr)
        conversion_results = run_language_conversion(items, book_code, aligned_path)
        if conversion_results:
            print(f"  Got {len(conversion_results)} conversion results", file=sys.stderr)
        else:
            print("  WARNING: Language conversion failed, using original quotes", file=sys.stderr)

    # 4b. Extract front/superscription Hebrew from source
    front_words = []
    hebrew_usfm = None
    for f in os.listdir(HEBREW_DIR):
        if f.upper().endswith(f'-{book_code}.usfm'.upper()):
            hebrew_usfm = os.path.join(HEBREW_DIR, f)
            break
    if hebrew_usfm and chapter:
        from fix_hebrew_quotes import extract_front_words
        front_words = extract_front_words(hebrew_usfm, chapter.lstrip('0') or '0')
        if front_words:
            print(f"  Extracted {len(front_words)} superscription words from Hebrew source", file=sys.stderr)

    # 5. Generate IDs
    ids = None
    if not args.skip_ids:
        print(f"Generating {len(items)} unique IDs for {book_code}...", file=sys.stderr)
        ids = generate_ids(book_code, len(items))
        if ids:
            print(f"  Generated {len(ids)} IDs", file=sys.stderr)
        else:
            print("  WARNING: ID generation failed", file=sys.stderr)

    # 6. Assemble prompts
    print("Assembling prompts...", file=sys.stderr)
    output_items = []

    for idx, item in enumerate(items):
        # Merge conversion data
        orig_quote = ''
        gl_quote_roundtripped = item['gl_quote']
        if conversion_results and idx < len(conversion_results):
            cr = conversion_results[idx]
            orig_quote = cr.get('Quote', '')
            gl_rt = cr.get('GLQuote', '').strip()
            if gl_rt:
                gl_quote_roundtripped = gl_rt

        # Assign ID
        item_id = ''
        if ids and idx < len(ids):
            item_id = ids[idx]

        # Assemble prompt
        prompt, sys_key, note_type, needs_at, tcm_mode = assemble_prompt(
            item, templates_db, ult_verses, ult_context, ust_verses, ust_context
        )

        ref = item['ref']
        entry = {
            'index': idx,
            'reference': ref,
            'sref': item['sref'],
            'gl_quote': item['gl_quote'],
            'orig_quote': orig_quote,
            'gl_quote_roundtripped': gl_quote_roundtripped,
            'id': item_id,
            'note_type': note_type,
            'needs_at': needs_at,
            'tcm_mode': tcm_mode,
            'prompt': prompt,
            'system_prompt_key': sys_key,
            'ult_verse': ult_verses.get(ref, ''),
            'ust_verse': ust_verses.get(ref, ''),
            'at_provided': item['at'],
            'explanation': item['explanation'],
        }

        # For front items, include source Hebrew words so the AI
        # can use the exact text instead of guessing
        if ref.endswith(':front') and front_words:
            entry['hebrew_front_words'] = front_words

        output_items.append(entry)

    # 7. Sort: front references first, then verse order
    def ref_sort_key(item):
        ref = item['reference']
        if ':' in ref:
            parts = ref.split(':', 1)
            verse = parts[1]
            if verse == 'front':
                return (0, 0)
            try:
                return (1, int(verse.split('-')[0]))
            except ValueError:
                return (1, 9999)
        return (1, 9999)

    output_items.sort(key=ref_sort_key)
    for idx, item in enumerate(output_items):
        item['index'] = idx

    # 8. Write output JSON
    output = {
        'book': book_code,
        'chapter': chapter,
        'source_file': os.path.abspath(args.input_tsv),
        'item_count': len(output_items),
        'items': output_items,
    }
    if intro_rows:
        output['intro_rows'] = intro_rows

    os.makedirs(os.path.dirname(args.output) or '.', exist_ok=True)
    with open(args.output, 'w', encoding='utf-8') as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    print(f"\nWrote {len(output_items)} prepared items to {args.output}", file=sys.stderr)


if __name__ == '__main__':
    main()
