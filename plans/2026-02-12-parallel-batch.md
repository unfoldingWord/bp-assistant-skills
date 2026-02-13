# Parallel Batch Orchestrator Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build a reusable `/parallel-batch` skill that splits large issue TSVs by verse range, fans out to parallel Task subagents running a target skill, and merges output TSVs.

**Architecture:** Two small Python scripts (split + merge) plus a skill markdown describing the three-phase orchestration flow. The skill is generic -- parameterized by target skill name -- so it works for any TSV-in/TSV-out skill.

**Tech Stack:** Python 3 scripts, Claude Code skill markdown, Task subagents

---

### Task 1: Create `split_tsv.py`

**Files:**
- Create: `.claude/skills/parallel-batch/scripts/split_tsv.py`

**Step 1: Write the split script**

```python
#!/usr/bin/env python3
"""
Split an issue TSV into verse-range chunks for parallel processing.

Reads an issue TSV, groups rows by verse, and splits into N chunk files.
Respects stanza boundaries for known acrostic/structured chapters.

Usage:
    python3 split_tsv.py output/issues/PSA/PSA-119.tsv \
        --chunks 4 \
        --output-dir tmp/parallel-batch/
"""

import argparse
import math
import os
import sys

# Known stanza structures: (book, chapter) -> verse group size
# PSA 119: 22 Hebrew-alphabet stanzas, each 8 verses
STANZA_MAP = {
    ('PSA', '119'): 8,
}


def parse_verse_num(ref):
    """Extract verse number from a reference like '119:5' or '119:front'."""
    parts = ref.split(':')
    if len(parts) < 2:
        return -1
    v = parts[-1]
    if v == 'front' or v == 'intro':
        return -1
    try:
        return int(v)
    except ValueError:
        return -1


def detect_book_chapter(filepath, rows):
    """Detect book and chapter from file content or filename."""
    # Try from first data row
    for row in rows:
        cols = row.split('\t')
        if cols and len(cols) >= 2:
            book = cols[0].strip().upper()
            ref = cols[1].strip()
            if ':' in ref and book and book != 'BOOK':
                ch = ref.split(':')[0]
                return book, ch
    # Fallback: filename like PSA-119.tsv or PSA-119-v1-40.tsv
    basename = os.path.basename(filepath).replace('.tsv', '')
    parts = basename.split('-')
    if len(parts) >= 2 and len(parts[0]) == 3:
        return parts[0].upper(), parts[1]
    return None, None


def read_tsv(filepath):
    """Read TSV, returning header line (if present) and data lines."""
    with open(filepath, 'r', encoding='utf-8') as f:
        lines = [l.rstrip('\n') for l in f if l.strip()]

    header = None
    data = lines
    if lines:
        first_cols = lines[0].split('\t')
        if first_cols[0].lower() in ('book', 'reference'):
            header = lines[0]
            data = lines[1:]

    return header, data


def group_by_verse(rows):
    """Group rows by verse number. Returns dict: verse_num -> [rows].

    Rows with 'front' or 'intro' references get verse_num = -1.
    """
    groups = {}
    for row in rows:
        cols = row.split('\t')
        ref = cols[1].strip() if len(cols) >= 2 else ''
        v = parse_verse_num(ref)
        groups.setdefault(v, []).append(row)
    return groups


def compute_stanza_boundaries(total_verses, stanza_size, num_chunks):
    """Compute chunk boundaries aligned to stanza breaks.

    Returns list of (start_verse, end_verse) tuples.
    """
    num_stanzas = math.ceil(total_verses / stanza_size)
    stanzas_per_chunk = max(1, round(num_stanzas / num_chunks))

    boundaries = []
    start = 1
    for i in range(num_chunks):
        if i == num_chunks - 1:
            # Last chunk gets everything remaining
            end = total_verses
        else:
            stanza_end = (i + 1) * stanzas_per_chunk
            end = min(stanza_end * stanza_size, total_verses)
        if start <= total_verses:
            boundaries.append((start, end))
        start = end + 1

    return boundaries


def compute_even_boundaries(verse_nums, num_chunks):
    """Compute evenly distributed chunk boundaries.

    Returns list of (start_verse, end_verse) tuples.
    """
    if not verse_nums:
        return []
    sorted_verses = sorted(verse_nums)
    per_chunk = max(1, math.ceil(len(sorted_verses) / num_chunks))

    boundaries = []
    for i in range(0, len(sorted_verses), per_chunk):
        chunk_verses = sorted_verses[i:i + per_chunk]
        boundaries.append((chunk_verses[0], chunk_verses[-1]))

    return boundaries


def main():
    parser = argparse.ArgumentParser(description='Split issue TSV into verse-range chunks')
    parser.add_argument('input_tsv', help='Path to issue TSV')
    parser.add_argument('--chunks', type=int, default=0,
                        help='Number of chunks (0 = auto based on row count)')
    parser.add_argument('--output-dir', default='tmp/parallel-batch/',
                        help='Output directory for chunk files')
    args = parser.parse_args()

    header, data = read_tsv(args.input_tsv)
    if not data:
        print("No data rows found.", file=sys.stderr)
        sys.exit(1)

    book, chapter = detect_book_chapter(args.input_tsv, data)

    # Auto-calculate chunk count
    num_chunks = args.chunks
    if num_chunks <= 0:
        num_chunks = max(2, min(6, math.ceil(len(data) / 50)))

    verse_groups = group_by_verse(data)

    # Separate front/intro rows (verse_num = -1)
    front_rows = verse_groups.pop(-1, [])
    verse_nums = sorted(verse_groups.keys())

    if not verse_nums:
        print("No verse-numbered rows found.", file=sys.stderr)
        sys.exit(1)

    # Compute boundaries
    stanza_size = STANZA_MAP.get((book, chapter))
    if stanza_size:
        max_verse = max(verse_nums)
        boundaries = compute_stanza_boundaries(max_verse, stanza_size, num_chunks)
    else:
        boundaries = compute_even_boundaries(verse_nums, num_chunks)

    # Assign rows to chunks
    os.makedirs(args.output_dir, exist_ok=True)
    chunk_files = []

    for i, (start, end) in enumerate(boundaries):
        chunk_rows = []
        # Front rows go in first chunk only
        if i == 0:
            chunk_rows.extend(front_rows)
        for v in verse_nums:
            if start <= v <= end:
                chunk_rows.extend(verse_groups[v])

        if not chunk_rows:
            continue

        ch_padded = chapter.zfill(3) if book == 'PSA' else chapter.zfill(2)
        filename = f"{book}-{ch_padded}-chunk-{i + 1}.tsv"
        filepath = os.path.join(args.output_dir, filename)

        with open(filepath, 'w', encoding='utf-8') as f:
            if header:
                f.write(header + '\n')
            for row in chunk_rows:
                f.write(row + '\n')

        chunk_files.append(filepath)
        print(f"Chunk {i + 1}: verses {start}-{end}, {len(chunk_rows)} rows -> {filepath}")

    print(f"\n{len(chunk_files)} chunks written to {args.output_dir}")
    # Print chunk file paths for orchestrator to parse
    print("CHUNK_FILES=" + ','.join(chunk_files))


if __name__ == '__main__':
    main()
```

**Step 2: Test the split script manually**

Run against PSA-119 combined TSV:
```bash
python3 .claude/skills/parallel-batch/scripts/split_tsv.py \
    output/issues/PSA/PSA-119.tsv \
    --chunks 4 \
    --output-dir tmp/parallel-batch/
```

Expected: 4 chunk files with rows split on 8-verse stanza boundaries.
Verify with: `wc -l tmp/parallel-batch/PSA-119-chunk-*.tsv`
Total lines across chunks should equal line count of input.

**Step 3: Commit**

```bash
git add .claude/skills/parallel-batch/scripts/split_tsv.py
git commit -m "feat: add split_tsv.py for parallel batch orchestration"
```

---

### Task 2: Create `merge_tsvs.py`

**Files:**
- Create: `.claude/skills/parallel-batch/scripts/merge_tsvs.py`

**Step 1: Write the merge script**

```python
#!/usr/bin/env python3
"""
Merge multiple TN output TSVs into a single sorted, deduplicated TSV.

Reads chunk output TSVs, strips duplicate headers, sorts by verse reference,
deduplicates rows with identical Reference + SupportReference + Quote, and
writes the merged result.

Usage:
    python3 merge_tsvs.py tmp/parallel-batch/out/PSA-119-chunk-*.tsv \
        --output output/notes/PSA-119.tsv
"""

import argparse
import os
import re
import sys


def ref_sort_key(ref):
    """Sort references: 'intro' first, 'front' second, then numerically."""
    parts = ref.split(':')
    if len(parts) == 2:
        try:
            ch = int(parts[0])
        except ValueError:
            ch = 9999
        v = parts[1]
        if v == 'intro':
            return (ch, -2)
        elif v == 'front':
            return (ch, -1)
        else:
            try:
                return (ch, int(v))
            except ValueError:
                return (ch, 9999)
    return (9999, 9999)


def main():
    parser = argparse.ArgumentParser(description='Merge chunk output TSVs')
    parser.add_argument('input_tsvs', nargs='+', help='Chunk TSV files to merge')
    parser.add_argument('--output', '-o', required=True, help='Output merged TSV path')
    args = parser.parse_args()

    header = None
    rows = []

    for filepath in sorted(args.input_tsvs):
        if not os.path.exists(filepath):
            print(f"WARNING: {filepath} not found, skipping", file=sys.stderr)
            continue

        with open(filepath, 'r', encoding='utf-8') as f:
            for i, line in enumerate(f):
                line = line.rstrip('\n')
                if not line.strip():
                    continue
                cols = line.split('\t')

                # Detect and skip header rows (keep first one seen)
                if cols[0].lower() == 'reference' and i == 0:
                    if header is None:
                        header = line
                    continue

                rows.append(line)

    # Sort by reference
    def row_sort_key(line):
        cols = line.split('\t')
        ref = cols[0] if cols else ''
        return ref_sort_key(ref)

    rows.sort(key=row_sort_key)

    # Deduplicate: same Reference + SupportReference + Quote
    seen = set()
    deduped = []
    dup_count = 0
    for row in rows:
        cols = row.split('\t')
        if len(cols) >= 5:
            key = (cols[0], cols[3], cols[4])  # Reference, SupportReference, Quote
        else:
            key = tuple(cols)
        if key in seen:
            dup_count += 1
            continue
        seen.add(key)
        deduped.append(row)

    # Write output
    os.makedirs(os.path.dirname(os.path.abspath(args.output)), exist_ok=True)
    with open(args.output, 'w', encoding='utf-8') as f:
        if header:
            f.write(header + '\n')
        for row in deduped:
            f.write(row + '\n')

    print(f"Merged {len(deduped)} rows from {len(args.input_tsvs)} files -> {args.output}")
    if dup_count:
        print(f"  ({dup_count} duplicates removed)")


if __name__ == '__main__':
    main()
```

**Step 2: Test merge with existing chunk outputs (if available) or create small test files**

```bash
# Quick smoke test with two tiny TSVs
mkdir -p tmp/parallel-batch/test/
echo -e "Reference\tID\tTags\tSupportReference\tQuote\tOccurrence\tNote\n119:1\tab12\t\trc://*/ta/man/translate/figs-abstractnouns\tHebrew\t1\tTest note" > tmp/parallel-batch/test/c1.tsv
echo -e "Reference\tID\tTags\tSupportReference\tQuote\tOccurrence\tNote\n119:9\tcd34\t\trc://*/ta/man/translate/figs-metaphor\tHebrew2\t1\tTest note 2" > tmp/parallel-batch/test/c2.tsv

python3 .claude/skills/parallel-batch/scripts/merge_tsvs.py \
    tmp/parallel-batch/test/c1.tsv tmp/parallel-batch/test/c2.tsv \
    --output tmp/parallel-batch/test/merged.tsv

cat tmp/parallel-batch/test/merged.tsv
```

Expected: 1 header + 2 rows, sorted by verse reference.

**Step 3: Commit**

```bash
git add .claude/skills/parallel-batch/scripts/merge_tsvs.py
git commit -m "feat: add merge_tsvs.py for parallel batch orchestration"
```

---

### Task 3: Create `SKILL.md`

**Files:**
- Create: `.claude/skills/parallel-batch/SKILL.md`

**Step 1: Write the skill markdown**

The SKILL.md describes the three-phase orchestration flow. It tells the
agent how to split, construct subagent prompts, launch them in parallel,
and merge. The actual logic is in the scripts; the skill just wires them
together.

Key points for the SKILL.md content:
- Arguments: `<skill> <book> <chapter> [--chunks N] [--extra-args "..."]`
- Phase 1: run `split_tsv.py` with the issue TSV, capture CHUNK_FILES output
- Phase 2: for each chunk file, launch a Task subagent (type: general-purpose)
  that invokes the target skill. Each gets isolated tmp dir `/tmp/claude/batch-<N>/`.
  Shared read-only files (ULT, UST, aligned USFM) are passed through.
  Output TSV goes to `tmp/parallel-batch/out/<chunk-filename>`.
  Launch ALL subagents in a single message (parallel execution).
- Phase 3: run `merge_tsvs.py` on all output TSVs -> `output/notes/<BOOK>-<CH>.tsv`
- Post-processing: run `curly_quotes.py` on the merged output
- Note: the tn-writer subagent prompt should tell the subagent to use `/tn-writer`
  skill, passing the chunk TSV as input and the isolated tmp dir for intermediates.
  The subagent prompt must also tell it the output TSV path.

**Step 2: Commit**

```bash
git add .claude/skills/parallel-batch/SKILL.md
git commit -m "feat: add parallel-batch skill for reusable parallel orchestration"
```

---

### Task 4: Verify End-to-End with PSA 119 (dry run)

**Step 1: Run split on PSA-119**

```bash
python3 .claude/skills/parallel-batch/scripts/split_tsv.py \
    output/issues/PSA/PSA-119.tsv \
    --chunks 4 \
    --output-dir tmp/parallel-batch/
```

Verify: 4 chunks, stanza-aligned boundaries, row counts sum to original.

**Step 2: Verify chunk boundaries are on alphabet changes**

PSA 119 stanzas: Aleph 1-8, Beth 9-16, ... Tav 169-176.
With 4 chunks of ~5-6 stanzas each, expected boundaries should be
multiples of 8 (e.g., 1-48, 49-96, 97-144, 145-176 or similar).

```bash
# Check first and last verse in each chunk
for f in tmp/parallel-batch/PSA-119-chunk-*.tsv; do
    echo "=== $f ==="
    # Skip header, get first and last reference
    tail -n +2 "$f" | head -1 | cut -f2
    tail -n +2 "$f" | tail -1 | cut -f2
done
```

**Step 3: Commit all**

If any fixes were needed, commit them.
