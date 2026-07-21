---
name: align-all-parallel

description: Run ULT-alignment and UST-alignment in parallel for a single chapter. Use when asked to align both ULT and UST or run all alignments for a chapter.

allowed-tools: Task, Read, Bash(node /app/src/workspace-tools-cli.js:*), mcp__workspace-tools__read_usfm_chapter, mcp__workspace-tools__plan_alignment_batches, mcp__workspace-tools__merge_aligned_usfm
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

This skill runs headless — no user is present, and raw freeform shell (`ls`,
`mkdir`, `cat`, compound one-liners) is auto-denied. To check whether a file
exists, just try `Read` on it (a failed Read means it is absent). If any tool
call is denied, do not stop and wait: switch to the tool equivalent (`Read`, or
the CLI wrapper) and continue.

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

A single-batch agent aligns the whole chapter and writes the whole-chapter file
directly (`output/AI-{ULT,UST}/BOOK/BOOK-CH-aligned.usfm`), so there is no merge
step on this path.

Spawn agents in parallel (single message — do not wait between them):

- If running ULT: spawn `ult-align` subagent (`model: "opus"`, `effort: "medium"`) with the ULT-alignment prompt template above
- If running UST: spawn `ust-align` subagent (`model: "opus"`, `effort: "medium"`) with the UST-alignment prompt template above

Compose each subagent prompt from this template (here and in Step 2c) — the
Skill-file Read replaces any Skill tool invocation, which headless sub-agents
cannot use (the call is auto-denied and the denial locks the subagent out of
all further tools — bp-assistant#242):

    Read the file /data/workspace/.claude/skills/{ULT,UST}-alignment/SKILL.md
    and follow its process for BOOK CH --{ult,ust} <path>.
    Do NOT invoke the Skill tool. Headless run — use Read and the
    workspace-tools CLI wrapper (node /app/src/workspace-tools-cli.js), not raw
    shell, for any file checks; if a tool call is denied, switch to an allowed
    tool and continue — never stop to wait for a user.

Here in Step 2a the subagent aligns the whole chapter, so the command line has
no `--verses` (that is what makes the sub-skill write the whole-chapter
`BOOK-CH-aligned.usfm`). Batch subagents in Step 2c add `--verses START-END`
to the command line, which routes the sub-skill to the partial
`BOOK-CH-vSTART-vEND-aligned.usfm` output.

Wait for all spawned agents to complete, then go to Step 2a-verify.

## Step 2a-verify: Confirm full verse coverage before reporting success

**Do not report success until every chapter verse is aligned.** A subagent can
return a nominal completion signal without writing all its verses (internal
failure, API throttle, turn-budget cutoff). Skipping this check is the
single-batch analogue of issue #114 — the pipeline's coverage gate then flags
`incomplete_coverage`/`missing_output` and files a spurious issue for a gap an
in-skill re-run would have closed.

For each type being aligned:

1. `Read` the whole-chapter output `output/AI-{ULT,UST}/BOOK/BOOK-CH-aligned.usfm`.
2. It is **complete** only if every `\v N` for the chapter is present AND each
   carries `\zaln-s` markers. A file that is stale or covers only some verses is
   **not** complete — list exactly which verses are missing.

If any type is incomplete:

- Re-spawn **only that type's** align subagent **once**, for the **whole
  chapter** (same prompt as Step 2a — no `--verses`; the sub-skills take only a
  single contiguous `--verses START-END` range, so re-aligning the whole chapter
  is the reliable way to fill scattered gaps and it overwrites the whole-chapter
  file in one clean pass, no merge needed).
- Wait for it to complete, then re-verify coverage as above.

If, after the one whole-chapter re-spawn, a type is still incomplete: **report
failure plainly**, naming the type and the still-missing verses, and return a
non-success result. Do NOT report success on partial output — the per-verse
mapping JSON in `tmp/alignments/` remains on disk so the pipeline can
salvage/resume from it. Only report success once every requested type covers
every chapter verse with `\zaln-s` markers.

## Step 2b: Split into Batches (> 18 verses)

Get the batch ranges from the deterministic planner rather than computing them by
hand — hand arithmetic on long chapters has dropped the chapter tail (EZK 16, 63
verses, was mis-split into 1–16 / 16–30 / 31–45 / 46–60, leaving 61–63 unaligned;
see #233). Run:

    node /app/src/workspace-tools-cli.js plan_alignment_batches '{"book":"BOOK","chapter":CH,"verseCount":N}'

(Fallback: `mcp__workspace-tools__plan_alignment_batches` with the same args.) It
returns `batches` (each with `start`/`end`/`verses`) plus `coversChapter`. Use
those ranges verbatim.

The planner implements: number of batches = ceil(N / 18); batch size =
ceil(N / numBatches), distributed evenly with the last batch taking the
remainder. The batches are contiguous, non-overlapping, and the **last batch
always ends at the final verse N**.

Examples:
- 22 verses → 2 batches → 11 each (v1–11, v12–22)
- 56 verses → 4 batches → 14 each (v1–14, v15–28, v29–42, v43–56)
- 63 verses → 4 batches (v1–16, v17–32, v33–48, v49–63)
- 176 verses → 10 batches (v1–18, v19–36, ... v163–176)

Before spawning, sanity-check the ranges: batch 1 starts at v1, each batch starts
one verse after the previous batch ends (no gaps, no overlaps), and the last batch
ends at verse N. If `coversChapter` is false or the ranges fail this check, re-run
the planner — do not spawn subagents over an incomplete plan.

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
  - If running ULT: spawn `ult-align-K` subagent (`model: "opus"`, `effort: "medium"`) with the Step 2a ULT prompt template for `BOOK CH --verses START-END`
  - If running UST: spawn `ust-align-K` subagent (`model: "opus"`, `effort: "medium"`) with the Step 2a UST prompt template for `BOOK CH --verses START-END`
- Every batch subagent prompt uses the Step 2a template (Read the skill file; never the Skill tool)
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
