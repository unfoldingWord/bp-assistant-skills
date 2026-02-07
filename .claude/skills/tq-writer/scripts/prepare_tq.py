#!/usr/bin/env python3
"""
Prepare translation question data for AI consumption.

Extracts TQ rows, ULT verses, and UST verses for a book/chapter and packages
them into a single JSON file. Deterministic work only -- no AI.

Usage:
    python3 prepare_tq.py PSA --chapter 150
    python3 prepare_tq.py PSA --whole-book
    python3 prepare_tq.py PSA --chapter 150 --tq-repo /path/to/en_tq
"""

import argparse
import json
import os
import re
import subprocess
import sys

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
SKILL_DIR = os.path.dirname(SCRIPT_DIR)
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(SKILL_DIR)))

DEFAULT_TQ_REPO = '/mnt/c/Users/benja/Documents/GitHub/en_tq'

# ULT/UST search paths (in priority order)
ULT_SEARCH_DIRS = [
    os.path.join(PROJECT_ROOT, 'output', 'AI-ULT'),
    '/mnt/c/Users/benja/Documents/GitHub/en_ult',
]
UST_SEARCH_DIRS = [
    os.path.join(PROJECT_ROOT, 'output', 'AI-UST'),
    '/mnt/c/Users/benja/Documents/GitHub/en_ust',
]

FETCH_SCRIPT = os.path.join(
    PROJECT_ROOT, '.claude', 'skills', 'utilities', 'scripts', 'fetch_door43.py'
)
PARSE_USFM_SCRIPT = os.path.join(
    PROJECT_ROOT, '.claude', 'skills', 'utilities', 'scripts', 'usfm', 'parse_usfm.js'
)

# Book number mapping (from fetch_door43.py)
BOOK_NUMBERS = {
    'GEN': '01', 'EXO': '02', 'LEV': '03', 'NUM': '04', 'DEU': '05',
    'JOS': '06', 'JDG': '07', 'RUT': '08', '1SA': '09', '2SA': '10',
    '1KI': '11', '2KI': '12', '1CH': '13', '2CH': '14', 'EZR': '15',
    'NEH': '16', 'EST': '17', 'JOB': '18', 'PSA': '19', 'PRO': '20',
    'ECC': '21', 'SNG': '22', 'ISA': '23', 'JER': '24', 'LAM': '25',
    'EZK': '26', 'DAN': '27', 'HOS': '28', 'JOL': '29', 'AMO': '30',
    'OBA': '31', 'JON': '32', 'MIC': '33', 'NAM': '34', 'HAB': '35',
    'ZEP': '36', 'HAG': '37', 'ZEC': '38', 'MAL': '39',
    'MAT': '41', 'MRK': '42', 'LUK': '43', 'JHN': '44', 'ACT': '45',
    'ROM': '46', '1CO': '47', '2CO': '48', 'GAL': '49', 'EPH': '50',
    'PHP': '51', 'COL': '52', '1TH': '53', '2TH': '54', '1TI': '55',
    '2TI': '56', 'TIT': '57', 'PHM': '58', 'HEB': '59', 'JAS': '60',
    '1PE': '61', '2PE': '62', '1JN': '63', '2JN': '64', '3JN': '65',
    'JUD': '66', 'REV': '67',
}


# ---------------------------------------------------------------------------
# USFM parsing (adapted from prepare_notes.py)
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

    Returns dict: {"chapter:verse": "text", ...}
    """
    if not os.path.exists(usfm_path):
        return {}

    with open(usfm_path, 'r', encoding='utf-8') as f:
        content = f.read()

    current_chapter = None
    current_verse = None
    current_text_lines = []
    verse_map = {}

    def save_current_verse():
        nonlocal current_verse, current_text_lines
        if current_chapter and current_verse and current_text_lines:
            text = ' '.join(current_text_lines)
            text = clean_usfm_text(text)
            key = f"{current_chapter}:{current_verse}"
            verse_map[key] = text
        current_text_lines = []

    for line in content.split('\n'):
        chapter_match = re.match(r'\\c\s+(\d+)', line)
        if chapter_match:
            save_current_verse()
            current_chapter = chapter_match.group(1)
            current_verse = None
            continue

        verse_match = re.match(r'\\v\s+(\d+[-\d]*)\s*(.*)', line)
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
    return verse_map


# ---------------------------------------------------------------------------
# TQ TSV parsing
# ---------------------------------------------------------------------------

def parse_tq_tsv(filepath, chapters=None):
    """Parse a TQ book TSV file.

    Args:
        filepath: Path to tq_BOOK.tsv
        chapters: List of chapter strings to extract, or None for all

    Returns:
        (header_line, rows_by_chapter)
        header_line: The TSV header string
        rows_by_chapter: dict of {chapter: [row_strings]}
    """
    with open(filepath, 'r', encoding='utf-8') as f:
        lines = f.read().rstrip('\n').split('\n')

    if not lines:
        return '', {}

    header = lines[0]
    rows_by_chapter = {}

    for line in lines[1:]:
        if not line.strip():
            continue
        ref = line.split('\t', 1)[0]
        ch = ref.split(':')[0] if ':' in ref else ref
        if chapters and ch not in chapters:
            continue
        rows_by_chapter.setdefault(ch, []).append(line)

    return header, rows_by_chapter


# ---------------------------------------------------------------------------
# ULT/UST location
# ---------------------------------------------------------------------------

def find_usfm_file(book, search_dirs, file_type='ult'):
    """Find a USFM file for the given book in search directories.

    Checks output/ AI files first, then repo clones.
    Returns path or None.
    """
    book_upper = book.upper()
    book_num = BOOK_NUMBERS.get(book_upper, '')

    for search_dir in search_dirs:
        if not os.path.isdir(search_dir):
            continue

        # Check for AI output files (various naming patterns)
        for pattern in [
            f'{book_upper}.usfm',
            f'{book_upper}-aligned.usfm',
            f'{book_upper}_plain.usfm',
        ]:
            candidate = os.path.join(search_dir, pattern)
            if os.path.exists(candidate):
                return candidate

        # Check for repo-style filename (NN-BOOK.usfm)
        if book_num:
            candidate = os.path.join(search_dir, f'{book_num}-{book_upper}.usfm')
            if os.path.exists(candidate):
                return candidate

    return None


def fetch_from_door43(book, file_type='ult', output_path=None):
    """Fetch USFM from Door43 as fallback.

    Returns path to the fetched file, or None on failure.
    """
    if not os.path.exists(FETCH_SCRIPT):
        print(f"  WARNING: fetch_door43.py not found at {FETCH_SCRIPT}", file=sys.stderr)
        return None

    if output_path is None:
        output_path = f'/tmp/claude/tq_{book.lower()}_{file_type}.usfm'

    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    type_arg = 'ust' if file_type == 'ust' else 'ult'
    try:
        result = subprocess.run(
            [sys.executable, FETCH_SCRIPT, book, '--type', type_arg, '--output', output_path],
            capture_output=True, text=True, timeout=60
        )
        if result.returncode == 0 and os.path.exists(output_path):
            return output_path
        print(f"  WARNING: fetch failed: {result.stderr.strip()}", file=sys.stderr)
    except subprocess.TimeoutExpired:
        print(f"  WARNING: fetch timed out for {book} {file_type}", file=sys.stderr)

    return None


def get_plain_usfm(usfm_path):
    """Convert aligned USFM to plain text using parse_usfm.js if available.

    If the parser isn't available, falls back to Python-based cleaning.
    Returns path to plain USFM file.
    """
    if not os.path.exists(PARSE_USFM_SCRIPT):
        return usfm_path  # Fall back to Python parsing

    # Check if file looks like it needs stripping (has alignment markers)
    with open(usfm_path, 'r', encoding='utf-8') as f:
        sample = f.read(2000)

    if '\\zaln-s' not in sample and '\\+w' not in sample:
        return usfm_path  # Already plain

    # Write plain file to /tmp/claude/ to avoid writing into repo clones
    basename = os.path.basename(usfm_path).replace('.usfm', '_plain.usfm')
    plain_path = os.path.join('/tmp/claude', basename)

    try:
        result = subprocess.run(
            ['node', PARSE_USFM_SCRIPT, usfm_path, '--plain-only'],
            capture_output=True, text=True, timeout=30
        )
        if result.returncode == 0 and result.stdout.strip():
            os.makedirs(os.path.dirname(plain_path) or '.', exist_ok=True)
            with open(plain_path, 'w', encoding='utf-8') as f:
                f.write(result.stdout)
            return plain_path
    except (subprocess.TimeoutExpired, FileNotFoundError):
        pass

    return usfm_path  # Fall back


def locate_usfm(book, file_type='ult', explicit_path=None):
    """Locate USFM for the given book, with fallback chain.

    Priority: explicit path > output/ AI files > repo clone > fetch from Door43

    Returns (path, source_description) or (None, None).
    """
    if explicit_path and os.path.exists(explicit_path):
        plain = get_plain_usfm(explicit_path)
        return plain, f"explicit: {explicit_path}"

    search_dirs = ULT_SEARCH_DIRS if file_type == 'ult' else UST_SEARCH_DIRS
    found = find_usfm_file(book, search_dirs, file_type)
    if found:
        plain = get_plain_usfm(found)
        return plain, f"local: {found}"

    fetched = fetch_from_door43(book, file_type)
    if fetched:
        plain = get_plain_usfm(fetched)
        return plain, f"fetched: {fetched}"

    return None, None


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description='Prepare TQ data for AI consumption',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    parser.add_argument('book', help='Book code (e.g., PSA, GEN, MAT)')
    parser.add_argument('--chapter', '-c', help='Chapter number (e.g., 150)')
    parser.add_argument('--whole-book', action='store_true',
                        help='Process all chapters')
    parser.add_argument('--tq-repo', default=DEFAULT_TQ_REPO,
                        help=f'Path to en_tq repo clone (default: {DEFAULT_TQ_REPO})')
    parser.add_argument('--ult-path', help='Explicit path to ULT USFM')
    parser.add_argument('--ust-path', help='Explicit path to UST USFM')
    parser.add_argument('--output', '-o', default='/tmp/claude/prepared_tq.json',
                        help='Output JSON path (default: /tmp/claude/prepared_tq.json)')

    args = parser.parse_args()
    book = args.book.upper()

    if not args.chapter and not args.whole_book:
        print("ERROR: Specify --chapter N or --whole-book", file=sys.stderr)
        sys.exit(1)

    # Determine chapters to process
    chapters = None  # None means all
    if args.chapter:
        chapters = [args.chapter.lstrip('0') or '0']

    # 1. Find TQ source
    tq_file = os.path.join(args.tq_repo, f'tq_{book}.tsv')
    if not os.path.exists(tq_file):
        print(f"ERROR: TQ file not found: {tq_file}", file=sys.stderr)
        sys.exit(1)

    print(f"TQ source: {tq_file}", file=sys.stderr)
    header, tq_rows = parse_tq_tsv(tq_file, chapters)
    total_rows = sum(len(v) for v in tq_rows.values())
    print(f"  Found {total_rows} TQ rows across {len(tq_rows)} chapter(s)", file=sys.stderr)

    if total_rows == 0:
        print(f"WARNING: No TQ rows found for {book} chapters {chapters}", file=sys.stderr)

    # 2. Locate ULT
    print("Locating ULT...", file=sys.stderr)
    ult_path, ult_source = locate_usfm(book, 'ult', args.ult_path)
    if ult_path:
        print(f"  ULT: {ult_source}", file=sys.stderr)
        ult_verses = parse_usfm_verses(ult_path)
        print(f"  Parsed {len(ult_verses)} ULT verses", file=sys.stderr)
    else:
        print("  WARNING: No ULT found -- proceeding without", file=sys.stderr)
        ult_verses = {}

    # 3. Locate UST
    print("Locating UST...", file=sys.stderr)
    ust_path, ust_source = locate_usfm(book, 'ust', args.ust_path)
    if ust_path:
        print(f"  UST: {ust_source}", file=sys.stderr)
        ust_verses = parse_usfm_verses(ust_path)
        print(f"  Parsed {len(ust_verses)} UST verses", file=sys.stderr)
    else:
        print("  WARNING: No UST found -- proceeding without", file=sys.stderr)
        ust_verses = {}

    # 4. Filter verses to requested chapters
    ult_by_verse = {}
    ust_by_verse = {}
    if chapters:
        for key, val in ult_verses.items():
            ch = key.split(':')[0]
            if ch in chapters:
                ult_by_verse[key] = val
        for key, val in ust_verses.items():
            ch = key.split(':')[0]
            if ch in chapters:
                ust_by_verse[key] = val
    else:
        ult_by_verse = ult_verses
        ust_by_verse = ust_verses

    # 5. Build output
    output = {
        'book': book,
        'chapters': chapters if chapters else sorted(tq_rows.keys(), key=lambda c: int(c) if c.isdigit() else 0),
        'ult_source': ult_source or 'not found',
        'ust_source': ust_source or 'not found',
        'ult_by_verse': ult_by_verse,
        'ust_by_verse': ust_by_verse,
        'tq_header': header,
        'tq_rows_by_chapter': tq_rows,
    }

    os.makedirs(os.path.dirname(args.output) or '.', exist_ok=True)
    with open(args.output, 'w', encoding='utf-8') as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    print(f"\nWrote prepared TQ data to {args.output}", file=sys.stderr)
    print(f"  {total_rows} TQ rows, {len(ult_by_verse)} ULT verses, {len(ust_by_verse)} UST verses", file=sys.stderr)


if __name__ == '__main__':
    main()
