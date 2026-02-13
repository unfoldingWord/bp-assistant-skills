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


def check_writer_in_psalms(row, book_code):
    """Check 11: 'The writer' should not appear in Psalms notes."""
    if book_code.upper() != 'PSA':
        return None
    if row.get('Occurrence') == '0':
        return None
    note = row.get('Note', '')
    if re.search(r'\bthe writer\b', note, re.IGNORECASE):
        return {'severity': 'warning', 'category': 'writer_in_psalms',
                'message': 'Uses "the writer" instead of "the psalmist" or attributed author'}
    return None


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

    # Is the gl_quote at the start of the verse?
    at_start = idx == 0 or clean_ult[:idx].rstrip().endswith('.')

    findings = []
    for at in ats:
        if not at:
            continue
        first_char = at[0]
        if at_start and first_char.islower():
            findings.append({
                'severity': 'warning', 'category': 'at_capitalization',
                'message': f'AT [{at}] starts lowercase but gl_quote is at verse/sentence start'
            })
        elif not at_start and first_char.isupper():
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

        # Annotate each finding with row context
        for f in row_findings:
            f['row'] = row['_line']
            f['reference'] = row.get('Reference', '')
            f['id'] = row.get('ID', '')
            all_findings.append(f)

    # --- File-level checks ---

    # Check 2: ID uniqueness
    all_findings.extend(check_id_uniqueness(rows))

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
