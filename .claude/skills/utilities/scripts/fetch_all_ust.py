#!/usr/bin/env python3
"""
fetch_all_ust.py - Batch fetch UST USFM files from Door43

Fetches published UST books from git.door43.org/unfoldingWord/en_ust
and saves them to data/published_ust/ with date headers for caching.

Usage:
    python fetch_all_ust.py                    # Fetch all v88 published books
    python fetch_all_ust.py --books GEN EXO    # Fetch specific books
    python fetch_all_ust.py --force            # Force re-fetch all
    python fetch_all_ust.py --list             # List available books

v88 Published OT Books (24 + Psalms):
    GEN, EXO, LEV, DEU, JOS, JDG, RUT, 1SA, 2SA, 1KI, 2KI,
    EZR, NEH, EST, JOB, PRO, SNG, JOL, OBA, JON, NAM, ZEP, HAG, MAL, PSA
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
OUTPUT_DIR = os.path.join(PROJECT_ROOT, "data", "published_ust")

# v88 published OT books (same as ULT)
V88_PUBLISHED_BOOKS = [
    'GEN', 'EXO', 'LEV', 'DEU', 'JOS', 'JDG', 'RUT', '1SA', '2SA',
    '1KI', '2KI', 'EZR', 'NEH', 'EST', 'JOB', 'PRO', 'SNG',
    'JOL', 'OBA', 'JON', 'NAM', 'ZEP', 'HAG', 'MAL', 'PSA'
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
    """Fetch a single book's USFM from Door43."""
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

    # Fetch from Door43 (UST repository)
    url = f"https://git.door43.org/unfoldingWord/en_ust/raw/branch/master/{filename}"
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
        description='Batch fetch UST USFM files from Door43',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s                    # Fetch all v88 published books
  %(prog)s --books GEN EXO    # Fetch specific books
  %(prog)s --force            # Force re-fetch all books
  %(prog)s --list             # List v88 published books
"""
    )
    parser.add_argument('--books', '-b', nargs='+',
                        help='Specific books to fetch (default: all v88 published)')
    parser.add_argument('--force', '-f', action='store_true',
                        help='Force re-fetch even if cached')
    parser.add_argument('--list', '-l', action='store_true',
                        help='List v88 published books')
    parser.add_argument('--output-dir', '-o', default=OUTPUT_DIR,
                        help=f'Output directory (default: {OUTPUT_DIR})')

    args = parser.parse_args()

    if args.list:
        print("v88 Published OT Books (25 total):")
        print(", ".join(V88_PUBLISHED_BOOKS))
        return

    # Ensure output directory exists
    os.makedirs(args.output_dir, exist_ok=True)

    # Determine which books to fetch
    books = args.books if args.books else V88_PUBLISHED_BOOKS
    books = [b.upper() for b in books]

    print(f"Fetching {len(books)} UST book(s) to {args.output_dir}")
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
