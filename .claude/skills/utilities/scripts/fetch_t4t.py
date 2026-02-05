#!/usr/bin/env python3
"""
fetch_t4t.py - Fetch T4T (Translation for Translators) USFM files from Door43

Fetches T4T source files from git.door43.org/unfoldingWord/en_t4t
and saves them to data/t4t/ with date headers for caching.

The T4T is the BASE SOURCE for UST creation. The UST workflow is to take
T4T and modify it minimally to meet unfoldingWord standards.

Usage:
    python fetch_t4t.py                    # Fetch all OT books
    python fetch_t4t.py --books GEN EXO    # Fetch specific books
    python fetch_t4t.py --force            # Force re-fetch all
    python fetch_t4t.py --list             # List available books
"""

import argparse
import os
import sys
import urllib.request
import urllib.error
from datetime import date

# Script location and project root
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(SCRIPT_DIR))))
OUTPUT_DIR = os.path.join(PROJECT_ROOT, "data", "t4t")

# All OT books
ALL_OT_BOOKS = [
    'GEN', 'EXO', 'LEV', 'NUM', 'DEU', 'JOS', 'JDG', 'RUT', '1SA', '2SA',
    '1KI', '2KI', '1CH', '2CH', 'EZR', 'NEH', 'EST', 'JOB', 'PSA', 'PRO',
    'ECC', 'SNG', 'ISA', 'JER', 'LAM', 'EZK', 'DAN', 'HOS', 'JOL', 'AMO',
    'OBA', 'JON', 'MIC', 'NAM', 'HAB', 'ZEP', 'HAG', 'ZEC', 'MAL'
]

# Book number mapping (Door43 USFM filename convention)
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

def get_cached_date(filepath):
    """Check if file exists and return the date from its first line."""
    if not os.path.exists(filepath):
        return None
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            first_line = f.readline().strip()
            if first_line.startswith("# Fetched: "):
                return first_line.replace("# Fetched: ", "")
    except:
        pass
    return None

def fetch_book(book, output_dir, force=False):
    """Fetch a single book's USFM from Door43 T4T repository."""
    book = book.upper()
    if book not in BOOK_NUMBERS:
        print(f"  Unknown book: {book}", file=sys.stderr)
        return False

    number = BOOK_NUMBERS[book]
    filename = f"{number}-{book}.usfm"
    output_path = os.path.join(output_dir, filename)
    today = date.today().isoformat()

    # Check cache
    if not force:
        cached_date = get_cached_date(output_path)
        if cached_date:
            print(f"  {book}: Using cached version from {cached_date}")
            return True

    # Fetch from Door43 (T4T repository)
    url = f"https://git.door43.org/unfoldingWord/en_t4t/raw/branch/master/{filename}"
    print(f"  {book}: Fetching from {url}")

    try:
        with urllib.request.urlopen(url) as response:
            content = response.read().decode('utf-8')

        # Add date header and save
        content_with_date = f"# Fetched: {today}\n{content}"
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(content_with_date)
        print(f"  {book}: Saved to {output_path}")
        return True

    except urllib.error.HTTPError as e:
        print(f"  {book}: HTTP Error {e.code}", file=sys.stderr)
        return False
    except Exception as e:
        print(f"  {book}: Error - {e}", file=sys.stderr)
        return False

def main():
    parser = argparse.ArgumentParser(
        description='Fetch T4T (Translation for Translators) USFM files from Door43',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
The T4T is the BASE SOURCE for UST creation. The UST workflow is to take
T4T and modify it minimally to meet unfoldingWord standards.

Examples:
  %(prog)s                    # Fetch all OT books
  %(prog)s --books PSA 1KI    # Fetch specific books
  %(prog)s --force            # Force re-fetch all books
  %(prog)s --list             # List available books
"""
    )
    parser.add_argument('--books', '-b', nargs='+',
                        help='Specific books to fetch (default: all OT)')
    parser.add_argument('--force', '-f', action='store_true',
                        help='Force re-fetch even if cached')
    parser.add_argument('--list', '-l', action='store_true',
                        help='List all OT books')
    parser.add_argument('--output-dir', '-o', default=OUTPUT_DIR,
                        help=f'Output directory (default: {OUTPUT_DIR})')

    args = parser.parse_args()

    if args.list:
        print("All OT Books (39 total):")
        print(", ".join(ALL_OT_BOOKS))
        return

    # Ensure output directory exists
    os.makedirs(args.output_dir, exist_ok=True)

    # Determine which books to fetch
    books = args.books if args.books else ALL_OT_BOOKS
    books = [b.upper() for b in books]

    print(f"Fetching {len(books)} T4T book(s) to {args.output_dir}")
    print()

    success_count = 0
    for book in books:
        if fetch_book(book, args.output_dir, force=args.force):
            success_count += 1

    print()
    print(f"Completed: {success_count}/{len(books)} books fetched successfully")

    if success_count != len(books):
        sys.exit(1)

if __name__ == '__main__':
    main()
