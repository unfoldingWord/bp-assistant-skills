---
name: align-all-parallel

description: Run ULT-alignment and UST-alignment in parallel for a single chapter. Use when asked to align both ULT and UST or run all alignments for a chapter.

allowed-tools: Task, Read, mcp__workspace-tools__read_usfm_chapter, mcp__workspace-tools__merge_aligned_usfm
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

Divide the chapter into batches of up to 18 verses each:
- Batch size = 18
- Number of batches = ceil(N / 18)
- Batch 1: verses 1–18, Batch 2: verses 19–36, etc.
- Last batch may be shorter

Run batches **sequentially** (one round at a time). Each round spawns ULT and/or UST sub-agents **in parallel**:

**Round K** (for each batch K = 1..numBatches):
- If running ULT: spawn `ult-align-K` subagent for `BOOK CH --verses START-END`
- If running UST: spawn `ust-align-K` subagent for `BOOK CH --verses START-END`
- Wait for round K to complete before starting round K+1

**Merge** — after all rounds complete, use `mcp__workspace-tools__merge_aligned_usfm` to assemble the full chapter:
- ULT (if applicable): call with `parts` = ordered array of all ULT partial files, `output` = `output/AI-ULT/BOOK/BOOK-CH-aligned.usfm`
- UST (if applicable): call with `parts` = ordered array of all UST partial files, `output` = `output/AI-UST/BOOK/BOOK-CH-aligned.usfm`

Do NOT use Bash, sub-agents, or manual Read+Write for the merge — use the MCP tool.

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
