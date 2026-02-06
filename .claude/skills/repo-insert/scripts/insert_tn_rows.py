#!/usr/bin/env python3
"""
insert_tn_rows.py - Surgically replace translation note rows in a book-level TSV file.

Usage:
  python3 insert_tn_rows.py \
    --book-file /mnt/c/.../en_tn/tn_PSA.tsv \
    --source-file output/notes/PSA-058.tsv \
    [--references 58:2,58:3] \
    [--dry-run] [--backup]

TSV format: Reference<tab>ID<tab>Tags<tab>SupportReference<tab>Quote<tab>Occurrence<tab>Note
"""

import argparse
import os
import re
import shutil
import sys
from collections import OrderedDict


def parse_reference(ref):
    """Parse a reference string into a sortable tuple.

    Sort order: front:intro < front:* < 1:intro < 1:1 < 1:2 < ... < 2:intro ...
    """
    parts = ref.split(':', 1)
    if len(parts) != 2:
        return (999999, 999999)

    chapter_str, verse_str = parts

    # Chapter sort key
    if chapter_str == 'front':
        ch = -1
    else:
        try:
            ch = int(chapter_str)
        except ValueError:
            ch = 999999

    # Verse sort key: intro < front < 1 < 2 < ...
    if verse_str == 'intro':
        vs = -2
    elif verse_str == 'front':
        vs = -1
    else:
        try:
            vs = int(verse_str)
        except ValueError:
            vs = 999999

    return (ch, vs)


def read_tsv(filepath):
    """Read a TSV file, returning (header_line, rows).

    Each row is the raw line string (preserving tabs).
    """
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    lines = content.split('\n')
    # Remove trailing empty line
    if lines and lines[-1] == '':
        lines = lines[:-1]

    if not lines:
        return None, []

    header = lines[0]
    rows = lines[1:]
    return header, rows


def get_reference(row):
    """Extract the Reference field (column 0) from a TSV row."""
    return row.split('\t', 1)[0]


def group_by_reference(rows):
    """Group rows by their reference, preserving order within each group."""
    groups = OrderedDict()
    for row in rows:
        ref = get_reference(row)
        if ref not in groups:
            groups[ref] = []
        groups[ref].append(row)
    return groups


def find_insert_position(book_rows, ref_sort_key):
    """Find the position to insert rows for a new reference.

    Locates the chapter block first, then positions within it.
    This avoids misplacement from data anomalies (e.g. typos like 559:1).

    Returns the index where the new rows should be inserted (before this index).
    """
    target_ch, target_vs = ref_sort_key

    # Find the contiguous block of rows belonging to this chapter
    chapter_start = None
    chapter_end = None
    for i, row in enumerate(book_rows):
        row_ch = parse_reference(get_reference(row))[0]
        if row_ch == target_ch:
            if chapter_start is None:
                chapter_start = i
            chapter_end = i + 1

    if chapter_start is not None:
        # Chapter exists -- find correct position within the chapter block
        for i in range(chapter_start, chapter_end):
            row_vs = parse_reference(get_reference(book_rows[i]))[1]
            if row_vs > target_vs:
                return i
        return chapter_end
    else:
        # Chapter doesn't exist -- find position by chapter order
        for i, row in enumerate(book_rows):
            row_ch = parse_reference(get_reference(row))[0]
            if row_ch > target_ch:
                return i
        return len(book_rows)


def detect_line_ending(filepath):
    """Detect the line ending used in the file."""
    with open(filepath, 'rb') as f:
        content = f.read(4096)
    if b'\r\n' in content:
        return '\r\n'
    return '\n'


def main():
    parser = argparse.ArgumentParser(
        description='Surgically replace TN rows in a book-level TSV file'
    )
    parser.add_argument('--book-file', required=True,
                        help='Path to the full book TN TSV file')
    parser.add_argument('--source-file', required=True,
                        help='Path to the source TSV with replacement rows')
    parser.add_argument('--references', default=None,
                        help='Comma-separated list of references to replace (default: all from source)')
    parser.add_argument('--dry-run', action='store_true',
                        help='Show what would change without modifying the file')
    parser.add_argument('--backup', action='store_true',
                        help='Create a .bak backup before modifying')

    args = parser.parse_args()

    line_ending = detect_line_ending(args.book_file)

    # Read files
    book_header, book_rows = read_tsv(args.book_file)
    source_header, source_rows = read_tsv(args.source_file)

    if book_header is None:
        print("ERROR: Book file is empty", file=sys.stderr)
        sys.exit(1)

    if not source_rows:
        print("ERROR: Source file has no data rows", file=sys.stderr)
        sys.exit(1)

    # Group source rows by reference
    source_groups = group_by_reference(source_rows)

    # Filter to requested references if specified
    if args.references:
        requested = [r.strip() for r in args.references.split(',')]
        filtered = OrderedDict()
        for ref in requested:
            if ref in source_groups:
                filtered[ref] = source_groups[ref]
            else:
                print(f"WARNING: Reference {ref} not found in source file",
                      file=sys.stderr)
        source_groups = filtered

    if not source_groups:
        print("ERROR: No matching references to insert", file=sys.stderr)
        sys.exit(1)

    print(f"References to insert/replace: {', '.join(source_groups.keys())}")
    print(f"Total source rows: {sum(len(v) for v in source_groups.values())}")
    print()

    # Process each reference group
    new_rows = list(book_rows)
    total_removed = 0
    total_added = 0

    for ref, new_ref_rows in source_groups.items():
        ref_sort_key = parse_reference(ref)

        # Find and remove existing rows with this reference
        indices_to_remove = []
        for i, row in enumerate(new_rows):
            if get_reference(row) == ref:
                indices_to_remove.append(i)

        if indices_to_remove:
            insert_pos = indices_to_remove[0]
            print(f"  {ref}: replacing {len(indices_to_remove)} existing rows with {len(new_ref_rows)} new rows")
            # Show existing rows being removed
            for idx in indices_to_remove[:3]:
                print(f"    - {new_rows[idx][:100]}")
            if len(indices_to_remove) > 3:
                print(f"    ... ({len(indices_to_remove) - 3} more)")

            # Remove old rows (in reverse order to preserve indices)
            for idx in reversed(indices_to_remove):
                del new_rows[idx]
            total_removed += len(indices_to_remove)
        else:
            insert_pos = find_insert_position(new_rows, ref_sort_key)
            print(f"  {ref}: inserting {len(new_ref_rows)} new rows at position {insert_pos}")

        # Insert new rows
        for i, row in enumerate(new_ref_rows):
            new_rows.insert(insert_pos + i, row)
        total_added += len(new_ref_rows)

    print()
    print(f"Summary: removed {total_removed} rows, added {total_added} rows")
    print(f"Book rows: {len(book_rows)} -> {len(new_rows)}")

    if args.dry_run:
        print("\n[DRY RUN] No changes written.")
        return

    # Backup
    if args.backup:
        backup_path = args.book_file + '.bak'
        shutil.copy2(args.book_file, backup_path)
        print(f"Backup saved to {backup_path}")

    # Write
    all_lines = [book_header] + new_rows
    final_content = '\n'.join(all_lines) + '\n'
    if line_ending == '\r\n':
        final_content = final_content.replace('\n', '\r\n')

    with open(args.book_file, 'w', encoding='utf-8', newline='') as f:
        f.write(final_content)

    print(f"Successfully updated {args.book_file}")


if __name__ == '__main__':
    main()
