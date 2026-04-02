"""
Fetch the TN Templates Google Spreadsheet containing templates for translation notes.
Default spreadsheet: Sample TN Templates
Can fetch specific sheets by name or gid.

Usage:
    python .claude/skills/utilities/scripts/fetch_templates.py                 # Fetch if not already fetched today
    python .claude/skills/utilities/scripts/fetch_templates.py --force         # Force fetch even if already fetched today
    python .claude/skills/utilities/scripts/fetch_templates.py -o file.csv     # Specify output file
"""
import requests
import sys
import os
from datetime import date

DEFAULT_SHEET_ID = "1ot6A7RxcsxM_Wv94sauoTAaRPO5Q-gynFqMHeldnM64"
# Resolve path relative to script location
# Script is in .claude/skills/utilities/scripts/
# Project root is 4 levels up
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(SCRIPT_DIR))))
DEFAULT_OUTPUT = os.path.join(PROJECT_ROOT, "data", "templates.csv")

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

def fetch_gsheet(sheet_id=None, gid=None, output_file=None, format='csv', force=False):
    """
    Fetch a public Google Sheet as CSV or TSV with daily caching.

    Args:
        sheet_id: The spreadsheet ID (from URL)
        gid: The specific sheet/tab ID (0 for first sheet, or specific gid)
        output_file: Optional file to save to
        format: 'csv' or 'tsv'
        force: Force fetch even if already fetched today
    """
    sheet_id = sheet_id or DEFAULT_SHEET_ID
    output_file = output_file or DEFAULT_OUTPUT
    today = date.today().isoformat()

    # Check if we already fetched today (only when output_file is specified)
    if output_file:
        cached_date = get_cached_date(output_file)
        if cached_date == today and not force:
            with open(output_file, 'r', encoding='utf-8') as f:
                content = f.read()
            print(f"Using cached templates from {today}")
            return content

    # Build export URL
    url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format={format}"
    if gid is not None:
        url += f"&gid={gid}"

    response = requests.get(url)
    if response.status_code == 200:
        text = response.text.lstrip('\ufeff')  # Remove BOM
        if output_file:
            # Add date stamp as first line (comment line for CSV)
            text_with_date = f"# Fetched: {today}\n{text}"
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(text_with_date)
            return f"Saved to {output_file}"
        return text
    else:
        return f"Error: {response.status_code}"

def list_sheets(sheet_id=None):
    """
    Note: Google Sheets API would be needed for proper sheet listing.
    For now, common gids for the TN Templates spreadsheet:
    - 0: First sheet (usually main templates)
    - Check spreadsheet URL for specific gid values
    """
    return """Known sheets in TN Templates spreadsheet:
- gid=0: Main templates
- gid=1835633752: Biblical weights and measures
- Check the spreadsheet URL for other gid values (shown as #gid=NUMBER)
"""

if __name__ == "__main__":
    # Fix Windows console encoding
    if sys.platform == "win32":
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')

    import argparse
    parser = argparse.ArgumentParser(description='Fetch Google Sheets content')
    parser.add_argument('--sheet-id', default=DEFAULT_SHEET_ID, help='Spreadsheet ID')
    parser.add_argument('--gid', type=int, default=None, help='Sheet/tab gid')
    parser.add_argument('--output', '-o', default=None, help='Output file')
    parser.add_argument('--format', '-f', choices=['csv', 'tsv'], default='csv')
    parser.add_argument('--list', action='store_true', help='List known sheets')
    parser.add_argument('--force', action='store_true', help='Force fetch even if already fetched today')

    args = parser.parse_args()

    if args.list:
        print(list_sheets(args.sheet_id))
    else:
        result = fetch_gsheet(args.sheet_id, args.gid, args.output, args.format, args.force)
        print(result)
