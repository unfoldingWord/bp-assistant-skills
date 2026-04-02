#!/usr/bin/env python3
r"""
insert_usfm_verses.py - Surgically replace a verse range in a book-level USFM file.

Usage:
  python3 insert_usfm_verses.py \
    --book-file /mnt/c/.../en_ult/19-PSA.usfm \
    --source-file output/AI-ULT/PSA-119-100-104-aligned.usfm \
    --chapter 119 --verses 100-104 \
    [--dry-run] [--backup]

The source file should be AI-generated aligned USFM. Header lines (\id, \usfm,
\ide, \h, \toc*, \mt, \c N) are stripped -- only verse content from the first
\v onward is used.
"""

import argparse
import os
import re
import shutil
import sys


HEADER_MARKERS = re.compile(r'^\\(id|usfm|ide|h|toc\d?|mt\d?|c)\b')

# Book-level markers that must never appear in inserted verse content.
# These are stripped from the entire source, not just the header, because
# aligned USFM sometimes scatters them throughout the file.
BOOK_LEVEL_JUNK = re.compile(r'^\\(id|usfm|ide|h|toc\d?|mt\d?|cl)\b')


def parse_verse_range(spec):
    """Parse '100-104' or '100' into (start, end) ints."""
    if '-' in spec:
        parts = spec.split('-', 1)
        return int(parts[0]), int(parts[1])
    v = int(spec)
    return v, v


INTER_VERSE_MARKERS = re.compile(r'^\\(d\b|ts\\\*|s\d+\s|qa\s|b\s*$)')


def strip_source_header(lines):
    """Remove header lines from source, return content from first \\v onward.

    Preserves inter-verse markers (\\d, \\cl, \\ts\\*, etc.) that appear
    between the headers and the first verse.
    """
    result = []
    found_verse = False
    pre_verse_markers = []
    for line in lines:
        stripped = line.strip()
        if not found_verse:
            if HEADER_MARKERS.match(stripped):
                continue
            if stripped == '':
                continue
            # Preserve inter-verse markers that come before \v 1
            if INTER_VERSE_MARKERS.match(stripped):
                pre_verse_markers.append(line)
                continue
            # Check if this line or any part of it contains \v
            if '\\v ' in stripped:
                found_verse = True
                result.extend(pre_verse_markers)
                result.append(line)
            # Also accept lines that start with \q markers followed by \v
            elif re.match(r'^\\q\d?\s', stripped) and '\\v ' in stripped:
                found_verse = True
                result.extend(pre_verse_markers)
                result.append(line)
        else:
            result.append(line)

    # Final pass: remove any book-level markers that leaked into verse content.
    # Aligned USFM sometimes scatters \toc*, \mt, \cl, etc. throughout the file.
    result = [line for line in result if not BOOK_LEVEL_JUNK.match(line.strip())]
    return result


def find_chapter_range(lines, chapter):
    """Find the line range for a chapter: (start_of_chapter_content, end).

    Returns (content_start, chapter_end) where:
    - content_start is the line after \\c N
    - chapter_end is the line of the next \\c or len(lines)
    """
    chapter_line = None
    chapter_end = None
    pattern = re.compile(rf'^\\c\s+{chapter}\s*$')

    for i, line in enumerate(lines):
        if pattern.match(line.strip()):
            chapter_line = i
            break

    if chapter_line is None:
        return None, None

    # Find end of chapter (next \c or EOF)
    for i in range(chapter_line + 1, len(lines)):
        if re.match(r'^\\c\s+\d+', lines[i].strip()):
            chapter_end = i
            break
    if chapter_end is None:
        chapter_end = len(lines)

    return chapter_line + 1, chapter_end


def find_verse_boundaries(lines, start_idx, end_idx, verse_start, verse_end):
    """Within a chapter range, find the line boundaries for a verse range.

    Returns (replace_start, replace_end) where:
    - replace_start: first line of verse_start content (including preceding poetry markers)
    - replace_end: first line of verse_end+1 (exclusive), or chapter end
    """
    replace_start = None
    replace_end = None
    next_verse = verse_end + 1

    verse_start_pat = re.compile(rf'\\v\s+{verse_start}\s')
    next_verse_pat = re.compile(rf'\\v\s+{next_verse}\s')

    for i in range(start_idx, end_idx):
        line = lines[i]
        # Find start of our verse range
        if replace_start is None and verse_start_pat.search(line):
            replace_start = i
            # Walk backward past inter-verse markers (\cl, \d, \ts\*, \s1, etc.)
            # that belong to this verse rather than the previous verse's content
            while replace_start > start_idx:
                prev = lines[replace_start - 1].strip()
                if (prev in ('\\ts\\*', '\\s5')
                        or re.match(r'^\\s\d+\s', prev)
                        or re.match(r'^\\(cl|d)\b', prev)):
                    replace_start -= 1
                else:
                    break

        # Find start of the verse AFTER our range
        if replace_start is not None and next_verse_pat.search(line):
            replace_end = i
            break

    if replace_start is not None and replace_end is None:
        replace_end = end_idx

    return replace_start, replace_end


def count_verse_markers(lines, start_idx, end_idx):
    """Count \\v markers in a line range."""
    count = 0
    for i in range(start_idx, end_idx):
        count += len(re.findall(r'\\v\s+\d+\s', lines[i]))
    return count


def detect_line_ending(content):
    """Detect the dominant line ending in the file."""
    if '\r\n' in content:
        return '\r\n'
    return '\n'


def main():
    parser = argparse.ArgumentParser(
        description='Surgically replace verses in a book-level USFM file'
    )
    parser.add_argument('--book-file', required=True,
                        help='Path to the full book USFM file')
    parser.add_argument('--source-file', required=True,
                        help='Path to the source USFM with replacement verses')
    parser.add_argument('--chapter', required=True, type=int,
                        help='Chapter number')
    parser.add_argument('--verses', required=True,
                        help='Verse range (e.g., 100-104 or 5)')
    parser.add_argument('--dry-run', action='store_true',
                        help='Show what would change without modifying the file')
    parser.add_argument('--backup', action='store_true',
                        help='Create a .bak backup before modifying')

    args = parser.parse_args()
    verse_start, verse_end = parse_verse_range(args.verses)

    # Read files
    with open(args.book_file, 'r', encoding='utf-8') as f:
        book_content = f.read()

    line_ending = detect_line_ending(book_content)
    book_lines = book_content.split('\n')
    # Remove trailing empty element from split if file ends with newline
    if book_lines and book_lines[-1] == '':
        trailing_newline = True
        book_lines = book_lines[:-1]
    else:
        trailing_newline = False

    with open(args.source_file, 'r', encoding='utf-8') as f:
        source_content = f.read()
    source_lines = source_content.split('\n')
    if source_lines and source_lines[-1] == '':
        source_lines = source_lines[:-1]

    # Strip source headers
    source_verses = strip_source_header(source_lines)
    if not source_verses:
        print("ERROR: No verse content found in source file after stripping headers.",
              file=sys.stderr)
        sys.exit(1)

    # Find chapter range
    ch_start, ch_end = find_chapter_range(book_lines, args.chapter)
    if ch_start is None:
        print(f"ERROR: Chapter {args.chapter} not found in {args.book_file}",
              file=sys.stderr)
        sys.exit(1)

    # Find verse boundaries
    v_start, v_end = find_verse_boundaries(
        book_lines, ch_start, ch_end, verse_start, verse_end
    )
    if v_start is None:
        print(f"ERROR: Verse {verse_start} not found in chapter {args.chapter}",
              file=sys.stderr)
        sys.exit(1)

    # Pre-insertion verse count
    pre_count = count_verse_markers(book_lines, ch_start, ch_end)

    # Show what's being replaced
    print(f"Chapter {args.chapter}, verses {verse_start}-{verse_end}")
    print(f"Replacing lines {v_start+1}-{v_end} (1-indexed)")
    print()

    # Show neighbors
    if v_start > ch_start:
        prev_line = max(ch_start, v_start - 2)
        print("--- Before replaced section (last 2 lines) ---")
        for i in range(prev_line, v_start):
            print(f"  {i+1}: {book_lines[i][:120]}")
        print()

    print("--- Current content (being replaced) ---")
    for i in range(v_start, min(v_end, v_start + 5)):
        print(f"  {i+1}: {book_lines[i][:120]}")
    if v_end - v_start > 5:
        print(f"  ... ({v_end - v_start - 5} more lines)")
    print()

    print("--- New content (from source) ---")
    for i, line in enumerate(source_verses[:5]):
        print(f"  {line[:120]}")
    if len(source_verses) > 5:
        print(f"  ... ({len(source_verses) - 5} more lines)")
    print()

    if v_end < ch_end:
        after_line = min(ch_end, v_end + 2)
        print("--- After replaced section (first 2 lines) ---")
        for i in range(v_end, after_line):
            print(f"  {i+1}: {book_lines[i][:120]}")
        print()

    if args.dry_run:
        print("[DRY RUN] No changes written.")
        return

    # Build new file content
    new_lines = book_lines[:v_start] + source_verses + book_lines[v_end:]

    # Post-insertion verse count
    new_ch_start, new_ch_end = find_chapter_range(new_lines, args.chapter)
    post_count = count_verse_markers(new_lines, new_ch_start, new_ch_end)

    if pre_count != post_count:
        print(f"WARNING: Verse marker count changed! Before: {pre_count}, After: {post_count}",
              file=sys.stderr)
    else:
        print(f"Verse marker count: {post_count} (unchanged)")

    # Verify inserted verses are present
    inserted_text = '\n'.join(source_verses)
    for v in range(verse_start, verse_end + 1):
        if not re.search(rf'\\v\s+{v}\s', inserted_text):
            print(f"WARNING: \\v {v} not found in inserted content", file=sys.stderr)

    # Backup
    if args.backup:
        backup_path = args.book_file + '.bak'
        shutil.copy2(args.book_file, backup_path)
        print(f"Backup saved to {backup_path}")

    # Write
    final_content = ('\n'.join(new_lines))
    if trailing_newline:
        final_content += '\n'
    # Restore original line endings
    if line_ending == '\r\n':
        final_content = final_content.replace('\n', '\r\n')

    with open(args.book_file, 'w', encoding='utf-8', newline='') as f:
        f.write(final_content)

    print(f"Successfully replaced verses {verse_start}-{verse_end} in chapter {args.chapter}")


if __name__ == '__main__':
    main()
