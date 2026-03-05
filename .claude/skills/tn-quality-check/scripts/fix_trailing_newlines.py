#!/usr/bin/env python3
"""Strip trailing literal \\n from Note column in TN TSV files.

Usage: python3 fix_trailing_newlines.py <file.tsv>

Rewrites the file in-place. Prints count of fixed rows.
"""

import csv
import sys
from pathlib import Path

def main():
    if len(sys.argv) != 2:
        print("Usage: fix_trailing_newlines.py <file.tsv>", file=sys.stderr)
        sys.exit(2)

    path = Path(sys.argv[1])
    if not path.exists():
        print(f"File not found: {path}", file=sys.stderr)
        sys.exit(1)

    text = path.read_text(encoding="utf-8")
    rows = list(csv.reader(text.splitlines(), delimiter="\t"))

    if not rows:
        return

    header = rows[0]
    try:
        note_idx = header.index("Note")
    except ValueError:
        print("No Note column found", file=sys.stderr)
        sys.exit(1)

    fixed = 0
    for row in rows[1:]:
        if note_idx < len(row) and row[note_idx].endswith("\\n"):
            row[note_idx] = row[note_idx][:-2].rstrip()
            fixed += 1

    if fixed:
        lines = []
        for row in rows:
            lines.append("\t".join(row))
        path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(f"Fixed {fixed} trailing \\n" + (f" in {path.name}" if fixed else ""))

if __name__ == "__main__":
    main()
