#!/usr/bin/env python3
"""
Filter Psalms USFM files to keep only specified chapter ranges.
Keeps: 1-29, 42-57, 90-118
Removes: 30-41, 58-89, 119-150
"""

import re
import sys
from pathlib import Path

KEEP_RANGES = [(1, 29), (42, 57), (90, 118)]

def should_keep_chapter(chapter_num):
    """Check if a chapter number should be kept."""
    for start, end in KEEP_RANGES:
        if start <= chapter_num <= end:
            return True
    return False

def filter_usfm(input_path, output_path=None):
    """Filter USFM file to keep only specified chapters."""
    if output_path is None:
        output_path = input_path

    with open(input_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Split by chapter markers, keeping the delimiter
    # Pattern matches \c followed by number
    chapter_pattern = r'(\\c\s+\d+)'
    parts = re.split(chapter_pattern, content)

    # First part is the header (before first \c)
    header = parts[0]

    # Process remaining parts in pairs (chapter marker, chapter content)
    filtered_parts = [header]

    i = 1
    while i < len(parts):
        if i + 1 < len(parts):
            chapter_marker = parts[i]
            chapter_content = parts[i + 1]

            # Extract chapter number
            match = re.search(r'\\c\s+(\d+)', chapter_marker)
            if match:
                chapter_num = int(match.group(1))
                if should_keep_chapter(chapter_num):
                    filtered_parts.append(chapter_marker)
                    filtered_parts.append(chapter_content)
            i += 2
        else:
            # Odd trailing part
            i += 1

    filtered_content = ''.join(filtered_parts)

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(filtered_content)

    return output_path

def main():
    files = [
        '/home/bmw/Documents/dev/cSkillBP/data/published_ult/19-PSA.usfm',
        '/home/bmw/Documents/dev/cSkillBP/data/published_ult_english/19-PSA.usfm',
        '/home/bmw/Documents/dev/cSkillBP/data/published_ust/19-PSA.usfm',
    ]

    for filepath in files:
        path = Path(filepath)
        if path.exists():
            print(f"Processing {filepath}...")
            # Get original size
            original_size = path.stat().st_size

            # Filter the file
            filter_usfm(filepath)

            # Get new size
            new_size = path.stat().st_size

            print(f"  Original: {original_size:,} bytes")
            print(f"  Filtered: {new_size:,} bytes")
            print(f"  Removed: {original_size - new_size:,} bytes ({100*(original_size-new_size)/original_size:.1f}%)")
        else:
            print(f"File not found: {filepath}")

if __name__ == '__main__':
    main()
