#!/usr/bin/env python3
"""
Split an issue TSV into verse-range chunks for parallel processing.

Handles two issue TSV formats:
  5-col with header: Book  Reference  SupportReference  ULT_Text  Explanation
  7-col headerless:  Book  Ref  SRef  GLQuote  Go?  AT  Explanation

Supports a stanza lookup table for chapters with structured verse groupings
(e.g., PSA 119 has 22 eight-verse stanzas tied to Hebrew alphabet letters).

Usage:
    python3 split_tsv.py output/issues/PSA/PSA-119.tsv --chunk-size 24
    python3 split_tsv.py output/issues/PSA/PSA-119.tsv --ranges 1-8,9-16,17-24
    python3 split_tsv.py output/issues/PSA/PSA-132.tsv  # auto 40-verse chunks
"""

import argparse
import os
import re
import sys

# ---------------------------------------------------------------------------
# Stanza lookup: chapters whose verse groupings must align to specific
# boundaries. Each entry maps (BOOK, CHAPTER) -> list of (start, end) tuples.
# ---------------------------------------------------------------------------
STANZA_TABLE = {
    ("PSA", 119): [
        (1, 8), (9, 16), (17, 24), (25, 32), (33, 40), (41, 48),
        (49, 56), (57, 64), (65, 72), (73, 80), (81, 88), (89, 96),
        (97, 104), (105, 112), (113, 120), (121, 128), (129, 136),
        (137, 144), (145, 152), (153, 160), (161, 168), (169, 176),
    ],
}

def parse_verse_num(ref_str):
    """Extract the verse number from a reference like '119:42' or '42'.

    Returns None for intro rows (e.g., '119:intro').
    """
    if ":intro" in ref_str or ref_str.strip() == "intro":
        return None
    m = re.search(r"(\d+)$", ref_str.split(":")[1] if ":" in ref_str else ref_str)
    if m:
        return int(m.group(1))
    return None

def detect_header(first_line):
    """Detect whether first_line is a header row."""
    cols = first_line.split("\t")
    if cols and cols[0].strip().lower() == "book":
        return True
    return False

def parse_book_chapter(filepath, header, rows):
    """Infer book and chapter from filename and row data."""
    basename = os.path.basename(filepath)
    m = re.match(r"([A-Za-z0-9]+)-(\d+)", basename)
    if m:
        return m.group(1).upper(), int(m.group(2))

    # Fallback: parse from first data row
    for row in rows:
        cols = row.split("\t")
        if len(cols) >= 2:
            book = cols[0].strip().upper()
            ref = cols[1].strip()
            ch_m = re.match(r"(\d+):", ref)
            if ch_m:
                return book, int(ch_m.group(1))
    return None, None

def compute_ranges(book, chapter, max_verse, chunk_size):
    """Compute verse ranges, respecting stanza boundaries if applicable."""
    key = (book, chapter)
    if key in STANZA_TABLE:
        stanzas = STANZA_TABLE[key]
        # Group stanzas into chunks of roughly chunk_size verses
        ranges = []
        current_start = stanzas[0][0]
        current_end = stanzas[0][1]
        for s_start, s_end in stanzas[1:]:
            if (s_end - current_start + 1) <= chunk_size:
                current_end = s_end
            else:
                ranges.append((current_start, current_end))
                current_start = s_start
                current_end = s_end
        ranges.append((current_start, current_end))
        return ranges

    # Generic: split into chunk_size ranges
    ranges = []
    start = 1
    while start <= max_verse:
        end = min(start + chunk_size - 1, max_verse)
        ranges.append((start, end))
        start = end + 1
    return ranges

def parse_explicit_ranges(ranges_str):
    """Parse explicit ranges like '1-8,9-16,17-24'."""
    ranges = []
    for part in ranges_str.split(","):
        part = part.strip()
        m = re.match(r"(\d+)-(\d+)", part)
        if m:
            ranges.append((int(m.group(1)), int(m.group(2))))
        else:
            v = int(part)
            ranges.append((v, v))
    return ranges

def main():
    parser = argparse.ArgumentParser(description="Split issue TSV into verse-range chunks")
    parser.add_argument("input_tsv", help="Input issue TSV file")
    parser.add_argument("--chunk-size", type=int, default=40,
                        help="Target verses per chunk (default: 40)")
    parser.add_argument("--ranges", type=str, default=None,
                        help="Explicit ranges: '1-8,9-16,17-24,...'")
    parser.add_argument("--output-dir", type=str, default=None,
                        help="Output directory (default: same as input)")

    args = parser.parse_args()

    if not os.path.exists(args.input_tsv):
        print(f"ERROR: File not found: {args.input_tsv}", file=sys.stderr)
        sys.exit(1)

    with open(args.input_tsv, "r", encoding="utf-8") as f:
        all_lines = [line.rstrip("\n") for line in f if line.strip()]

    if not all_lines:
        print("ERROR: Empty file", file=sys.stderr)
        sys.exit(1)

    header_line = None
    data_lines = all_lines
    if detect_header(all_lines[0]):
        header_line = all_lines[0]
        data_lines = all_lines[1:]

    book, chapter = parse_book_chapter(args.input_tsv, header_line, data_lines)
    if not book or not chapter:
        print("ERROR: Could not determine book/chapter", file=sys.stderr)
        sys.exit(1)

    # Parse verse numbers to find max and assign rows to ranges
    verse_nums = []
    for line in data_lines:
        cols = line.split("\t")
        if len(cols) >= 2:
            v = parse_verse_num(cols[1].strip())
            if v is not None:
                verse_nums.append(v)

    if not verse_nums:
        print("ERROR: No verse data found", file=sys.stderr)
        sys.exit(1)

    max_verse = max(verse_nums)

    # Compute ranges
    if args.ranges:
        ranges = parse_explicit_ranges(args.ranges)
    else:
        ranges = compute_ranges(book, chapter, max_verse, args.chunk_size)

    # If only one range covers everything, no split needed
    if len(ranges) == 1 and ranges[0] == (1, max_verse):
        print(f"Only one chunk needed ({max_verse} verses), no split performed.", file=sys.stderr)
        print(os.path.abspath(args.input_tsv))
        sys.exit(0)

    # Assign rows to ranges
    output_dir = args.output_dir or os.path.dirname(args.input_tsv) or "."
    os.makedirs(output_dir, exist_ok=True)

    base_name = os.path.splitext(os.path.basename(args.input_tsv))[0]
    # Strip existing verse-range suffix if re-splitting
    base_name = re.sub(r"-v\d+-\d+$", "", base_name)

    output_files = []
    intro_lines = []  # intro rows go into the first chunk

    for line in data_lines:
        cols = line.split("\t")
        if len(cols) >= 2:
            ref = cols[1].strip()
            if ":intro" in ref or ref == "intro":
                intro_lines.append(line)

    for r_start, r_end in ranges:
        chunk_lines = []
        for line in data_lines:
            cols = line.split("\t")
            if len(cols) < 2:
                continue
            ref = cols[1].strip()
            if ":intro" in ref or ref == "intro":
                continue  # handled separately
            v = parse_verse_num(ref)
            if v is not None and r_start <= v <= r_end:
                chunk_lines.append(line)

        if not chunk_lines and not (r_start == ranges[0][0] and intro_lines):
            continue  # skip empty chunks

        out_name = f"{base_name}-v{r_start}-{r_end}.tsv"
        out_path = os.path.join(output_dir, out_name)

        with open(out_path, "w", encoding="utf-8") as f:
            if header_line:
                f.write(header_line + "\n")
            # Intro rows go in the first chunk only
            if r_start == ranges[0][0]:
                for intro in intro_lines:
                    f.write(intro + "\n")
            for line in chunk_lines:
                f.write(line + "\n")

        row_count = len(chunk_lines) + (len(intro_lines) if r_start == ranges[0][0] else 0)
        print(f"{out_path}  ({row_count} rows, v{r_start}-{r_end})", file=sys.stderr)
        output_files.append(out_path)

    # Print output file paths to stdout (one per line) for script consumption
    for f in output_files:
        print(os.path.abspath(f))

    print(f"\nSplit into {len(output_files)} chunks", file=sys.stderr)

if __name__ == "__main__":
    main()
