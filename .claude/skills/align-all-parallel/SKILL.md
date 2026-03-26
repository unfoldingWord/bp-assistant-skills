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
- If verse count **> 18**: proceed to Step 2b (split into batches of 18)

## Step 2a: Single Batch (≤ 18 verses)

Spawn agents in parallel:

- If running ULT: spawn `ult-align` subagent (`model: "sonnet"`, skill: ULT-alignment)
- If running UST: spawn `ust-align` subagent (`model: "sonnet"`, skill: UST-alignment)

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

Launch all batch subagents in a **single message** — do not wait between batches:

- For each batch K (1..numBatches):
  - If running ULT: spawn `ult-align-K` subagent (`model: "sonnet"`, skill: ULT-alignment) for `BOOK CH --verses START-END`
  - If running UST: spawn `ust-align-K` subagent (`model: "sonnet"`, skill: UST-alignment) for `BOOK CH --verses START-END`
- All subagents launch at once (e.g., 4 batches × 2 types = 8 parallel subagents)

**Parallel cap:** If the chapter has more than 5 batches per type (>90 verses), split into waves of 5 batches each. Run wave 1 (batches 1–5), wait for completion, then run wave 2 (batches 6–N). This keeps total parallel agents manageable.

Wait for all subagents to complete before proceeding.

## Step 2d: Consistency Check

After all alignment batches complete, spawn a consistency checker to catch cross-batch inconsistencies. The same Hebrew word (same Strong's number) should get the same English alignment across the chapter.

For each type being aligned (ULT and/or UST), spawn a Task subagent (`model: "sonnet"`):

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

## Step 2e: Merge

After consistency check completes, use `mcp__workspace-tools__merge_aligned_usfm` to assemble the full chapter:
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
