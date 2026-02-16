#!/usr/bin/env python3
"""
Merge multiple output notes TSVs into a single file.

Handles:
  - Header deduplication (keeps first header, strips from subsequent files)
  - Verse sorting (intro first, then by verse number)
  - Row deduplication (same Reference + SupportReference/Tags = duplicate)

Notes TSV format (7 columns):
  Reference  ID  Tags  SupportReference  Quote  Occurrence  Note

Usage:
    python3 merge_tsvs.py output/notes/PSA/PSA-119-v1-8.tsv output/notes/PSA/PSA-119-v9-16.tsv ... -o output/notes/PSA/PSA-119.tsv
    python3 merge_tsvs.py --glob "output/notes/PSA/PSA-119-v*.tsv" -o output/notes/PSA/PSA-119.tsv
"""

import argparse
import glob
import os
import re
import sys

def parse_ref_sort_key(ref):
    """Sort key for Reference column: intro=0, then verse number."""
    if "intro" in ref:
        return (0, 0)
    m = re.search(r"(\d+)$", ref.split(":")[1] if ":" in ref else ref)
    if m:
        return (1, int(m.group(1)))
    return (1, 99999)

def is_header(line):
    """Check if a line is the notes TSV header."""
    cols = line.split("\t")
    if cols and cols[0].strip().lower() == "reference":
        return True
    return False

def dedup_key(line):
    """Generate a dedup key from Reference + SupportReference (or Tags)."""
    cols = line.split("\t")
    if len(cols) < 4:
        return line
    ref = cols[0].strip()
    # Use SupportReference (col 3) as secondary key; fall back to Tags (col 2)
    sref = cols[3].strip() if cols[3].strip() else cols[2].strip()
    # Also include Quote (col 4) to distinguish different phrases in same verse
    quote = cols[4].strip() if len(cols) > 4 else ""
    return f"{ref}|{sref}|{quote}"

def main():
    parser = argparse.ArgumentParser(description="Merge output notes TSVs")
    parser.add_argument("files", nargs="*", help="Input TSV files to merge")
    parser.add_argument("--glob", type=str, default=None,
                        help="Glob pattern for input files (e.g., 'output/notes/PSA/PSA-119-v*.tsv')")
    parser.add_argument("-o", "--output", required=True, help="Output file path")
    parser.add_argument("--no-sort", action="store_true",
                        help="Do not re-sort by verse (preserve chunk order)")

    args = parser.parse_args()

    input_files = list(args.files) if args.files else []
    if args.glob:
        input_files.extend(sorted(glob.glob(args.glob)))

    if not input_files:
        print("ERROR: No input files specified", file=sys.stderr)
        sys.exit(1)

    # Remove the output file from inputs if it exists there (avoids circular merge)
    abs_output = os.path.abspath(args.output)
    input_files = [f for f in input_files if os.path.abspath(f) != abs_output]

    header = None
    data_lines = []

    for filepath in input_files:
        if not os.path.exists(filepath):
            print(f"WARNING: File not found, skipping: {filepath}", file=sys.stderr)
            continue

        with open(filepath, "r", encoding="utf-8") as f:
            for line in f:
                line = line.rstrip("\n")
                if not line.strip():
                    continue
                if is_header(line):
                    if header is None:
                        header = line
                    continue  # skip duplicate headers
                data_lines.append(line)

    # Deduplicate
    seen = set()
    unique_lines = []
    dupes = 0
    for line in data_lines:
        key = dedup_key(line)
        if key in seen:
            dupes += 1
            continue
        seen.add(key)
        unique_lines.append(line)

    if dupes:
        print(f"Removed {dupes} duplicate rows", file=sys.stderr)

    # Sort by verse
    if not args.no_sort:
        unique_lines.sort(key=lambda line: parse_ref_sort_key(line.split("\t")[0].strip()))

    # Write output
    os.makedirs(os.path.dirname(args.output) or ".", exist_ok=True)
    with open(args.output, "w", encoding="utf-8") as f:
        if header:
            f.write(header + "\n")
        for line in unique_lines:
            f.write(line + "\n")

    total = len(unique_lines)
    print(f"Merged {len(input_files)} files -> {args.output} ({total} rows)", file=sys.stderr)
    print(os.path.abspath(args.output))

if __name__ == "__main__":
    main()
