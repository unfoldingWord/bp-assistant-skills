#!/usr/bin/env python3
"""
fetch_glossary.py - Fetch ULST Glossary sheets from Google Sheets

Fetches glossary data for ULT/UST creation from the ULST Glossary spreadsheet.

Usage:
    python fetch_glossary.py --all                     # Fetch all 5 sheets
    python fetch_glossary.py --sheet hebrew_ot        # Fetch specific sheet
    python fetch_glossary.py --force                  # Force refresh all

Sheets available:
    hebrew_ot_glossary    - Core Hebrew terms (adam, berit, torah, hesed, etc.)
    biblical_measurements - Weight, volume, money, distance conversions
    psalms_reference      - Psalms-specific terms (Selah, musical terms)
    sacrifice_terminology - Hebrew sacrifice/offering terms (olah, hatta't)
    biblical_phrases      - Grammatical, prophetic phrases

Output: data/glossary/<sheet_name>.csv
"""

import argparse
import os
import sys
import requests
from datetime import date, timedelta

# Script location and project root
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(SCRIPT_DIR))))
OUTPUT_DIR = os.path.join(PROJECT_ROOT, "data", "glossary")

# ULST Glossary Google Sheet ID
SHEET_ID = "1pop2F61kRCRBgUvf8zHVwx9s-CBE8x3PyXojrTjJ3Lc"

# Sheet name to gid mapping
GLOSSARY_SHEETS = {
    'hebrew_ot_glossary': 1711192506,
    'biblical_measurements': 1835633752,
    'psalms_reference': 1739562476,
    'sacrifice_terminology': 243454428,
    'biblical_phrases': 1459152614,
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


def should_refresh_weekly(cached_date_str):
    """Return True if cache predates the most recent Thursday."""
    if not cached_date_str:
        return True
    try:
        cached = date.fromisoformat(cached_date_str)
    except ValueError:
        return True
    today = date.today()
    days_since_thursday = (today.weekday() - 3) % 7
    last_thursday = today - timedelta(days=days_since_thursday)
    return cached < last_thursday


def fetch_sheet(sheet_name, gid, output_dir, force=False):
    """Fetch a single sheet from the glossary spreadsheet."""
    output_path = os.path.join(output_dir, f"{sheet_name}.csv")
    today = date.today().isoformat()

    # Check cache -- refresh weekly on Thursdays even if daily cache exists
    if not force:
        cached_date = get_cached_date(output_path)
        if cached_date and not should_refresh_weekly(cached_date):
            print(f"  {sheet_name}: Using cached version from {cached_date}")
            return True

    # Build URL
    url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&gid={gid}"
    print(f"  {sheet_name}: Fetching from Google Sheets...")

    try:
        response = requests.get(url)
        if response.status_code != 200:
            print(f"  {sheet_name}: HTTP Error {response.status_code}", file=sys.stderr)
            return False

        # Decode as UTF-8 explicitly (Google Sheets exports UTF-8)
        # Using response.content instead of response.text to avoid encoding guessing
        text = response.content.decode('utf-8').lstrip('\ufeff')

        # Add date header and save
        text_with_date = f"# Fetched: {today}\n{text}"
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(text_with_date)

        print(f"  {sheet_name}: Saved to {output_path}")
        return True

    except Exception as e:
        print(f"  {sheet_name}: Error - {e}", file=sys.stderr)
        return False


def main():
    parser = argparse.ArgumentParser(
        description='Fetch ULST Glossary sheets from Google Sheets',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Available sheets:
  hebrew_ot_glossary    - Core Hebrew terms
  biblical_measurements - Weight, volume, money, distance
  psalms_reference      - Psalms-specific terms
  sacrifice_terminology - Hebrew sacrifice/offering terms
  biblical_phrases      - Grammatical, prophetic phrases

Examples:
  %(prog)s --all                     # Fetch all 5 sheets
  %(prog)s --sheet hebrew_ot_glossary  # Fetch specific sheet
  %(prog)s --force                   # Force refresh all
"""
    )
    parser.add_argument('--all', '-a', action='store_true',
                        help='Fetch all glossary sheets')
    parser.add_argument('--sheet', '-s', choices=list(GLOSSARY_SHEETS.keys()),
                        help='Fetch a specific sheet')
    parser.add_argument('--force', '-f', action='store_true',
                        help='Force refresh even if cached')
    parser.add_argument('--list', '-l', action='store_true',
                        help='List available sheets')
    parser.add_argument('--output-dir', '-o', default=OUTPUT_DIR,
                        help=f'Output directory (default: {OUTPUT_DIR})')

    args = parser.parse_args()

    if args.list:
        print("Available glossary sheets:")
        for name, gid in GLOSSARY_SHEETS.items():
            print(f"  {name} (gid={gid})")
        return

    if not args.all and not args.sheet:
        parser.print_help()
        print("\nError: Specify --all or --sheet", file=sys.stderr)
        sys.exit(1)

    # Ensure output directory exists
    os.makedirs(args.output_dir, exist_ok=True)

    # Determine which sheets to fetch
    if args.all:
        sheets_to_fetch = GLOSSARY_SHEETS.items()
    else:
        sheets_to_fetch = [(args.sheet, GLOSSARY_SHEETS[args.sheet])]

    print(f"Fetching {len(list(sheets_to_fetch))} sheet(s) to {args.output_dir}")
    print()

    # Re-create iterator since we consumed it
    if args.all:
        sheets_to_fetch = GLOSSARY_SHEETS.items()
    else:
        sheets_to_fetch = [(args.sheet, GLOSSARY_SHEETS[args.sheet])]

    success_count = 0
    total = 0
    for sheet_name, gid in sheets_to_fetch:
        total += 1
        if fetch_sheet(sheet_name, gid, args.output_dir, force=args.force):
            success_count += 1

    print()
    print(f"Completed: {success_count}/{total} sheets fetched successfully")

    if success_count != total:
        sys.exit(1)


if __name__ == '__main__':
    main()
