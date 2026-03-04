#!/usr/bin/env python3
"""
insert_tn_rows.py - Replace translation note rows in a book-level TSV file.

Default mode: verse-aware chapter replacement — detects which verses are
present in the source file and only removes existing rows for those verses.
Rows for verses not covered by the source file are preserved. When the source
covers all verses in a chapter, this behaves identically to a full wipe.

Usage:
  python3 insert_tn_rows.py \
    --book-file /mnt/c/.../en_tn/tn_PSA.tsv \
    --source-file output/notes/PSA-058.tsv \
    --chapter 58 \
    [--skip-intro] [--per-reference] \
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
            vs = int(verse_str.split('-')[0])
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


def get_chapter(ref):
    """Extract the chapter number from a reference string."""
    parts = ref.split(':', 1)
    if parts[0] == 'front':
        return -1
    try:
        return int(parts[0])
    except ValueError:
        return 999999


def is_intro_ref(ref):
    """Check if a reference is a chapter intro (e.g. '58:intro')."""
    parts = ref.split(':', 1)
    return len(parts) == 2 and parts[1] == 'intro'


def group_by_reference(rows):
    """Group rows by their reference, preserving order within each group."""
    groups = OrderedDict()
    for row in rows:
        ref = get_reference(row)
        if ref not in groups:
            groups[ref] = []
        groups[ref].append(row)
    return groups


def find_chapter_bounds(book_rows, chapter):
    """Find start and end indices of all rows belonging to a chapter.

    Returns (start, end) where end is exclusive, or (None, None) if chapter
    not found.
    """
    chapter_start = None
    chapter_end = None
    for i, row in enumerate(book_rows):
        row_ch = get_chapter(get_reference(row))
        if row_ch == chapter:
            if chapter_start is None:
                chapter_start = i
            chapter_end = i + 1

    return (chapter_start, chapter_end)


def find_insert_position(book_rows, ref_sort_key):
    """Find the position to insert rows for a new reference.

    Locates the chapter block first, then positions within it.
    This avoids misplacement from data anomalies (e.g. typos like 559:1).

    Returns the index where the new rows should be inserted (before this index).
    """
    target_ch, target_vs = ref_sort_key

    # Find the contiguous block of rows belonging to this chapter
    chapter_start, chapter_end = find_chapter_bounds(book_rows, target_ch)

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


def find_chapter_insert_position(book_rows, chapter):
    """Find position to insert a whole chapter's worth of rows.

    Returns the index where the chapter rows should be inserted.
    """
    for i, row in enumerate(book_rows):
        row_ch = get_chapter(get_reference(row))
        if row_ch > chapter:
            return i
    return len(book_rows)


def detect_line_ending(filepath):
    """Detect the line ending used in the file."""
    with open(filepath, 'rb') as f:
        content = f.read(4096)
    if b'\r\n' in content:
        return '\r\n'
    return '\n'


def do_per_reference(book_rows, source_groups):
    """Original per-reference replacement logic."""
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
            for idx in indices_to_remove[:3]:
                print(f"    - {new_rows[idx][:100]}")
            if len(indices_to_remove) > 3:
                print(f"    ... ({len(indices_to_remove) - 3} more)")

            for idx in reversed(indices_to_remove):
                del new_rows[idx]
            total_removed += len(indices_to_remove)
        else:
            insert_pos = find_insert_position(new_rows, ref_sort_key)
            print(f"  {ref}: inserting {len(new_ref_rows)} new rows at position {insert_pos}")

        for i, row in enumerate(new_ref_rows):
            new_rows.insert(insert_pos + i, row)
        total_added += len(new_ref_rows)

    return new_rows, total_removed, total_added


def do_full_chapter(book_rows, source_rows, chapter, skip_intro):
    """Verse-aware chapter replacement: only replace verses present in source.

    Detects which verses the source file covers and removes only those verses
    from the existing book data, preserving rows for verses not in the source.
    When the source covers all verses this behaves identically to a full wipe.
    """
    new_rows = list(book_rows)

    # Build set of verse references present in the source file
    source_refs = set()
    for row in source_rows:
        ref = get_reference(row)
        if get_chapter(ref) == chapter:
            source_refs.add(ref)

    # Find existing chapter bounds
    chapter_start, chapter_end = find_chapter_bounds(new_rows, chapter)

    # Collect existing intro rows for this chapter
    existing_intro_rows = []
    if chapter_start is not None:
        for i in range(chapter_start, chapter_end):
            ref = get_reference(new_rows[i])
            if is_intro_ref(ref) and get_chapter(ref) == chapter:
                existing_intro_rows.append(new_rows[i])

    # Check if source has intro rows
    source_has_intro = any(
        is_intro_ref(get_reference(row)) and get_chapter(get_reference(row)) == chapter
        for row in source_rows
    )

    # Determine which intro rows to preserve
    preserve_intro = []
    if skip_intro and existing_intro_rows:
        # Always preserve existing intro when --skip-intro
        preserve_intro = existing_intro_rows
    elif not source_has_intro and existing_intro_rows:
        # Source doesn't have intro, preserve existing
        preserve_intro = existing_intro_rows

    # Filter source rows: remove intro rows if we're preserving existing ones
    filtered_source = source_rows
    if preserve_intro:
        filtered_source = [
            row for row in source_rows
            if not (is_intro_ref(get_reference(row)) and get_chapter(get_reference(row)) == chapter)
        ]

    # Identify which existing rows to remove: only those whose reference
    # matches a verse in the source file
    total_removed = 0
    preserved_rows = []  # existing rows for verses NOT in source
    if chapter_start is not None:
        indices_to_remove = []
        for i in range(chapter_start, chapter_end):
            ref = get_reference(new_rows[i])
            if ref in source_refs:
                indices_to_remove.append(i)
            elif is_intro_ref(ref) and ref in source_refs:
                indices_to_remove.append(i)
            else:
                # This row's verse is not in the source -- preserve it
                # (intro rows handled separately via preserve_intro logic)
                if not (is_intro_ref(ref) and ref.split(':', 1)[1] == 'intro'):
                    preserved_rows.append(new_rows[i])

        removed = [new_rows[i] for i in indices_to_remove]
        # Also count intro rows that will be replaced (not in preserve list)
        intro_removed = []
        if not preserve_intro:
            for i in range(chapter_start, chapter_end):
                ref = get_reference(new_rows[i])
                if is_intro_ref(ref) and get_chapter(ref) == chapter:
                    if new_rows[i] not in removed:
                        intro_removed.append(i)

        all_remove_indices = sorted(set(indices_to_remove + intro_removed))
        total_removed = len(all_remove_indices)

        # Remove ALL chapter rows (we'll re-insert preserved + new)
        del new_rows[chapter_start:chapter_end]
        insert_pos = chapter_start

        if preserved_rows:
            print(f"  Removed {total_removed} existing rows for verses in source")
            print(f"  Preserving {len(preserved_rows)} existing rows for verses not in source")
        else:
            print(f"  Removed {total_removed} existing rows for chapter {chapter}")

        # Show a few removed rows
        for row in removed[:3]:
            print(f"    - {row[:100]}")
        if len(removed) > 3:
            print(f"    ... ({len(removed) - 3} more)")
    else:
        insert_pos = find_chapter_insert_position(new_rows, chapter)
        print(f"  Chapter {chapter} not found in book file; inserting at position {insert_pos}")

    # Build rows to insert: preserved intro + source rows + preserved non-source rows
    # Merge preserved_rows and filtered_source in correct verse order
    combined = []
    if preserve_intro:
        combined.extend(preserve_intro)
    combined.extend(filtered_source)
    combined.extend(preserved_rows)
    # Sort by reference to maintain correct order
    combined.sort(key=lambda row: parse_reference(get_reference(row)))

    total_added = len(combined)

    if preserve_intro:
        print(f"  Preserved {len(preserve_intro)} existing intro row(s)")

    # Insert
    for i, row in enumerate(combined):
        new_rows.insert(insert_pos + i, row)

    print(f"  Inserted {total_added} rows for chapter {chapter}")

    return new_rows, total_removed, total_added


def main():
    parser = argparse.ArgumentParser(
        description='Replace TN rows in a book-level TSV file'
    )
    parser.add_argument('--book-file', required=True,
                        help='Path to the full book TN TSV file')
    parser.add_argument('--source-file', required=True,
                        help='Path to the source TSV with replacement rows')
    parser.add_argument('--chapter', type=int, required=True,
                        help='Chapter number being replaced')
    parser.add_argument('--references', default=None,
                        help='Comma-separated list of references to replace (only with --per-reference)')
    parser.add_argument('--per-reference', action='store_true',
                        help='Use old per-reference replacement instead of full-chapter replacement')
    parser.add_argument('--skip-intro', action='store_true',
                        help='Preserve existing intro row even if source has one')
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

    if args.per_reference:
        # Legacy per-reference mode
        source_groups = group_by_reference(source_rows)

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

        print(f"Mode: per-reference replacement")
        print(f"References to insert/replace: {', '.join(source_groups.keys())}")
        print(f"Total source rows: {sum(len(v) for v in source_groups.values())}")
        print()

        new_rows, total_removed, total_added = do_per_reference(book_rows, source_groups)
    else:
        # Full-chapter replacement (default)
        print(f"Mode: verse-aware chapter replacement (chapter {args.chapter})")
        print(f"Source rows: {len(source_rows)}")
        if args.skip_intro:
            print(f"Preserving existing intro row (--skip-intro)")
        print()

        new_rows, total_removed, total_added = do_full_chapter(
            book_rows, source_rows, args.chapter, args.skip_intro
        )

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
