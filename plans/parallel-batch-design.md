# Parallel Batch Orchestrator Design

Date: 2026-02-12

## Problem

Large chapters (PSA 119 at 450 issues, future large chapters) exceed what a
single tn-writer context window can handle well. We need a way to split the
work across parallel subagents and merge the results.

## Solution

A lightweight, reusable skill (`/parallel-batch`) that splits a TSV by verse
ranges, fans out to N parallel Task subagents each running a target skill,
and merges output TSVs.

## Approach: Option 3 (Lightweight Orchestrator)

Not a mode inside tn-writer. Not a full separate skill with heavy logic.
Just "split, fan out, merge" with two small scripts and a skill markdown.

## Inputs

```
/parallel-batch <skill> <book> <chapter> [--chunks N] [--extra-args "..."]
```

| Param | Example | Description |
|-------|---------|-------------|
| skill | tn-writer | Skill each subagent invokes |
| book | PSA | 3-letter book code |
| chapter | 119 | Chapter number |
| --chunks N | 4 | Number of parallel batches (default: auto) |
| --extra-args | "..." | Pass-through args for target skill |

## Three Phases

### Phase 1: Split (`split_tsv.py`)

Read the issue TSV from `output/issues/<BOOK>/<BOOK>-<CH>.tsv`. Group rows by
verse reference. Divide into N chunks by verse range, never splitting a verse
across chunks.

**Chunk boundary rules (priority order):**

1. **Stanza boundaries** -- For books/chapters with known stanza structure
   (PSA 119: every 8 verses = one Hebrew alphabet letter), always split on
   stanza boundaries. The script has a small lookup table of known stanza
   patterns:
   - PSA 119: 8-verse stanzas (Aleph 1-8, Beth 9-16, Gimel 17-24, ...)
   - Future entries can be added as needed

2. **Paragraph/section boundaries** -- When no stanza structure applies, prefer
   splitting at natural section breaks if detectable from verse numbering
   patterns.

3. **Even distribution** -- Fallback: divide total verses evenly across N
   chunks, keeping all rows for a given verse together.

Auto chunk count when `--chunks` is not specified:
- `ceil(total_rows / 50)`, minimum 2, maximum 6
- For PSA 119 (450 rows, 22 stanzas of 8 verses): 4 chunks of ~5-6 stanzas
  each, splitting on stanza boundaries (e.g., 1-48, 49-96, 97-144, 145-176)

Output: `tmp/parallel-batch/<BOOK>-<CH>-chunk-<N>.tsv` for each chunk.

### Phase 2: Fan Out (orchestrator launches Task subagents)

For each chunk, the orchestrator launches a Task subagent with a prompt like:

```
Invoke /tn-writer for <BOOK> chapter <CH>.
Issue TSV: tmp/parallel-batch/<BOOK>-<CH>-chunk-2.tsv
ULT USFM: /tmp/claude/ult_plain.usfm
UST USFM: /tmp/claude/ust_plain.usfm
Aligned USFM: output/AI-ULT/<BOOK>-<CH>-aligned.usfm
Output TSV: tmp/parallel-batch/out/<BOOK>-<CH>-chunk-2.tsv
Use /tmp/claude/batch-2/ for all intermediate files
  (prepared_notes.json, alignment_data.json, generated_notes.json).
```

Key points:
- Each subagent gets its own tmp directory so intermediate files don't collide
- USFM source files are read-only, safe to share across subagents
- All subagents launched as concurrent Task tool calls (parallel execution)
- Each subagent is type `general-purpose` so it has full tool access

### Phase 3: Merge (`merge_tsvs.py`)

Read all chunk output TSVs from `tmp/parallel-batch/out/`. Merge:
- Strip duplicate header rows (keep one)
- Sort by verse reference (same ref_sort_key as assemble_notes.py)
- Within a verse: sort by position in ULT (first-to-last), then longest-first
- Deduplicate: same Reference + same SupportReference + same Quote = keep one
- Write to `output/notes/<BOOK>-<CH>.tsv`

## Files Created

| File | Type | Lines (est) |
|------|------|-------------|
| `.claude/skills/parallel-batch/SKILL.md` | Skill | ~80 |
| `.claude/skills/parallel-batch/scripts/split_tsv.py` | Script | ~80 |
| `.claude/skills/parallel-batch/scripts/merge_tsvs.py` | Script | ~60 |

## Reusability

The split/merge scripts are TSV-generic. The skill takes `<skill>` as a
parameter. Any skill that reads an issue TSV (with a Reference column
containing chapter:verse values) and produces an output TSV can be batched.

The stanza lookup table in `split_tsv.py` is a simple dict -- adding new
entries for future structured chapters is one line each.

## What This Does NOT Change

- The tn-writer skill itself is untouched
- The makeBP orchestrator is untouched
- No existing scripts are modified
