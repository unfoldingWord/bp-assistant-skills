#!/usr/bin/env python3
r"""
extract_ult_english.py - Extract English text from aligned USFM files

Strips alignment markers (\zaln-s, \zaln-e, \w...\w*) from aligned USFM,
leaving clean English text with standard USFM structure preserved.

Usage:
    python extract_ult_english.py                    # Process all files
    python extract_ult_english.py --books GEN EXO    # Process specific books
    python extract_ult_english.py --force            # Force re-process all

Input: data/published_ult/*.usfm (aligned USFM with \zaln markers)
Output: data/published_ult_english/*.usfm (clean English USFM)
"""

import argparse
import os
import re
import sys
from datetime import date

# Script location and project root
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(SCRIPT_DIR))))
INPUT_DIR = os.path.join(PROJECT_ROOT, "data", "published_ult")
OUTPUT_DIR = os.path.join(PROJECT_ROOT, "data", "published_ult_english")


def get_cached_date(filepath):
    """Check if file exists and return the date from its first line."""
    if not os.path.exists(filepath):
        return None
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            first_line = f.readline().strip()
            if first_line.startswith("# Fetched: ") or first_line.startswith("# Extracted: "):
                return first_line.split(": ", 1)[1]
    except:
        pass
    return None


def strip_alignment_markers(content):
    r"""
    Remove alignment markers from USFM content, preserving structure.

    Removes:
    - \zaln-s | ... \* (alignment start markers with attributes)
    - \zaln-e\* (alignment end markers)
    - \w ... | ... \w* (word markers with attributes) -> keeps just the word

    Preserves:
    - \v, \p, \q1, \q2, \s, \c, etc. (standard USFM markers)
    - Verse text and structure

    Also joins words that were on separate lines back into continuous text.
    """
    # Remove \zaln-s markers (multi-line possible)
    # Pattern: \zaln-s | attributes \*
    content = re.sub(r'\\zaln-s\s*\|[^*]*\*', '', content)

    # Remove \zaln-e markers
    content = re.sub(r'\\zaln-e\\\*', '', content)

    # Extract words from \w markers: \w word|attributes\w* -> word
    # The word is between \w and the pipe |
    content = re.sub(r'\\w\s+([^|]+)\|[^*]*\\w\*', r'\1', content)

    # Also handle \w markers without attributes: \w word\w* -> word
    content = re.sub(r'\\w\s+([^\\]+)\\w\*', r'\1', content)

    # Join words that are on separate lines into continuous text
    # The aligned USFM has one word per line, we want flowing sentences
    lines = content.split('\n')
    result_lines = []
    i = 0

    while i < len(lines):
        line = lines[i]
        stripped = line.strip()

        # Check if this line is a USFM marker line, comment, or empty
        if stripped == '' or stripped.startswith('#'):
            result_lines.append(line)
            i += 1
        elif stripped.startswith('\\'):
            # This is a USFM marker line - collect it plus any following text
            # until we hit another marker or empty line
            marker_line = line
            text_parts = []
            i += 1

            # Collect following text lines
            while i < len(lines):
                next_line = lines[i].strip()
                if next_line == '' or next_line.startswith('\\') or next_line.startswith('#'):
                    break
                text_parts.append(next_line)
                i += 1

            # Join marker with its text
            if text_parts:
                result_lines.append(marker_line + ' ' + ' '.join(text_parts))
            else:
                result_lines.append(marker_line)
        else:
            # Plain text line (shouldn't happen often after markers are processed)
            result_lines.append(line)
            i += 1

    content = '\n'.join(result_lines)

    # Clean up multiple spaces
    content = re.sub(r'  +', ' ', content)

    # Clean up spaces before punctuation
    content = re.sub(r' +([.,;:!?\'")}])', r'\1', content)

    # Clean up spaces after opening punctuation
    content = re.sub(r'([{(\'"]) +', r'\1', content)

    # Clean up spaces at end of lines
    content = re.sub(r' +\n', '\n', content)

    # Clean up multiple blank lines
    content = re.sub(r'\n{3,}', '\n\n', content)

    return content


def process_file(input_path, output_path, force=False):
    """Process a single USFM file."""
    filename = os.path.basename(input_path)
    today = date.today().isoformat()

    # Check cache
    if not force:
        cached_date = get_cached_date(output_path)
        if cached_date:
            print(f"  {filename}: Using cached version from {cached_date}")
            return True

    # Read input
    try:
        with open(input_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        print(f"  {filename}: Error reading - {e}", file=sys.stderr)
        return False

    # Skip the "# Fetched:" line if present
    if content.startswith("# Fetched:"):
        content = content.split('\n', 1)[1]

    # Strip alignment markers
    print(f"  {filename}: Extracting English text...")
    clean_content = strip_alignment_markers(content)

    # Add date header and save
    clean_content = f"# Extracted: {today}\n{clean_content}"
    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(clean_content)
        print(f"  {filename}: Saved to {output_path}")
        return True
    except Exception as e:
        print(f"  {filename}: Error writing - {e}", file=sys.stderr)
        return False


def main():
    parser = argparse.ArgumentParser(
        description='Extract English text from aligned USFM files',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s                    # Process all files in data/published_ult/
  %(prog)s --books GEN EXO    # Process specific books
  %(prog)s --force            # Force re-process all files
"""
    )
    parser.add_argument('--books', '-b', nargs='+',
                        help='Specific books to process (e.g., GEN EXO)')
    parser.add_argument('--force', '-f', action='store_true',
                        help='Force re-process even if cached')
    parser.add_argument('--input-dir', '-i', default=INPUT_DIR,
                        help=f'Input directory (default: {INPUT_DIR})')
    parser.add_argument('--output-dir', '-o', default=OUTPUT_DIR,
                        help=f'Output directory (default: {OUTPUT_DIR})')

    args = parser.parse_args()

    # Ensure output directory exists
    os.makedirs(args.output_dir, exist_ok=True)

    # Find input files
    if not os.path.exists(args.input_dir):
        print(f"Error: Input directory not found: {args.input_dir}", file=sys.stderr)
        sys.exit(1)

    input_files = sorted([f for f in os.listdir(args.input_dir) if f.endswith('.usfm')])

    if not input_files:
        print(f"No USFM files found in {args.input_dir}", file=sys.stderr)
        sys.exit(1)

    # Filter by books if specified
    if args.books:
        book_codes = [b.upper() for b in args.books]
        input_files = [f for f in input_files if any(f.upper().endswith(f'-{b}.USFM') for b in book_codes)]

    print(f"Processing {len(input_files)} file(s) from {args.input_dir}")
    print()

    success_count = 0
    for filename in input_files:
        input_path = os.path.join(args.input_dir, filename)
        output_path = os.path.join(args.output_dir, filename)
        if process_file(input_path, output_path, force=args.force):
            success_count += 1

    print()
    print(f"Completed: {success_count}/{len(input_files)} files processed successfully")

    if success_count != len(input_files):
        sys.exit(1)


if __name__ == '__main__':
    main()
