---
name: align-all-parallel

description: Run ULT-alignment and UST-alignment in parallel for a single chapter. Use when asked to align both ULT and UST or run all alignments for a chapter.

allowed-tools: Task, Read, Bash(node /app/src/workspace-tools-cli.js:*), mcp__workspace-tools__read_usfm_chapter, mcp__workspace-tools__merge_aligned_usfm
---

## Quick Alignment Pipeline

Spawn alignment agents in parallel and wait for them to complete.

## Workspace Tools Execution

Run workspace tools via the blessed CLI wrapper:

    node /app/src/workspace-tools-cli.js <tool_name> '<json-args>'

stdout is the tool result (same output the MCP tool returns). If args contain
quotes, pass `-` as the second arg and pipe the JSON on stdin (heredoc).
Fallback (if Bash is unavailable): call `mcp__workspace-tools__<tool_name>` with
the same args.

- **Do NOT improvise your own alignment/merge scripts** (e.g. `generate_*.js`).
  Per-verse conversion happens inside the subagents via the `create_aligned_usfm`
  tool; the full-chapter assembly is done here via `merge_aligned_usfm` (Step 2f).
  Use only the CLI wrapper (or the MCP fallback) — never a hand-written script.
- If a batch subagent fails or a tool returns an error, **re-spawn that batch or
  report the failure plainly** — do not work around it with ad-hoc code.

## Pipeline Context

If `--context <path>` is provided, read the context.json file. It contains the authoritative source paths:
- `sources.ult` — the ULT to align (may be a freshly generated file, not Door43 master)
- `sources.ust` — the UST to align
- `sources.hebrew` — Hebrew source file

Pass the ULT and UST paths to the alignment subagents so they align the correct files. Include these in the subagent prompts, e.g.: `PSA 35 --ult output/AI-ULT/PSA/PSA-035.usfm`

## Input

- **Book**: 3-letter abbreviation (PSA, GEN, 2SA, etc.)
- **Chapter**: number
- **--ult** (optional): run ULT alignment only
- **--ust** (optional): run UST alignment only
- **--context** (optional): path to pipeline context.json

If neither `--ult` nor `--ust` is given, run both.

## Model

This skill is coordination only, but the merge is USFM-structure-sensitive — run it on **Opus** at **medium** effort. The alignment subagents require linguistic judgment — spawn each with `model: "opus"`, `effort: "medium"`.

## Step 1: Check Verse Count

Before spawning agents, count the verses in the chapter. Read the chapter with:

    node /app/src/workspace-tools-cli.js read_usfm_chapter '{"file":"data/hebrew_bible/XX-BOOK.usfm","chapter":CH}'

Count the number of `\v` markers in the result. (Fallback: `mcp__workspace-tools__read_usfm_chapter` with the same args.)

- If verse count **≤ 18**: proceed to Step 2a (single batch)
- If verse count **> 18**: proceed to Step 2b (split into batches of 18)

## Step 2a: Single Batch (≤ 18 verses)

Spawn agents in parallel:

- If running ULT: spawn `ult-align` subagent (`model: "opus"`, `effort: "medium"`, skill: ULT-alignment)
- If running UST: spawn `ust-align` subagent (`model: "opus"`, `effort: "medium"`, skill: UST-alignment)

Wait for both to complete. Report results.

## Step 2b: Split into Batches (> 18 verses)

Determine the number of batches, then split evenly:
- Number of batches = ceil(N / 18)
- Batch size = ceil(N / numBatches) — distributes verses evenly
- Batch 1: verses 1–batchSize, Batch 2: verses (batchSize+1)–(2×batchSize), etc.
- Last batch gets the remainder

Examples:
- 22 verses → 2 batches → 11 each (v1–11, v12–22)
- 56 verses → 4 batches → 14 each (v1–14, v15–28, v29–42, v43–56)
- 176 verses → 10 batches → 18 each (v1–18, v19–36, ... v163–176)

## Step 2c: Spawn ALL Batches in Parallel

**First, skip batches that are already done (resume support).** For each batch,
`Read` its expected partial output (`output/AI-{ULT,UST}/BOOK/BOOK-CH-vSTART-vEND-aligned.usfm`).
If the file already exists and contains every verse in that batch's range (each
`\v` present, with `\zaln-s` alignment markers), that batch is complete — do NOT
re-spawn it. Only spawn subagents for the batches still missing or incomplete.
This lets a resumed run finish a long chapter by filling just the remaining
batches instead of re-aligning everything (and timing out again).

Launch the still-needed batch subagents in a **single message** — do not wait between batches:

- For each batch K (1..numBatches) that is NOT already complete:
  - If running ULT: spawn `ult-align-K` subagent (`model: "opus"`, `effort: "medium"`, skill: ULT-alignment) for `BOOK CH --verses START-END`
  - If running UST: spawn `ust-align-K` subagent (`model: "opus"`, `effort: "medium"`, skill: UST-alignment) for `BOOK CH --verses START-END`
- All still-needed subagents launch at once (e.g., 4 batches × 2 types = 8 parallel subagents)

If every batch is already complete, skip straight to Step 2d/2e/2f (verify + consistency check + merge).

**Parallel cap:** If the chapter has more than 5 batches per type (>90 verses), split into waves of 5 batches each. Run wave 1 (batches 1–5), wait for completion, then run wave 2 (batches 6–N). This keeps total parallel agents manageable.

Wait for all subagents to complete before proceeding.

## Step 2d: Verify Batch Files Exist

**Before doing anything else after the subagents return, confirm every expected batch file was actually written.** Subagents can return a nominal completion signal without writing their output (internal failure, API throttle, turn-budget cutoff). If you skip this check, a merge over partial batches will silently succeed and the pipeline's freshness check will later flag a `missing_output` failure — see issue #114.

For each type being aligned (ULT and/or UST) and each batch K in `1..numBatches`:

1. `Read` the expected batch file `output/AI-{ULT,UST}/BOOK/BOOK-CH-vSTART-vEND-aligned.usfm`.
2. Treat the batch as **written** only if the file exists AND contains every verse in the batch range (each `\v N` present) AND has `\zaln-s` alignment markers.
3. A file that is stale from a prior run is **not** acceptable proof — if the Read succeeds but the content does not cover the current batch range, treat it as missing.

If any expected batch file is missing or incomplete:

- **Do NOT proceed to Step 2e or 2f.**
- If **≤2 batches** are missing (per type), re-spawn just those batch subagents (same prompts as Step 2c) and re-verify.
- If more than 2 batches are missing, or a targeted re-spawn still fails to produce the files, **report failure plainly**. List the missing files and return a non-success result so the pipeline can raise `missing_output` and resume from checkpoint. Do not merge partial output.

Only proceed once every expected batch file for every requested type is present and complete.

## Step 2e: Consistency Check

After all alignment batches complete, spawn a consistency checker to catch cross-batch inconsistencies. The same Hebrew word (same Strong's number) should get the same English alignment across the chapter.

For each type being aligned (ULT and/or UST), spawn a Task subagent (`model: "opus"`, `effort: "medium"`):

```
Task: "Check alignment consistency for BOOK CH (ULT|UST)"
```

The checker:
1. **Read** all partial aligned USFM files for that type
2. **Extract** every `x-strong` + `x-content` pairing and which English word(s) it maps to
3. **Identify inconsistencies** — same Strong's/content combo aligned to different English words across batches (e.g., H2617 x-content="חֶסֶד" → "faithfulness" in batch 1 but "loyalty" in batch 3)
4. **Fix** by choosing the most frequent alignment and updating the minority files using Edit
5. **Report** what was changed (or confirm no inconsistencies found)

If running both ULT and UST, spawn both checkers in parallel.

Note: The checker does NOT re-align from scratch — it only patches inconsistencies in the already-generated partial files. Skip this step for chapters with only 2 batches (≤36 verses), where inconsistency risk is low.

## Step 2f: Merge

After consistency check completes, assemble the full chapter with the `merge_aligned_usfm` tool via the CLI wrapper:

    node /app/src/workspace-tools-cli.js merge_aligned_usfm '{"parts":["output/AI-ULT/BOOK/BOOK-CH-vSTART-vEND-aligned.usfm", ...],"output":"output/AI-ULT/BOOK/BOOK-CH-aligned.usfm"}'

- ULT (if applicable): `parts` = ordered array of all ULT partial files, `output` = `output/AI-ULT/BOOK/BOOK-CH-aligned.usfm`
- UST (if applicable): `parts` = ordered array of all UST partial files, `output` = `output/AI-UST/BOOK/BOOK-CH-aligned.usfm`

Use the `merge_aligned_usfm` tool (CLI wrapper, or `mcp__workspace-tools__merge_aligned_usfm` as fallback) — do NOT assemble the chapter with a hand-written script or manual Read+Write.

## Output

- `output/AI-ULT/<BOOK>/<BOOK>-<CH>-aligned.usfm` - ULT with word-level alignments (if --ult or both)
- `output/AI-UST/<BOOK>/<BOOK>-<CH>-aligned.usfm` - UST with phrase-level alignments (if --ust or both)

Both are ready for insertion into Door43 repos.

## Usage

```
/align-all-parallel psa 124
/align-all-parallel lam 4 --ust
/align-all-parallel lam 3 --ult --ust
```
