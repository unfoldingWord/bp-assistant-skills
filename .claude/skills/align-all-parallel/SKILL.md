---
name: align-all-parallel

description: Run ULT-alignment and UST-alignment in parallel for a single chapter. Use when asked to align both ULT and UST or run all alignments for a chapter.

allowed-tools: Task, Read, mcp__workspace-tools__read_usfm_chapter
---

## Quick Alignment Pipeline

Spawn alignment agents in parallel and wait for them to complete.

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

This skill is coordination only — run it as **haiku**. The alignment subagents require linguistic judgment — spawn each with `model: "sonnet"`.

## Step 1: Check Verse Count

Before spawning agents, count the verses in the chapter using `mcp__workspace-tools__read_usfm_chapter` on `data/hebrew_bible/XX-BOOK.usfm`. Count the number of `\v` markers in the result.

- If verse count **≤ 18**: proceed to Step 2a (single batch)
- If verse count **> 18**: proceed to Step 2b (split into two batches)

Use `floor(N/2)` as the split point. For example, 22 verses → batch 1 is v1–v11, batch 2 is v12–v22.

## Step 2a: Single Batch (≤ 18 verses)

Spawn agents in parallel:

- If running ULT: spawn `ult-align` subagent (`model: "sonnet"`, skill: ULT-alignment)
- If running UST: spawn `ust-align` subagent (`model: "sonnet"`, skill: UST-alignment)

Wait for both to complete. Report results.

## Step 2b: Split Batch (> 18 verses)

Run in two rounds:

**Round 1** — spawn in parallel:
- If running ULT: `ult-align-1` subagent for `BOOK CH --verses 1-HALF`
- If running UST: `ust-align-1` subagent for `BOOK CH --verses 1-HALF`

Wait for round 1 to complete.

**Round 2** — spawn in parallel:
- If running ULT: `ult-align-2` subagent for `BOOK CH --verses HALF+1-N`
- If running UST: `ust-align-2` subagent for `BOOK CH --verses HALF+1-N`

Wait for round 2 to complete.

**Merge** — assemble the full chapter file for each translation type:
- ULT: read `BOOK-CH-v1-vHALF-aligned.usfm` and `BOOK-CH-vHALF+1-vN-aligned.usfm`, write `BOOK-CH-aligned.usfm`
  - Keep the full header (`\id`, `\usfm`, `\ide`, `\h`, `\mt`, `\c`) from part 1
  - Append only the verse lines (lines starting with `\v`, `\q`, `\zaln`, `\w`, etc.) from part 2
- UST: same

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
