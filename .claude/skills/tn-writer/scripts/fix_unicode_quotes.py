#!/usr/bin/env python3
"""
Fix Hebrew quote Unicode to exactly match UHB source byte order.

The TN pipeline can reorder combining marks (via NFKD normalization in
tsv-quote-converters or LLM tokenization). This script re-extracts each
Hebrew quote from the UHB source so the bytes match exactly.

Usage:
    python3 fix_unicode_quotes.py <tsv_file> <hebrew_usfm> [--in-place] [--output path]
    python3 fix_unicode_quotes.py --batch <notes_dir> [--hebrew-dir <dir>]
"""

import argparse
import os
import re
import sys
import unicodedata

# Marks to strip from source to build "reduced source"
STRIP_RE = re.compile(r'[\u0591-\u05AF\u2060\u05BD\u05C3]')
HEBREW_RE = re.compile(r'[\u0590-\u05FF]')
WORD_RE = re.compile(r'\\w\s+([^|]+)\|[^\\]*?\\w\*')

# Book number mapping for auto-detecting Hebrew USFM files
BOOK_NUMBERS = {
    'GEN': '01', 'EXO': '02', 'LEV': '03', 'NUM': '04', 'DEU': '05',
    'JOS': '06', 'JDG': '07', 'RUT': '08', '1SA': '09', '2SA': '10',
    '1KI': '11', '2KI': '12', '1CH': '13', '2CH': '14', 'EZR': '15',
    'NEH': '16', 'EST': '17', 'JOB': '18', 'PSA': '19', 'PRO': '20',
    'ECC': '21', 'SNG': '22', 'ISA': '23', 'JER': '24', 'LAM': '25',
    'EZK': '26', 'DAN': '27', 'HOS': '28', 'JOL': '29', 'AMO': '30',
    'OBA': '31', 'JON': '32', 'MIC': '33', 'NAM': '34', 'HAB': '35',
    'ZEP': '36', 'HAG': '37', 'ZEC': '38', 'MAL': '39',
}

def parse_hebrew_usfm(content):
    """Parse Hebrew USFM into verse map: { "ch:vs": "raw text" }.

    Handles multi-line verses where \\v is on its own line and \\w tokens
    follow on subsequent lines. Preserves inter-word connectors like maqqeph.
    """
    verse_map = {}
    ch = 0
    cur_verse = None
    cur_lines = []
    for line in content.split('\n'):
        trimmed = line.strip()
        cm = re.match(r'^\\c\s+(\d+)', trimmed)
        if cm:
            if cur_verse and cur_lines:
                verse_map[cur_verse] = _extract_verse_text('\n'.join(cur_lines))
            ch = int(cm.group(1))
            cur_verse = None
            cur_lines = []
            continue
        vm = re.match(r'^\\v\s+(\d+[-\d]*)', trimmed)
        if vm:
            if cur_verse and cur_lines:
                verse_map[cur_verse] = _extract_verse_text('\n'.join(cur_lines))
            vs = vm.group(1).split('-')[0]
            cur_verse = f'{ch}:{vs}'
            cur_lines = []
        if cur_verse and trimmed:
            cur_lines.append(trimmed)
    if cur_verse and cur_lines:
        verse_map[cur_verse] = _extract_verse_text('\n'.join(cur_lines))
    return verse_map

# Matches \w tokens and captures text between them (e.g., maqqeph)
_TOKEN_RE = re.compile(r'\\w\s+([^|]+)\|[^\\]*?\\w\*')

def _extract_verse_text(raw_lines):
    """Extract Hebrew text from verse lines, preserving maqqeph between words."""
    # Join all lines, then extract words and inter-word connectors
    text = raw_lines.replace('\n', ' ')
    parts = []
    last_end = 0
    for m in _TOKEN_RE.finditer(text):
        # Check for connector (like maqqeph) between previous token and this one
        between = text[last_end:m.start()]
        if parts and '\u05BE' in between:
            # Maqqeph connects words without space
            parts.append('\u05BE')
        elif parts:
            parts.append(' ')
        parts.append(m.group(1).strip())
        last_end = m.end()
    return ''.join(parts)

def build_stripped(raw):
    """Strip cantillation/word-joiners/meteg from source, keeping offset map back to raw."""
    stripped = []
    offset_map = []  # offset_map[i] = index in raw for stripped[i]
    for i, c in enumerate(raw):
        if not STRIP_RE.match(c):
            stripped.append(c)
            offset_map.append(i)
    return ''.join(stripped), offset_map

def raw_span(raw, offset_map, s_start, s_end, stripped_len):
    """Given a match in stripped text, return the corresponding full span from raw."""
    raw_start = offset_map[s_start]
    # End: start of NEXT stripped char, or end of raw string
    raw_end_excl = offset_map[s_end + 1] if (s_end + 1 < stripped_len) else len(raw)
    # Trim trailing spaces and sof pasuq
    end = raw_end_excl
    while end > raw_start and raw[end - 1] in (' ', '\u05C3'):
        end -= 1
    return raw[raw_start:end]

def fix_segment(seg, raw_verse):
    """Match a quote segment against UHB verse and return exact full-mark bytes."""
    stripped_verse, offset_map = build_stripped(raw_verse)
    # Strip the quote too (it may or may not already have marks stripped)
    stripped_quote = STRIP_RE.sub('', seg)

    norm_quote = unicodedata.normalize('NFKD', stripped_quote)
    norm_stripped = unicodedata.normalize('NFKD', stripped_verse)

    # Build map from normalized stripped index back to stripped index
    nr_map = []
    si = 0
    ni = 0
    while ni < len(norm_stripped) and si < len(stripped_verse):
        char_norm = unicodedata.normalize('NFKD', stripped_verse[si])
        for k in range(len(char_norm)):
            if ni + k < len(norm_stripped):
                nr_map.append(si)
        ni += len(char_norm)
        si += 1

    pos = norm_stripped.find(norm_quote)
    if pos == -1:
        return None

    # Map: norm pos -> stripped pos -> raw pos
    s_start = nr_map[pos] if pos < len(nr_map) else 0
    end_norm = pos + len(norm_quote) - 1
    s_end = nr_map[end_norm] if end_norm < len(nr_map) else len(stripped_verse) - 1

    # Extract the FULL raw span (with all marks) from the original verse
    return raw_span(raw_verse, offset_map, s_start, s_end, len(stripped_verse))

def fix_tsv(tsv_content, verse_map):
    """Fix Hebrew quotes in TSV content. Returns (fixed_content, stats)."""
    lines = tsv_content.split('\n')
    header = lines[0]
    cols0 = header.split('\t')

    try:
        quote_idx = cols0.index('Quote')
        ref_idx = cols0.index('Reference')
    except ValueError:
        return tsv_content, {'error': 'TSV missing Quote or Reference column'}

    fixed = 0
    skipped = 0
    not_found = 0
    warnings = []

    for i in range(1, len(lines)):
        if not lines[i].strip():
            continue
        cols = lines[i].split('\t')
        if len(cols) <= quote_idx:
            continue
        quote = cols[quote_idx]
        if not quote or not HEBREW_RE.search(quote):
            continue

        ref = cols[ref_idx]
        if ':' not in ref:
            continue

        raw_verse = verse_map.get(ref)
        if not raw_verse:
            skipped += 1
            continue

        segments = re.split(r'\s*&\s*', quote)
        fixed_segments = []
        all_matched = True

        for seg in segments:
            result = fix_segment(seg, raw_verse)
            if result is None:
                all_matched = False
                warnings.append(f'{ref}: segment not found: "{seg[:30]}..."')
                fixed_segments.append(seg)
            else:
                fixed_segments.append(result)

        fixed_quote = ' & '.join(fixed_segments)
        if fixed_quote != quote:
            cols[quote_idx] = fixed_quote
            lines[i] = '\t'.join(cols)
            fixed += 1
        if not all_matched:
            not_found += 1

    return '\n'.join(lines), {
        'fixed': fixed, 'skipped': skipped, 'not_found': not_found,
        'warnings': warnings
    }

def find_hebrew_usfm(book_code, hebrew_dir):
    """Find the Hebrew USFM file for a book code."""
    num = BOOK_NUMBERS.get(book_code.upper(), '')
    if num:
        candidate = os.path.join(hebrew_dir, f'{num}-{book_code.upper()}.usfm')
        if os.path.exists(candidate):
            return candidate
    # Fallback: search by book code
    for f in os.listdir(hebrew_dir):
        if book_code.upper() in f.upper() and f.endswith('.usfm'):
            return os.path.join(hebrew_dir, f)
    return None

def main():
    parser = argparse.ArgumentParser(description='Fix Hebrew quote Unicode in TN TSVs')
    parser.add_argument('tsv_file', nargs='?', help='TN TSV file path')
    parser.add_argument('hebrew_usfm', nargs='?', help='Hebrew source USFM path')
    parser.add_argument('--in-place', action='store_true', help='Overwrite input file')
    parser.add_argument('--output', help='Output file path')
    parser.add_argument('--batch', help='Process all TSVs in directory')
    parser.add_argument('--hebrew-dir', default=None,
                        help='Hebrew USFM directory (default: data/hebrew_bible/)')
    args = parser.parse_args()

    # Determine workspace root
    script_dir = os.path.dirname(os.path.abspath(__file__))
    workspace = os.environ.get('CSKILLBP_DIR',
        os.path.abspath(os.path.join(script_dir, '..', '..', '..', '..')))
    hebrew_dir = args.hebrew_dir or os.path.join(workspace, 'data', 'hebrew_bible')

    if args.batch:
        notes_dir = args.batch
        total_fixed = 0
        for root, dirs, files in os.walk(notes_dir):
            for f in sorted(files):
                if not f.endswith('.tsv'):
                    continue
                m = re.match(r'([A-Z0-9]{3})', f, re.I)
                if not m:
                    continue
                book = m.group(1).upper()
                heb_path = find_hebrew_usfm(book, hebrew_dir)
                if not heb_path:
                    print(f'  SKIP {f}: no Hebrew USFM for {book}', file=sys.stderr)
                    continue
                tsv_path = os.path.join(root, f)
                tsv_content = open(tsv_path, 'r', encoding='utf-8').read()
                heb_content = open(heb_path, 'r', encoding='utf-8').read()
                verse_map = parse_hebrew_usfm(heb_content)
                fixed_content, stats = fix_tsv(tsv_content, verse_map)
                if stats.get('fixed', 0) > 0:
                    open(tsv_path, 'w', encoding='utf-8').write(fixed_content)
                    total_fixed += stats['fixed']
                    print(f'  {f}: fixed {stats["fixed"]} quotes', file=sys.stderr)
        print(f'Total: fixed {total_fixed} quotes across all files', file=sys.stderr)
        return

    if not args.tsv_file:
        parser.error('tsv_file is required (or use --batch)')

    tsv_content = open(args.tsv_file, 'r', encoding='utf-8').read()

    if args.hebrew_usfm:
        heb_path = args.hebrew_usfm
    else:
        m = re.match(r'([A-Z0-9]{3})', os.path.basename(args.tsv_file), re.I)
        book = m.group(1).upper() if m else ''
        heb_path = find_hebrew_usfm(book, hebrew_dir)
        if not heb_path:
            print(f'ERROR: No Hebrew USFM found for {book}', file=sys.stderr)
            sys.exit(1)

    heb_content = open(heb_path, 'r', encoding='utf-8').read()
    verse_map = parse_hebrew_usfm(heb_content)
    fixed_content, stats = fix_tsv(tsv_content, verse_map)

    if args.in_place:
        open(args.tsv_file, 'w', encoding='utf-8').write(fixed_content)
        out_path = args.tsv_file
    elif args.output:
        os.makedirs(os.path.dirname(args.output), exist_ok=True)
        open(args.output, 'w', encoding='utf-8').write(fixed_content)
        out_path = args.output
    else:
        print(fixed_content)
        out_path = '<stdout>'

    print(f'Fixed {stats["fixed"]} Hebrew quotes', file=sys.stderr)
    if stats['skipped']:
        print(f'Skipped {stats["skipped"]} (verse not in Hebrew source)', file=sys.stderr)
    if stats['not_found']:
        print(f'{stats["not_found"]} quotes had unmatched segments', file=sys.stderr)
    for w in stats.get('warnings', [])[:10]:
        print(f'  WARNING: {w}', file=sys.stderr)

if __name__ == '__main__':
    main()
