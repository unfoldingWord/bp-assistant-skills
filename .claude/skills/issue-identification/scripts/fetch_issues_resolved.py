"""
Fetch the Issues Resolved Google Doc containing decisions about translation notes.
Default document: Content Meeting Issues Resolved

Usage:
    python .claude/skills/issue-identification/scripts/fetch_issues_resolved.py              # Fetch if not already fetched today
    python .claude/skills/issue-identification/scripts/fetch_issues_resolved.py --force      # Force fetch even if already fetched today
    python .claude/skills/issue-identification/scripts/fetch_issues_resolved.py -o file.txt  # Specify output file
"""
import requests
import sys
import os
from datetime import date, timedelta

DEFAULT_DOC_ID = "1C0C7Qsm78fM0tuLyVZEAs-IWtClNo9nqbsAZkAFeFio"
# Resolve path relative to script location
# Script is in .claude/skills/issue-identification/scripts/
# Project root is 4 levels up
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(SCRIPT_DIR))))
DEFAULT_OUTPUT = os.path.join(PROJECT_ROOT, "data", "issues_resolved.txt")

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


def fetch_gdoc(doc_id=None, output_file=None, force=False):
    """Fetch a public Google Doc as plain text with daily caching."""
    doc_id = doc_id or DEFAULT_DOC_ID
    output_file = output_file or DEFAULT_OUTPUT
    today = date.today().isoformat()

    # Check if we already fetched today -- also refresh weekly on Thursdays
    cached_date = get_cached_date(output_file)
    if cached_date == today and not force and not should_refresh_weekly(cached_date):
        with open(output_file, 'r', encoding='utf-8') as f:
            content = f.read()
        return content

    # Fetch fresh content
    url = f"https://docs.google.com/document/d/{doc_id}/export?format=txt"
    response = requests.get(url)
    if response.status_code == 200:
        text = response.text.lstrip('\ufeff')  # Remove BOM
        # Add date stamp as first line
        text_with_date = f"# Fetched: {today}\n{text}"
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(text_with_date)
        return text_with_date
    else:
        return f"Error: {response.status_code}"

if __name__ == "__main__":
    # Fix Windows console encoding
    if sys.platform == "win32":
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')

    force = "--force" in sys.argv
    output = DEFAULT_OUTPUT

    # Parse -o flag for output file
    if "-o" in sys.argv:
        idx = sys.argv.index("-o")
        if idx + 1 < len(sys.argv):
            output = sys.argv[idx + 1]

    result = fetch_gdoc(output_file=output, force=force)
    print(result)
