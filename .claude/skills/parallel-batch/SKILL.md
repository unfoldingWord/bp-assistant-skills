---
name: parallel-batch
description: Split a long chapter's issue TSV into chunks and process them in parallel for note generation. Use when writing notes for long chapters (50+ issues) like PSA 119.
---

# Parallel Batch Note Writer

Split a chapter's issue TSV into verse-range chunks, run `/tn-writer` on each chunk in parallel via Task subagents, then merge the output notes TSVs into a single file.

## Model

This orchestrator only splits and merges -- run it as **haiku**. Each tn-writer chunk requires deep reasoning -- spawn with `model: "opus"`.

## When to Use

- Long chapters where running tn-writer on the full issue TSV would exceed context or take too long
- PSA 119 (176 verses, 22 stanzas) is the primary use case
- Any chapter with more than ~50 issues benefits from parallelization

## Inputs

- **Book**: 3-letter abbreviation (e.g., PSA)
- **Chapter**: number (e.g., 119)
- **Chunk size**: `--chunk-size N` (optional, default 40 verses per chunk)
- **Explicit ranges**: `--ranges 1-24,25-48,...` (optional, overrides auto-chunking)

## Workflow

### Step 1: Split the Issue TSV

Use `mcp__workspace-tools__split_tsv` with `inputTsv="output/issues/<BOOK>/<BOOK>-<CH>.tsv"`, `chunkSize=24`.

The tool:
- Auto-detects stanza boundaries for known chapters (PSA 119 -> 8-verse stanzas)
- Groups stanzas into chunks of roughly `chunkSize` verses
- Writes chunk files to the same directory: `<BOOK>-<CH>-v<START>-<END>.tsv`
- Returns the output file paths (one per line)
- Each chunk file includes the header row and intro rows (first chunk only)

For PSA 119 with `--chunk-size 24`, you get chunks like: v1-24, v25-48, v49-72, v73-96, v97-120, v121-144, v145-176 (three stanzas per chunk).

### Step 2: Run tn-writer in Parallel

For each chunk file from Step 1, launch a Task subagent:

```
Task: "Write notes for <BOOK> <CH>:<START>-<END>"
Prompt: "/tn-writer <BOOK> <CH>:<START>-<END> --issues output/issues/<BOOK>/<BOOK>-<CH>-v<START>-<END>.tsv"
subagent_type: "general-purpose"
model: "opus"
```

Launch all subagents in parallel (multiple Task calls in a single message). Each subagent:
- Runs the tn-writer skill against its chunk's issue TSV
- Produces output at `output/notes/<BOOK>/<BOOK>-<CH>-v<START>-<END>.tsv`

Wait for all subagents to complete before proceeding.

### Step 3: Merge Output Notes

Use `mcp__workspace-tools__merge_tsvs` with `glob="output/notes/<BOOK>/<BOOK>-<CH>-v*.tsv"`, `output="output/notes/<BOOK>/<BOOK>-<CH>.tsv"`.

The merge tool:
- Deduplicates headers (keeps first)
- Sorts by verse number (intro first, then ascending)
- Removes duplicate rows (same Reference + SupportReference + Quote)
- Writes the final merged file

### Step 4: Verify

After merging, do a quick sanity check:
```bash
wc -l output/notes/<BOOK>/<BOOK>-<CH>.tsv
head -5 output/notes/<BOOK>/<BOOK>-<CH>.tsv
```

Verify the intro row is present, notes start at verse 1, and the file looks complete.

## Output

- Chunk files: `output/issues/<BOOK>/<BOOK>-<CH>-v<START>-<END>.tsv` (input splits)
- Chunk notes: `output/notes/<BOOK>/<BOOK>-<CH>-v<START>-<END>.tsv` (per-chunk output)
- Final merged: `output/notes/<BOOK>/<BOOK>-<CH>.tsv`

## Stanza Table

The split script has a built-in stanza table for chapters with structured verse groupings:

| Book | Chapter | Structure |
|------|---------|-----------|
| PSA  | 119     | 22 stanzas of 8 verses, each tied to a Hebrew alphabet letter |

To add more entries, edit the `STANZA_TABLE` dict in `split_tsv.py`.

## Example: PSA 119

```
# Split into ~24-verse chunks (3 stanzas each)
mcp__workspace-tools__split_tsv(inputTsv="output/issues/PSA/PSA-119.tsv", chunkSize=24)

# Outputs:
#   output/issues/PSA/PSA-119-v1-24.tsv
#   output/issues/PSA/PSA-119-v25-48.tsv
#   output/issues/PSA/PSA-119-v49-72.tsv
#   output/issues/PSA/PSA-119-v73-96.tsv
#   output/issues/PSA/PSA-119-v97-120.tsv
#   output/issues/PSA/PSA-119-v121-144.tsv
#   output/issues/PSA/PSA-119-v145-176.tsv

# Launch 7 parallel tn-writer subagents (one per chunk)
# After all complete, merge:
mcp__workspace-tools__merge_tsvs(glob="output/notes/PSA/PSA-119-v*.tsv", output="output/notes/PSA/PSA-119.tsv")
```
