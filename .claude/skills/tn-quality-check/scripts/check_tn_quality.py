#!/usr/bin/env python3
"""
Check AI-generated translation notes for quality issues.

Mechanical checks against the assembled TSV, prepared notes JSON, and ULT/UST.
Outputs a findings JSON for human review or further semantic analysis by Claude.

Usage:
    python3 check_tn_quality.py output/notes/PSA/PSA-147.tsv \
        --prepared-json /tmp/claude/prepared_notes.json \
        --ult-usfm /tmp/claude/ult_plain.usfm \
        --ust-usfm /tmp/claude/ust_plain.usfm \
        --book PSA \
        --output /tmp/claude/tn_quality_findings.json
"""

import argparse
import json
import os
import re
import sys
import unicodedata

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
SKILL_DIR = os.path.dirname(SCRIPT_DIR)
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(SKILL_DIR)))

TRANSLATION_ISSUES_CSV = os.path.join(PROJECT_ROOT, 'data', 'translation-issues.csv')


def load_valid_issues():
    """Load the set of valid issue slugs from translation-issues.csv."""
    valid = set()
    if not os.path.exists(TRANSLATION_ISSUES_CSV):
        return None  # Can't check; file missing
    with open(TRANSLATION_ISSUES_CSV, 'r', encoding='utf-8') as f:
        for i, line in enumerate(f):
            if i == 0:
                continue  # skip header
            slug = line.split(',')[0].strip()
            if slug:
                valid.add(slug)
    return valid

# Add tn-writer scripts to path for reuse
TN_WRITER_SCRIPTS = os.path.join(PROJECT_ROOT, '.claude', 'skills', 'tn-writer', 'scripts')
sys.path.insert(0, TN_WRITER_SCRIPTS)

# Conjunctions and prepositions that shouldn't be orphaned before an AT
CONJUNCTIONS = {'and', 'but', 'so', 'then', 'or', 'for', 'yet', 'nor'}
PREPOSITIONS = {'in', 'to', 'from', 'by', 'for', 'with', 'on', 'at', 'of',
                'into', 'upon', 'about', 'through', 'against', 'between'}


# ---------------------------------------------------------------------------
# Parsing helpers
# ---------------------------------------------------------------------------

def parse_tsv(tsv_path):
    """Parse assembled TN TSV into list of row dicts."""
    rows = []
    with open(tsv_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    if not lines:
        return rows

    headers = lines[0].rstrip('\n').split('\t')
    for i, line in enumerate(lines[1:], start=2):
        if not line.strip():
            continue
        cols = line.rstrip('\n').split('\t')
        row = {}
        for j, h in enumerate(headers):
            row[h] = cols[j] if j < len(cols) else ''
        row['_line'] = i
        rows.append(row)
    return rows


def parse_usfm_verses(usfm_path):
    """Parse plain USFM into {chapter:verse -> text} dict."""
    if not usfm_path or not os.path.exists(usfm_path):
        return {}

    with open(usfm_path, 'r', encoding='utf-8') as f:
        content = f.read()

    verses = {}
    current_chapter = None
    current_verse = None
    current_lines = []

    def save():
        nonlocal current_verse, current_lines
        if current_chapter and current_verse and current_lines:
            text = ' '.join(current_lines)
            text = re.sub(r'\\[a-z]+\d*\*?\s*', '', text)
            text = re.sub(r'\\\*', '', text)
            text = re.sub(r'\s+', ' ', text).strip()
            verses[f"{current_chapter}:{current_verse}"] = text
        current_lines = []

    for line in content.split('\n'):
        cm = re.match(r'\\c\s+(\d+)', line)
        if cm:
            save()
            current_chapter = cm.group(1)
            current_verse = None
            continue
        vm = re.match(r'\\v\s+(\d+[-\d]*)\s*(.*)', line)
        if vm and current_chapter:
            save()
            current_verse = vm.group(1)
            rest = vm.group(2).strip()
            if rest:
                current_lines.append(rest)
            continue
        if current_verse is not None:
            stripped = line.strip()
            if stripped and not stripped.startswith('\\c ') and not stripped.startswith('\\v '):
                if stripped.startswith('\\') and re.match(r'^\\[a-z]+\s*$', stripped):
                    continue
                current_lines.append(stripped)
    save()
    return verses


def parse_hebrew_source_words(hebrew_path):
    """Parse Hebrew source USFM into {chapter:verse -> [word_list]}.

    Each word_list is a list of Hebrew word strings (with cantillation) in verse order.
    """
    if not hebrew_path or not os.path.exists(hebrew_path):
        return {}

    with open(hebrew_path, 'r', encoding='utf-8') as f:
        content = f.read()

    verses = {}
    current_chapter = None
    current_verse = None
    current_words = []

    def save():
        nonlocal current_verse, current_words
        if current_chapter and current_verse and current_words:
            verses[f"{current_chapter}:{current_verse}"] = current_words
        current_words = []

    for line in content.split('\n'):
        cm = re.match(r'\\c\s+(\d+)', line)
        if cm:
            save()
            current_chapter = cm.group(1)
            current_verse = None
            continue
        vm = re.match(r'\\v\s+(\d+[-\d]*)', line)
        if vm and current_chapter:
            save()
            current_verse = vm.group(1)
        # Extract \w word|...\w* entries
        for m in re.finditer(r'\\w\s+([^|]+)\|[^\\]*?\\w\*', line):
            word = m.group(1).strip()
            if current_chapter and current_verse:
                current_words.append(word)
    save()
    return verses


def find_hebrew_usfm(book_code):
    """Auto-detect Hebrew source USFM for a book code."""
    import glob as globmod
    hebrew_dir = os.path.join(PROJECT_ROOT, 'data', 'hebrew_bible')
    pattern = os.path.join(hebrew_dir, f'*-{book_code.upper()}.usfm')
    matches = globmod.glob(pattern)
    return matches[0] if matches else None


def strip_braces(text):
    """Remove {curly braces} used for implied words in ULT."""
    return re.sub(r'\{([^}]*)\}', r'\1', text)


def has_rtl(text):
    """Check if text contains RTL (Hebrew/Arabic) characters."""
    for ch in text:
        if unicodedata.bidirectional(ch) in ('R', 'AL', 'AN'):
            return True
    return False


def extract_ats(note_text):
    """Extract alternate translation texts from [square brackets] after 'Alternate translation:'."""
    # Find all AT sections
    ats = []
    # Look for text after "Alternate translation:" and extract bracketed content
    at_pattern = re.compile(r'Alternate translation:\s*(.*?)(?=\n|$)', re.IGNORECASE)
    for m in at_pattern.finditer(note_text):
        section = m.group(1)
        brackets = re.findall(r'\[([^\]]+)\]', section)
        ats.extend(brackets)
    # Also catch any [bracketed] text after "Alternate translation:" across the note
    if not ats:
        # Fallback: find all brackets in the note
        all_brackets = re.findall(r'\[([^\]]+)\]', note_text)
        ats = all_brackets
    return ats


def extract_bold(note_text):
    """Extract all **bolded** text from note."""
    return re.findall(r'\*\*([^*]+)\*\*', note_text)


def find_gl_quote_in_ult(ult_verse, gl_quote):
    """Try to find gl_quote in ULT verse. Returns (index, success)."""
    clean_ult = strip_braces(ult_verse)
    clean_quote = strip_braces(gl_quote)
    if not clean_quote or not clean_ult:
        return -1, False
    # Direct match
    idx = clean_ult.find(clean_quote)
    if idx >= 0:
        return idx, True
    # Case-insensitive
    idx = clean_ult.lower().find(clean_quote.lower())
    if idx >= 0:
        return idx, True
    return -1, False


def substitute_at(ult_verse, gl_quote, at_text):
    """Substitute AT for gl_quote in ULT verse. Returns (result, success)."""
    clean_ult = strip_braces(ult_verse)
    clean_quote = strip_braces(gl_quote)
    if not clean_quote or not clean_ult:
        return None, False
    if clean_quote in clean_ult:
        return clean_ult.replace(clean_quote, at_text, 1), True
    idx = clean_ult.lower().find(clean_quote.lower())
    if idx >= 0:
        return clean_ult[:idx] + at_text + clean_ult[idx + len(clean_quote):], True
    return None, False


def get_word_before(text, substring):
    """Get the word immediately before a substring in text."""
    idx = text.lower().find(substring.lower())
    if idx <= 0:
        return None
    before = text[:idx].rstrip()
    if not before:
        return None
    words = before.split()
    return words[-1] if words else None


# ---------------------------------------------------------------------------
# Individual checks
# ---------------------------------------------------------------------------

def check_id_format(row):
    """Check 1: ID must match [a-z][a-z0-9]{3}."""
    note_id = row.get('ID', '')
    if row.get('Occurrence') == '0':
        return None  # Skip intro rows
    if not note_id:
        return {'severity': 'error', 'category': 'id_format',
                'message': 'Missing ID'}
    if not re.match(r'^[a-z][a-z0-9]{3}$', note_id):
        return {'severity': 'error', 'category': 'id_format',
                'message': f'ID "{note_id}" does not match [a-z][a-z0-9]{{3}}'}
    return None


def check_id_uniqueness(rows):
    """Check 2: No duplicate IDs within the file."""
    findings = []
    seen = {}
    for row in rows:
        note_id = row.get('ID', '')
        if not note_id or row.get('Occurrence') == '0':
            continue
        if note_id in seen:
            findings.append({
                'row': row['_line'], 'reference': row.get('Reference', ''),
                'id': note_id, 'severity': 'error', 'category': 'id_duplicate',
                'message': f'Duplicate ID "{note_id}" (first seen line {seen[note_id]})'
            })
        else:
            seen[note_id] = row['_line']
    return findings


def check_id_collisions(rows, book_code):
    """Check 3: No ID collisions with master TN."""
    findings = []
    try:
        from generate_ids import fetch_upstream_ids
        upstream_ids = fetch_upstream_ids(book_code)
    except Exception as e:
        findings.append({
            'row': 0, 'reference': '', 'id': '',
            'severity': 'warning', 'category': 'id_collision',
            'message': f'Could not fetch upstream IDs: {e}'
        })
        return findings

    for row in rows:
        note_id = row.get('ID', '')
        if not note_id or row.get('Occurrence') == '0':
            continue
        if note_id in upstream_ids:
            findings.append({
                'row': row['_line'], 'reference': row.get('Reference', ''),
                'id': note_id, 'severity': 'error', 'category': 'id_collision',
                'message': f'ID "{note_id}" already exists in master TN for {book_code}'
            })
    return findings


def check_hebrew_quote(row):
    """Check 4: Quote column must contain RTL Hebrew characters."""
    if row.get('Occurrence') == '0':
        return None
    quote = row.get('Quote', '')
    if not quote:
        return {'severity': 'error', 'category': 'empty_quote',
                'message': 'Quote column is empty'}
    if not has_rtl(quote):
        return {'severity': 'error', 'category': 'no_hebrew_in_quote',
                'message': f'Quote column has no Hebrew characters: "{quote[:40]}"'}
    return None


def check_at_bracket_syntax(row):
    """Check 5: ATs must use [square brackets]."""
    note = row.get('Note', '')
    if 'Alternate translation:' not in note and 'Alternate translation:' not in note:
        return None
    # Find the AT section
    at_match = re.search(r'Alternate translation:\s*(.+?)(?:\n|$)', note, re.IGNORECASE)
    if not at_match:
        return {'severity': 'warning', 'category': 'at_syntax',
                'message': 'Has "Alternate translation:" but no text follows'}
    at_section = at_match.group(1)
    if '[' not in at_section:
        return {'severity': 'error', 'category': 'at_syntax',
                'message': f'AT not in [square brackets]: "{at_section[:60]}"'}
    return None


def check_at_not_ust(row, ust_verses, prepared_items):
    """Check 6: AT must NOT match UST phrasing."""
    note = row.get('Note', '')
    ats = extract_ats(note)
    if not ats:
        return []

    ref = row.get('Reference', '')
    # Get UST verse from prepared items or parsed USFM
    ust_verse = ''
    item = prepared_items.get(row.get('ID', ''))
    if item:
        ust_verse = item.get('ust_verse', '')
    if not ust_verse:
        ust_verse = ust_verses.get(ref, '')
    if not ust_verse:
        return []

    findings = []
    ust_lower = ust_verse.lower()
    for at in ats:
        at_lower = at.lower().strip()
        if at_lower in ust_lower:
            findings.append({
                'severity': 'error', 'category': 'at_matches_ust',
                'message': f'AT [{at}] appears verbatim in UST: "{ust_verse[:80]}"'
            })
        elif len(at_lower) > 10:
            # Check high overlap (word-level)
            at_words = set(at_lower.split())
            ust_words = set(ust_lower.split())
            if len(at_words) > 2:
                overlap = len(at_words & ust_words) / len(at_words)
                if overlap > 0.85:
                    findings.append({
                        'severity': 'warning', 'category': 'at_similar_to_ust',
                        'message': f'AT [{at}] has {overlap:.0%} word overlap with UST'
                    })
    return findings


def check_gl_quote_in_ult(row, prepared_items):
    """Check 7: gl_quote must be findable in ULT verse."""
    if row.get('Occurrence') == '0':
        return None
    item = prepared_items.get(row.get('ID', ''))
    if not item:
        return None
    gl_quote = item.get('gl_quote_roundtripped') or item.get('gl_quote', '')
    ult_verse = item.get('ult_verse', '')
    if not gl_quote or not ult_verse:
        return None
    _, found = find_gl_quote_in_ult(ult_verse, gl_quote)
    if not found:
        return {'severity': 'error', 'category': 'gl_quote_not_in_ult',
                'message': f'gl_quote "{gl_quote}" not found in ULT verse'}
    return None


def check_bold_accuracy(row, prepared_items, ult_verses):
    """Check 8: Bolded text must appear verbatim in ULT verse."""
    note = row.get('Note', '')
    ref = row.get('Reference', '')
    bold_spans = extract_bold(note)
    if not bold_spans:
        return []

    # Get ULT verse
    ult_verse = ''
    item = prepared_items.get(row.get('ID', ''))
    if item:
        ult_verse = item.get('ult_verse', '')
    if not ult_verse:
        ult_verse = ult_verses.get(ref, '')
    if not ult_verse:
        return []

    clean_ult = strip_braces(ult_verse).lower()
    findings = []
    for bold in bold_spans:
        if bold.lower() not in clean_ult:
            findings.append({
                'severity': 'error', 'category': 'bold_not_in_ult',
                'message': f'Bolded text "{bold}" not found verbatim in ULT verse'
            })
    return findings


def check_no_rc_in_note(row):
    """Check 9: Note text must not contain rc:// links."""
    if row.get('Occurrence') == '0':
        return None  # Skip intro rows
    note = row.get('Note', '')
    if 'rc://' in note:
        return {'severity': 'error', 'category': 'rc_link_in_note',
                'message': 'Note contains rc:// link (belongs in SupportReference column only)'}
    return None


def check_orphaned_words(row, prepared_items):
    """Check 10: Orphaned conjunctions/prepositions before AT in substitution."""
    note = row.get('Note', '')
    ats = extract_ats(note)
    if not ats:
        return []

    item = prepared_items.get(row.get('ID', ''))
    if not item:
        return []
    gl_quote = item.get('gl_quote_roundtripped') or item.get('gl_quote', '')
    ult_verse = item.get('ult_verse', '')
    if not gl_quote or not ult_verse:
        return []

    findings = []
    for at in ats:
        result, success = substitute_at(ult_verse, gl_quote, f'[{at}]')
        if not success:
            continue
        # Find the word before [AT]
        idx = result.find(f'[{at}]')
        if idx <= 0:
            continue
        before = result[:idx].rstrip()
        if not before:
            continue
        word_before = before.split()[-1].lower().strip('.,;:!?')
        if word_before in CONJUNCTIONS:
            findings.append({
                'severity': 'warning', 'category': 'orphaned_conjunction',
                'message': f'Conjunction "{word_before}" orphaned before AT [{at}]'
            })
        elif word_before in PREPOSITIONS:
            # Only flag if the preposition is not part of the gl_quote
            gl_lower = strip_braces(gl_quote).lower()
            if not gl_lower.startswith(word_before):
                findings.append({
                    'severity': 'warning', 'category': 'orphaned_preposition',
                    'message': f'Preposition "{word_before}" orphaned before AT [{at}]'
                })
    return findings


def check_dropped_leading_conjunction(row, prepared_items):
    """Check 10b: AT drops a conjunction that the gl_quote starts with."""
    note = row.get('Note', '')
    ats = extract_ats(note)
    if not ats:
        return []

    item = prepared_items.get(row.get('ID', ''))
    if not item:
        return []
    gl_quote = item.get('gl_quote_roundtripped') or item.get('gl_quote', '')
    if not gl_quote:
        return []

    gl_first = gl_quote.strip().split()[0].lower().strip('.,;:!?') if gl_quote.strip() else ''
    if gl_first not in CONJUNCTIONS:
        return []

    findings = []
    for at in ats:
        at_first = at.strip().split()[0].lower().strip('.,;:!?') if at.strip() else ''
        # Allow a different conjunction (e.g. "and" → "so") but flag if no conjunction at all
        if at_first not in CONJUNCTIONS:
            findings.append({
                'severity': 'warning', 'category': 'dropped_conjunction',
                'message': f'gl_quote starts with "{gl_first}" but AT [{at}] drops it'
            })
    return findings


def check_writer_in_psalms(row, book_code):
    """Check 11: 'The writer' and 'the author' should not appear in Psalms notes.

    In Psalms, use the attributed name (David, Asaph, etc.) from the
    superscription, or 'the psalmist' for anonymous psalms. Never 'the author'
    or 'the writer'.
    """
    if book_code.upper() != 'PSA':
        return None
    if row.get('Occurrence') == '0':
        return None
    note = row.get('Note', '')
    if re.search(r'\bthe writer\b', note, re.IGNORECASE):
        return {'severity': 'warning', 'category': 'writer_in_psalms',
                'message': 'Uses "the writer" instead of "the psalmist" or attributed author'}
    if re.search(r'\bthe author\b', note, re.IGNORECASE):
        return {'severity': 'warning', 'category': 'author_in_psalms',
                'message': 'Uses "the author" — use the attributed name (David, Asaph, etc.) or "the psalmist" for anonymous psalms'}
    return None


def check_abstract_noun_at(row, prepared_items):
    """Check 14: figs-abstractnouns ATs must not contain abstract nouns."""
    sref = row.get('SupportReference', '')
    if 'figs-abstractnouns' not in sref:
        return []
    note = row.get('Note', '')
    ats = extract_ats(note)
    if not ats:
        return []

    # Get the gl_quote to know what abstract noun we're resolving
    item = prepared_items.get(row.get('ID', ''))
    gl_quote = ''
    if item:
        gl_quote = item.get('gl_quote_roundtripped') or item.get('gl_quote', '')

    findings = []
    # Specific known problem: "covenant faithfulness" AT using "love"
    if gl_quote and 'covenant faithfulness' in gl_quote.lower():
        for at in ats:
            if re.search(r'\blove\b', at, re.IGNORECASE):
                findings.append({
                    'severity': 'error', 'category': 'abstract_noun_in_at',
                    'message': f'AT [{at}] for "covenant faithfulness" uses abstract noun "love" -- verbalize instead (e.g. "being faithful to his covenant")'
                })
    return findings


def check_at_ending_punctuation(row, prepared_items):
    """Check 15: AT should not introduce ending punctuation unless proposing a punctuation change."""
    note = row.get('Note', '')
    ats = extract_ats(note)
    if not ats:
        return []

    # Rhetorical question notes intentionally change ? to . or !
    sref = row.get('SupportReference', '')
    is_rquestion = 'figs-rquestion' in sref

    item = prepared_items.get(row.get('ID', ''))
    if not item:
        return []
    gl_quote = item.get('gl_quote_roundtripped') or item.get('gl_quote', '')
    if not gl_quote:
        return []

    findings = []
    gl_stripped = gl_quote.rstrip()
    for at in ats:
        at_stripped = at.rstrip()
        if not at_stripped:
            continue
        last_char = at_stripped[-1]
        if last_char in '.?,!':
            # Check if the gl_quote also ends with that punctuation
            if not gl_stripped or gl_stripped[-1] != last_char:
                # For rquestion notes, the punctuation change (? -> . or !) is
                # intentional -- only flag if the AT *also* ends with ?
                if is_rquestion and gl_stripped and gl_stripped[-1] == '?' and last_char in '.!':
                    continue
                findings.append({
                    'severity': 'warning', 'category': 'at_ending_punctuation',
                    'message': f'AT [{at}] ends with "{last_char}" but gl_quote does not — '
                               f'remove unless proposing a punctuation change'
                })
    return findings


def check_rquestion_at_punctuation(row, prepared_items):
    """Check 21: figs-rquestion ATs must end with . or ! (not ? or no punctuation)."""
    sref = row.get('SupportReference', '')
    if 'figs-rquestion' not in sref:
        return []
    note = row.get('Note', '')
    ats = extract_ats(note)
    if not ats:
        return []

    item = prepared_items.get(row.get('ID', ''))
    gl_quote = ''
    if item:
        gl_quote = item.get('gl_quote_roundtripped') or item.get('gl_quote', '')
    # Only check when the gl_quote ends with ?
    if not gl_quote or not gl_quote.rstrip().endswith('?'):
        return []

    findings = []
    for at in ats:
        at_stripped = at.rstrip()
        if not at_stripped:
            continue
        last_char = at_stripped[-1]
        if last_char not in '.!':
            findings.append({
                'severity': 'warning', 'category': 'rquestion_missing_punctuation',
                'message': f'figs-rquestion AT [{at}] should end with . or ! '
                           f'(currently ends with "{last_char}")'
            })
    return findings


def check_support_reference(row, valid_issues):
    """Check 17: SupportReference must be a known issue from translation-issues.csv."""
    if row.get('Occurrence') == '0':
        return None
    sref = row.get('SupportReference', '').strip()
    if not sref:
        return None  # Empty is allowed (some notes have no support reference)
    if valid_issues is None:
        return None  # Can't validate; CSV missing
    # Support reference format: rc://*/ta/man/translate/SLUG
    # May contain multiple entries separated by whitespace or semicolons
    slugs = re.findall(r'rc://\*/ta/man/translate/([^\s;,]+)', sref)
    if not slugs:
        # Has a SupportReference but no rc:// links — flag it
        return {'severity': 'warning', 'category': 'support_ref_format',
                'message': f'SupportReference has no rc:// links: "{sref[:60]}"'}
    unknown = [s for s in slugs if s not in valid_issues]
    if unknown:
        return {'severity': 'error', 'category': 'unknown_support_ref',
                'message': f'SupportReference slug(s) not in translation-issues.csv: {unknown}'}
    return None


def check_at_starting_punctuation(row, prepared_items):
    """Check 18: AT should not start with punctuation unless proposing a change."""
    note = row.get('Note', '')
    ats = extract_ats(note)
    if not ats:
        return []

    item = prepared_items.get(row.get('ID', ''))
    if not item:
        return []
    gl_quote = item.get('gl_quote_roundtripped') or item.get('gl_quote', '')

    findings = []
    for at in ats:
        at_stripped = at.lstrip()
        if not at_stripped:
            continue
        first_char = at_stripped[0]
        if first_char in '.,;:!?':
            # Only flag if the gl_quote doesn't also start with that punctuation
            gl_stripped = gl_quote.lstrip() if gl_quote else ''
            if not gl_stripped or gl_stripped[0] != first_char:
                findings.append({
                    'severity': 'warning', 'category': 'at_starting_punctuation',
                    'message': f'AT [{at}] starts with "{first_char}" — '
                               f'remove unless proposing a punctuation change'
                })
    return findings


def check_missing_at(row, prepared_items):
    """Check 22: Notes must have an alternate translation when the template requires one."""
    note = row.get('Note', '')
    item = prepared_items.get(row.get('ID', ''))
    if not item:
        return None
    needs_at = item.get('needs_at', False)
    tcm_mode = item.get('tcm_mode', False)
    note_type = item.get('note_type', '')

    # If the template has an AT section, the note must include one
    if not needs_at and not tcm_mode:
        return None

    # Check for "Alternate translation:" anywhere in the note
    if 'Alternate translation:' in note or 'Alternate translation:' in note:
        return None

    # TCM notes use inline "Alternate translation:" per option
    if tcm_mode:
        return {'severity': 'error', 'category': 'missing_at',
                'message': 'TCM note is missing Alternate translation(s)'}

    return {'severity': 'error', 'category': 'missing_at',
            'message': 'Note is missing Alternate translation (template requires one)'}


def check_hebrew_quote_joiners(row, hebrew_verses):
    """Check 19: Hebrew quotes spanning non-adjacent words should use & separators."""
    if row.get('Occurrence') == '0':
        return []
    quote = row.get('Quote', '')
    if not quote or not has_rtl(quote):
        return []
    # Skip quotes that already have & separators
    if ' & ' in quote:
        return []

    findings = []
    # Heuristic: extract Hebrew word tokens from the quote
    heb_words = [w for w in quote.split() if has_rtl(w)]
    if len(heb_words) < 2:
        return []

    # Check against the Hebrew verse if available
    ref = row.get('Reference', '')
    verse_words = hebrew_verses.get(ref, [])
    if not verse_words:
        return findings

    # Find positions of each quote word in the verse
    positions = []
    for qw in heb_words:
        # Strip cantillation marks for comparison
        qw_clean = qw.strip()
        for i, vw in enumerate(verse_words):
            if vw.strip() == qw_clean:
                if i not in positions:
                    positions.append(i)
                    break

    if len(positions) >= 2:
        # Check for gaps (non-consecutive positions)
        positions_sorted = sorted(positions)
        for i in range(1, len(positions_sorted)):
            gap = positions_sorted[i] - positions_sorted[i - 1]
            if gap > 1:
                findings.append({
                    'severity': 'warning', 'category': 'hebrew_quote_missing_joiner',
                    'message': f'Hebrew quote may need & separator — {gap - 1} word(s) '
                               f'skipped between positions {positions_sorted[i-1]} and '
                               f'{positions_sorted[i]} in source verse'
                })
                break  # One warning per quote is enough
    return findings


def check_multiverse_notes(rows):
    """Check 20: Flag potential multi-verse note issues for review.

    Detects three patterns:
    (a) Notes that explicitly reference multiple verses (e.g., "verses 2, 5, and 6").
    (b) Notes with cross-verse back-references (e.g., "as in verse 3").
    (c) Near-duplicate notes: same issue type in adjacent verses with high text
        similarity, suggesting a summary was split rather than independent notes written.

    All findings are warnings (not errors) because adjacent-verse thoughts can
    be legitimate.
    """
    findings = []

    # --- Pattern (a): explicit multi-verse language ---
    # "verses 2, 5, and 6", "verses 3-5", "in verses 2 and 3"
    multi_verse_re = re.compile(
        r'\bverses\s+\d+(?:\s*[-,]\s*\d+)*(?:\s*(?:,\s*)?and\s+\d+)',
        re.IGNORECASE
    )
    # Also catch "in verses X-Y" range form
    verse_range_re = re.compile(r'\bverses\s+\d+\s*[-\u2013]\s*\d+', re.IGNORECASE)

    for row in rows:
        if row.get('Occurrence') == '0':
            continue
        note = row.get('Note', '')
        m = multi_verse_re.search(note) or verse_range_re.search(note)
        if m:
            findings.append({
                'row': row['_line'],
                'reference': row.get('Reference', ''),
                'id': row.get('ID', ''),
                'severity': 'warning',
                'category': 'multiverse_language',
                'message': f'Note references multiple verses: "{m.group(0)}" '
                           f'— each verse should get its own independent note'
            })

    # --- Pattern (b): cross-verse back-references ---
    # "as in verse 3", "see verse 5", "refers to ... verse 3"
    back_ref_re = re.compile(
        r'\b(?:as in|see|from|refers? to[^.]{0,30})\s+verse\s+\d+',
        re.IGNORECASE
    )

    for row in rows:
        if row.get('Occurrence') == '0':
            continue
        note = row.get('Note', '')
        m = back_ref_re.search(note)
        if m:
            findings.append({
                'row': row['_line'],
                'reference': row.get('Reference', ''),
                'id': row.get('ID', ''),
                'severity': 'warning',
                'category': 'multiverse_backref',
                'message': f'Note back-references another verse: "{m.group(0)}" '
                           f'— verify the note is self-contained'
            })

    # --- Pattern (c): near-duplicate notes in adjacent verses ---
    # Group rows by issue type slug
    def get_slug(row):
        sref = row.get('SupportReference', '')
        m = re.search(r'translate/([^\s;,]+)', sref)
        return m.group(1) if m else ''

    def get_verse_num(row):
        ref = row.get('Reference', '')
        m = re.match(r'(\d+):(\d+)', ref)
        return int(m.group(2)) if m else -1

    def note_words(row):
        """Extract content words from a note for similarity comparison."""
        note = row.get('Note', '')
        # Remove bold markers, AT brackets, punctuation
        clean = re.sub(r'\*\*[^*]+\*\*', '', note)
        clean = re.sub(r'\[[^\]]+\]', '', clean)
        clean = re.sub(r'[^\w\s]', '', clean.lower())
        words = set(clean.split())
        # Remove very common words to focus on content
        stop = {'the', 'a', 'an', 'is', 'are', 'was', 'were', 'in', 'of', 'to',
                'and', 'or', 'for', 'that', 'this', 'with', 'you', 'could',
                'if', 'it', 'he', 'his', 'her', 'by', 'as', 'be', 'not',
                'alternate', 'translation', 'here', 'means', 'way', 'idea',
                'same', 'express', 'another'}
        return words - stop

    # Only check real note rows
    note_rows = [r for r in rows if r.get('Occurrence') != '0']

    for i in range(len(note_rows)):
        for j in range(i + 1, len(note_rows)):
            row_a = note_rows[i]
            row_b = note_rows[j]
            slug_a = get_slug(row_a)
            slug_b = get_slug(row_b)
            if not slug_a or slug_a != slug_b:
                continue
            v_a = get_verse_num(row_a)
            v_b = get_verse_num(row_b)
            if v_a < 0 or v_b < 0:
                continue
            # Only check adjacent or near-adjacent verses (within 2)
            if abs(v_a - v_b) > 2:
                continue
            words_a = note_words(row_a)
            words_b = note_words(row_b)
            if not words_a or not words_b:
                continue
            overlap = len(words_a & words_b) / min(len(words_a), len(words_b))
            if overlap >= 0.75:
                findings.append({
                    'row': row_b['_line'],
                    'reference': f"{row_a.get('Reference', '')} / {row_b.get('Reference', '')}",
                    'id': f"{row_a.get('ID', '')} / {row_b.get('ID', '')}",
                    'severity': 'warning',
                    'category': 'multiverse_duplicate',
                    'message': f'Near-duplicate {slug_a} notes in adjacent verses '
                               f'({overlap:.0%} content overlap) — verify each note '
                               f'is independently written, not a multi-verse summary'
                })

    return findings


def check_parallelism_quote_scope(row, prepared_items):
    """Check 16: Parallelism notes should quote both full parallel phrases."""
    sref = row.get('SupportReference', '')
    if 'figs-parallelism' not in sref:
        return []

    item = prepared_items.get(row.get('ID', ''))
    if not item:
        return []
    gl_quote = item.get('gl_quote_roundtripped') or item.get('gl_quote', '')
    ult_verse = item.get('ult_verse', '')
    if not gl_quote or not ult_verse:
        return []

    # Heuristic: if the gl_quote is very short relative to the verse, it likely
    # captures only key words rather than full parallel phrases
    quote_words = len(gl_quote.split())
    verse_words = len(ult_verse.split())
    if verse_words > 0 and quote_words < 4 and verse_words > 8:
        return [{
            'severity': 'warning', 'category': 'narrow_parallelism_quote',
            'message': f'Parallelism gl_quote is only {quote_words} words in a '
                       f'{verse_words}-word verse — verify both full parallel phrases are quoted'
        }]
    return []


def check_curly_quotes(row):
    """Check 12: No straight quotes should remain."""
    if row.get('Occurrence') == '0':
        return None
    note = row.get('Note', '')
    # Skip checking inside markdown bold markers
    clean = re.sub(r'\*\*[^*]+\*\*', '', note)
    # Check for straight double quotes (but not within markdown or code)
    if '"' in clean:
        return {'severity': 'warning', 'category': 'straight_quotes',
                'message': 'Note contains straight double quotes (should be curly)'}
    return None


def check_at_capitalization(row, prepared_items):
    """Check 13: AT capitalization should match sentence position."""
    note = row.get('Note', '')
    ats = extract_ats(note)
    if not ats:
        return []

    item = prepared_items.get(row.get('ID', ''))
    if not item:
        return []
    gl_quote = item.get('gl_quote_roundtripped') or item.get('gl_quote', '')
    ult_verse = item.get('ult_verse', '')
    if not gl_quote or not ult_verse:
        return []

    clean_ult = strip_braces(ult_verse)
    clean_quote = strip_braces(gl_quote)
    idx, found = find_gl_quote_in_ult(ult_verse, gl_quote)
    if not found:
        return []

    # Distinguish sentence start (after period) from verse start (idx == 0)
    after_period = idx > 0 and clean_ult[:idx].rstrip().endswith('.')
    verse_start = idx == 0
    mid_sentence = not after_period and not verse_start

    findings = []
    for at in ats:
        if not at:
            continue
        first_char = at[0]
        if after_period and first_char.islower():
            findings.append({
                'severity': 'warning', 'category': 'at_capitalization',
                'message': f'AT [{at}] starts lowercase but gl_quote follows a period (sentence start)'
            })
        elif verse_start and first_char.islower():
            findings.append({
                'severity': 'warning', 'category': 'at_capitalization',
                'message': f'AT [{at}] starts lowercase at verse start — verify whether this verse begins a new sentence (if so, capitalize the AT)'
            })
        elif mid_sentence and first_char.isupper():
            # Check if the uppercase might be a proper noun (allow it)
            at_words = at.split()
            if len(at_words) > 0:
                first_word = at_words[0]
                # Don't flag proper nouns (simple heuristic: known proper nouns)
                if first_word not in ('Yahweh', 'God', 'Lord', 'David', 'Israel',
                                      'Jerusalem', 'Zion', 'Moses', 'Jacob',
                                      'Abraham', 'Christ', 'Jesus', 'I'):
                    findings.append({
                        'severity': 'warning', 'category': 'at_capitalization',
                        'message': f'AT [{at}] starts uppercase but gl_quote is mid-sentence'
                    })
    return findings


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description='Check AI-generated translation notes for quality issues',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    parser.add_argument('tsv_path', help='Path to assembled TN TSV')
    parser.add_argument('--prepared-json', help='Path to prepared_notes.json')
    parser.add_argument('--ult-usfm', help='Path to plain ULT USFM')
    parser.add_argument('--ust-usfm', help='Path to plain UST USFM')
    parser.add_argument('--book', help='Book code (e.g. PSA) for master TN ID check')
    parser.add_argument('--hebrew-usfm', help='Path to Hebrew source USFM (for quote validation)')
    parser.add_argument('--output', '-o', default='/tmp/claude/tn_quality_findings.json',
                        help='Output findings JSON path')

    args = parser.parse_args()

    # Parse inputs
    print(f"Reading TSV: {args.tsv_path}", file=sys.stderr)
    rows = parse_tsv(args.tsv_path)
    print(f"  {len(rows)} rows", file=sys.stderr)

    # Load prepared notes for context
    prepared_items = {}
    if args.prepared_json and os.path.exists(args.prepared_json):
        print(f"Reading prepared JSON: {args.prepared_json}", file=sys.stderr)
        with open(args.prepared_json) as f:
            prepared = json.load(f)
        for item in prepared.get('items', []):
            prepared_items[item['id']] = item

    # Parse ULT/UST
    ult_verses = parse_usfm_verses(args.ult_usfm) if args.ult_usfm else {}
    ust_verses = parse_usfm_verses(args.ust_usfm) if args.ust_usfm else {}

    # Detect book code
    book_code = args.book
    if not book_code and args.prepared_json and os.path.exists(args.prepared_json):
        with open(args.prepared_json) as f:
            pdata = json.load(f)
        book_code = pdata.get('book', '')

    # Parse Hebrew source for quote validation
    hebrew_path = args.hebrew_usfm
    if not hebrew_path and book_code:
        hebrew_path = find_hebrew_usfm(book_code)
    hebrew_verses = parse_hebrew_source_words(hebrew_path) if hebrew_path else {}
    if hebrew_verses:
        print(f"  Loaded Hebrew source: {len(hebrew_verses)} verses", file=sys.stderr)
    else:
        print("  No Hebrew source available; skipping quote joiner check", file=sys.stderr)

    # Load valid issues once
    valid_issues = load_valid_issues()
    if valid_issues is None:
        print("Warning: translation-issues.csv not found; skipping support reference check",
              file=sys.stderr)

    all_findings = []

    # --- Per-row checks ---
    for row in rows:
        row_findings = []

        # Check 1: ID format
        f = check_id_format(row)
        if f:
            row_findings.append(f)

        # Check 4: Hebrew quote
        f = check_hebrew_quote(row)
        if f:
            row_findings.append(f)

        # Check 5: AT bracket syntax
        f = check_at_bracket_syntax(row)
        if f:
            row_findings.append(f)

        # Check 6: AT does not match UST
        for f in check_at_not_ust(row, ust_verses, prepared_items):
            row_findings.append(f)

        # Check 7: gl_quote in ULT
        f = check_gl_quote_in_ult(row, prepared_items)
        if f:
            row_findings.append(f)

        # Check 8: Bold accuracy
        for f in check_bold_accuracy(row, prepared_items, ult_verses):
            row_findings.append(f)

        # Check 9: No rc:// in note
        f = check_no_rc_in_note(row)
        if f:
            row_findings.append(f)

        # Check 10: Orphaned words
        for f in check_orphaned_words(row, prepared_items):
            row_findings.append(f)

        # Check 10b: Dropped leading conjunction
        for f in check_dropped_leading_conjunction(row, prepared_items):
            row_findings.append(f)

        # Check 11: "The writer" in Psalms
        if book_code:
            f = check_writer_in_psalms(row, book_code)
            if f:
                row_findings.append(f)

        # Check 12: Curly quotes
        f = check_curly_quotes(row)
        if f:
            row_findings.append(f)

        # Check 13: AT capitalization
        for f in check_at_capitalization(row, prepared_items):
            row_findings.append(f)

        # Check 14: Abstract noun ATs must not contain abstract nouns
        for f in check_abstract_noun_at(row, prepared_items):
            row_findings.append(f)

        # Check 15: AT ending punctuation
        for f in check_at_ending_punctuation(row, prepared_items):
            row_findings.append(f)

        # Check 16: Parallelism quote scope
        for f in check_parallelism_quote_scope(row, prepared_items):
            row_findings.append(f)

        # Check 17: SupportReference slug must be in translation-issues.csv
        f = check_support_reference(row, valid_issues)
        if f:
            row_findings.append(f)

        # Check 18: AT starting punctuation
        for f in check_at_starting_punctuation(row, prepared_items):
            row_findings.append(f)

        # Check 19: Hebrew quote missing & joiners
        for f in check_hebrew_quote_joiners(row, hebrew_verses):
            row_findings.append(f)

        # Check 21: rquestion AT must end with . or !
        for f in check_rquestion_at_punctuation(row, prepared_items):
            row_findings.append(f)

        # Check 22: Missing alternate translation
        f = check_missing_at(row, prepared_items)
        if f:
            row_findings.append(f)

        # Annotate each finding with row context
        for f in row_findings:
            f['row'] = row['_line']
            f['reference'] = row.get('Reference', '')
            f['id'] = row.get('ID', '')
            all_findings.append(f)

    # --- File-level checks ---

    # Check 2: ID uniqueness
    all_findings.extend(check_id_uniqueness(rows))

    # Check 20: Multi-verse note detection
    all_findings.extend(check_multiverse_notes(rows))

    # Check 3: ID collisions with master TN
    if book_code:
        print(f"Checking ID collisions against master TN for {book_code}...",
              file=sys.stderr)
        all_findings.extend(check_id_collisions(rows, book_code))

    # --- Summary ---
    errors = [f for f in all_findings if f['severity'] == 'error']
    warnings = [f for f in all_findings if f['severity'] == 'warning']
    note_rows = [r for r in rows if r.get('Occurrence') != '0']

    output = {
        'summary': {
            'total_notes': len(note_rows),
            'errors': len(errors),
            'warnings': len(warnings),
            'clean': len(note_rows) - len(set(f['id'] for f in all_findings if f.get('id'))),
        },
        'findings': all_findings
    }

    # Write output
    os.makedirs(os.path.dirname(os.path.abspath(args.output)) or '.', exist_ok=True)
    with open(args.output, 'w', encoding='utf-8') as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    # Print summary to stderr
    print(f"\n--- Quality Check Results ---", file=sys.stderr)
    print(f"  Notes checked: {len(note_rows)}", file=sys.stderr)
    print(f"  Errors:   {len(errors)}", file=sys.stderr)
    print(f"  Warnings: {len(warnings)}", file=sys.stderr)
    print(f"  Clean:    {output['summary']['clean']}", file=sys.stderr)

    if errors:
        print(f"\nErrors:", file=sys.stderr)
        for f in errors:
            print(f"  {f['reference']} ({f['id']}) [{f['category']}]: {f['message']}",
                  file=sys.stderr)

    if warnings:
        print(f"\nWarnings:", file=sys.stderr)
        for f in warnings:
            print(f"  {f['reference']} ({f['id']}) [{f['category']}]: {f['message']}",
                  file=sys.stderr)

    print(f"\nFindings written to {args.output}", file=sys.stderr)
    return 1 if errors else 0


if __name__ == '__main__':
    sys.exit(main())
