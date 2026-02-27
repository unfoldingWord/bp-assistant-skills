#!/usr/bin/env python3
"""
fetch_door43.py - Fetch USFM files from Door43 git repositories

Usage:
  python fetch_door43.py <book> [options]
  python fetch_door43.py PSA --user benjamin-test
  python fetch_door43.py 1JN --output ./data/1jn.usfm

Options:
  --user <username>     Fetch from user's fork instead of unfoldingWord
  --repo <repo>         Repository name (default: en_ult)
  --branch <branch>     Branch name (default: master)
  --output <path>       Output file path (default: stdout)
  --type <ult|ust>      Shortcut for repo (en_ult or en_ust)

Book names:
  Use standard abbreviations: GEN, EXO, PSA, MAT, 1JN, REV, etc.
  Both uppercase and lowercase work.

URL Pattern:
  https://git.door43.org/{org}/{repo}/raw/branch/{branch}/{filename}

Examples:
  python fetch_door43.py PSA                          # Psalms from unfoldingWord/en_ult master
  python fetch_door43.py 1JN --user benjamin-test    # 1 John from user's fork
  python fetch_door43.py MAT --type ust               # Matthew from en_ust
  python fetch_door43.py GEN --output gen.usfm        # Save to file
"""

import argparse
import sys
import urllib.request
import urllib.error

# Book number mapping (Door43 USFM filename convention)
# OT: 01-39, NT: 41-67 (40 skipped for intertestamental gap)
# These abbreviations match the actual filenames on git.door43.org
BOOK_NUMBERS = {
    # Old Testament
    'GEN': '01', 'EXO': '02', 'LEV': '03', 'NUM': '04', 'DEU': '05',
    'JOS': '06', 'JDG': '07', 'RUT': '08', '1SA': '09', '2SA': '10',
    '1KI': '11', '2KI': '12', '1CH': '13', '2CH': '14', 'EZR': '15',
    'NEH': '16', 'EST': '17', 'JOB': '18', 'PSA': '19', 'PRO': '20',
    'ECC': '21', 'SNG': '22', 'ISA': '23', 'JER': '24', 'LAM': '25',
    'EZK': '26', 'DAN': '27', 'HOS': '28', 'JOL': '29', 'AMO': '30',
    'OBA': '31', 'JON': '32', 'MIC': '33', 'NAM': '34', 'HAB': '35',
    'ZEP': '36', 'HAG': '37', 'ZEC': '38', 'MAL': '39',
    # New Testament
    'MAT': '41', 'MRK': '42', 'LUK': '43', 'JHN': '44', 'ACT': '45',
    'ROM': '46', '1CO': '47', '2CO': '48', 'GAL': '49', 'EPH': '50',
    'PHP': '51', 'COL': '52', '1TH': '53', '2TH': '54', '1TI': '55',
    '2TI': '56', 'TIT': '57', 'PHM': '58', 'HEB': '59', 'JAS': '60',
    '1PE': '61', '2PE': '62', '1JN': '63', '2JN': '64', '3JN': '65',
    'JUD': '66', 'REV': '67'
}

# Alternative book names (aliases map to Door43 canonical abbreviations)
BOOK_ALIASES = {
    'PS': 'PSA', 'PSALM': 'PSA', 'PSALMS': 'PSA',
    'SONG': 'SNG', 'SONGS': 'SNG', 'SOS': 'SNG',
    'EZE': 'EZK', 'EZEK': 'EZK', 'EZEKIEL': 'EZK',
    'JOEL': 'JOL',
    'OBAD': 'OBA', 'OBADIAH': 'OBA',
    'JONAH': 'JON',
    'MICAH': 'MIC',
    'NAH': 'NAM', 'NAHUM': 'NAM',
    'HABAKKUK': 'HAB', 'HABAK': 'HAB',
    'ZEPHANIAH': 'ZEP', 'ZEPH': 'ZEP',
    'HAGGAI': 'HAG',
    'ZECHARIAH': 'ZEC', 'ZECH': 'ZEC',
    'MALACHI': 'MAL',
    'MARK': 'MRK',
    'JOHN': 'JHN',
    'ACTS': 'ACT',
    'PHIL': 'PHP', 'PHILIPPIANS': 'PHP',
    'PHILEM': 'PHM', 'PHILEMON': 'PHM',
    'JAM': 'JAS', 'JAMES': 'JAS',
    'JUDE': 'JUD',
}


def normalize_book(book: str) -> str:
    """Normalize book name to standard abbreviation."""
    upper = book.upper()
    if upper in BOOK_NUMBERS:
        return upper
    if upper in BOOK_ALIASES:
        return BOOK_ALIASES[upper]
    raise ValueError(f"Unknown book: {book}")


def get_filename(book: str) -> str:
    """Get USFM filename for a book."""
    normalized = normalize_book(book)
    number = BOOK_NUMBERS[normalized]
    return f"{number}-{normalized}.usfm"


def build_url(org: str, repo: str, branch: str, filename: str) -> str:
    """Build Door43 raw file URL."""
    return f"https://git.door43.org/{org}/{repo}/raw/branch/{branch}/{filename}"


def fetch_usfm(book: str, user: str = None, repo: str = 'en_ult',
               branch: str = 'master') -> str:
    """Fetch USFM content from Door43."""
    org = user if user else 'unfoldingWord'
    filename = get_filename(book)
    url = build_url(org, repo, branch, filename)

    try:
        with urllib.request.urlopen(url) as response:
            return response.read().decode('utf-8')
    except urllib.error.HTTPError as e:
        if e.code == 404:
            raise FileNotFoundError(f"File not found: {url}")
        raise


def main():
    parser = argparse.ArgumentParser(
        description='Fetch USFM files from Door43',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s PSA                          # Psalms from unfoldingWord/en_ult
  %(prog)s 1JN --user benjamin-test    # 1 John from user's fork
  %(prog)s MAT --type ust               # Matthew from en_ust
  %(prog)s GEN --output gen.usfm        # Save to file
"""
    )
    parser.add_argument('book', help='Book abbreviation (e.g., PSA, 1JN, MAT)')
    parser.add_argument('--user', '-u', help='Fetch from user fork instead of unfoldingWord')
    parser.add_argument('--repo', '-r', default='en_ult', help='Repository name (default: en_ult)')
    parser.add_argument('--branch', '-b', default='master', help='Branch name (default: master)')
    parser.add_argument('--output', '-o', help='Output file path (default: stdout)')
    parser.add_argument('--type', '-t', choices=['ult', 'ust'],
                        help='Shortcut for repo type')

    args = parser.parse_args()

    # Handle --type shortcut
    repo = args.repo
    if args.type:
        repo = f'en_{args.type}'

    try:
        content = fetch_usfm(args.book, user=args.user, repo=repo, branch=args.branch)

        if args.output:
            with open(args.output, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"Saved to {args.output}", file=sys.stderr)
        else:
            print(content)

    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
