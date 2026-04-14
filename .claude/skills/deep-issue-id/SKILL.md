---
name: deep-issue-id
description: Multi-agent adversarial issue identification for human-authored ULT/UST. Use when asked to find issues in human-authored text or analyze human ULT/UST for translation concerns.
---

# Deep Issue Identification (Human ULT/UST)

Adversarial multi-agent issue identification against human-authored ULT/UST from repo master. Same analytical depth as initial-pipeline waves 2-3-4a, but skips AI text generation since the human text already exists.

This skill orchestrates issue-identification agents. Shared orchestration
patterns are in sibling reference files (read each at the relevant stage):
- `orchestration-conventions.md` (start)
- `analyst-domains.md` (Wave 2)
- `challenger-protocol.md` (Wave 3)
- `merge-procedure.md` (Wave 4a)
- `gemini-review-wave.md` (after merge)

Analysts receive `.claude/agents/issue-identification.md` when spawned.

## Inputs

- **Book**: 3-letter abbreviation (PSA, GEN, 2SA, etc.)
- **Chapter**: number
- **Verses**: `--verses 1-40` (optional) -- restrict analysis to a verse range within the chapter. Useful for long chapters (e.g., PSA 119 at 176 verses) that benefit from chunked runs.

## Verse Range

If `--verses <start>-<end>` is specified:
- Pass `--verse <start>-<end>` to both `parse_usfm.js` calls (filters alignment JSON and plain text)
- Downstream scripts (compare, detect) automatically operate on the filtered data
- Use verse-range suffix in tmp directory: `TMP=tmp/deep-issue-id/<BOOK>-<CH>-v<START>-<END>`
- Output file uses verse range: `output/issues/<BOOK>/<BOOK>-<CH>-v<START>-<END>.tsv`
- Team name includes range: `deep-issue-<BOOK>-<CH>-v<START>-<END>`

After running all chunks, concatenate the chunk TSVs (stripping any duplicate headers) into the final `output/issues/<BOOK>/<BOOK>-<CH>.tsv`.

## Pipeline Context

If `--context <path>` is provided, read the context.json file. The pipeline runner has already fetched the current ULT/UST from Door43 master:
- `sources.ult` — chapter ULT USFM (use instead of running `fetch_door43.py`)
- `sources.ust` — chapter UST USFM
- `sources.ultFull` — full book ULT (for alignment parsing)
- `sources.ustFull` — full book UST
- `sources.hebrew` — Hebrew source file

When context is available, skip the "Fetch and Parse" step's fetch commands and read directly from the context paths. Still run the parse/compare/detect scripts on the fetched content.

## Setup (orchestrator runs directly)

Read `orchestration-conventions.md` for chapter padding and model assignments.

### Working Directory

Set `TMP=tmp/deep-issue-id/<BOOK>-<CH>` (e.g. `tmp/deep-issue-id/PSA-119`). MCP tools create output directories automatically — no shell mkdir needed.

With verse range: `TMP=tmp/deep-issue-id/<BOOK>-<CH>-v<START>-<END>`

### Fetch and Parse

**Without context**: Use `mcp__workspace-tools__fetch_door43` with `book="<BOOK>"`, output to `$TMP/book_ult.usfm`. Repeat with `type="ust"` for `$TMP/book_ust.usfm`.

**With context** (`--context <path>` was provided): Use `sources.ultFull` and `sources.ustFull` directly as the full-book paths — no copy needed.

In both cases, extract chapter plain text using MCP tools:
- `mcp__workspace-tools__read_usfm_chapter` with `file=<fullBookUltPath>`, `chapter=<N>`, `verseStart`/`verseEnd` if verse range applies, `plain=true`, `output="$TMP/ult_plain.usfm"`
- `mcp__workspace-tools__read_usfm_chapter` with `file=<fullBookUstPath>`, `chapter=<N>`, same verse range, `plain=true`, `output="$TMP/ust_plain.usfm"`

### Editor Notes

Use Glob to check if `data/editor-notes/<BOOK>.md` exists. If it does, read it with the Read tool and pass its content to both analysts as additional input. Each analyst should factor these human observations into their analysis.

### Compare, Detect, Index

Use `mcp__workspace-tools__compare_ult_ust` with `ultFile="$TMP/ult_plain.usfm"`, `ustFile="$TMP/ust_plain.usfm"`, `chapter=<N>`, `output="$TMP/ult_ust_diff.tsv"`.

Use `mcp__workspace-tools__detect_abstract_nouns` with the plain ULT text (read `$TMP/ult_plain.usfm` and pass as `text`), `format="tsv"`. Write the result to `$TMP/detected_issues.tsv` using the Write tool.

Use `mcp__workspace-tools__build_tn_index` (no parameters needed for default build).

Passive voice is identified by analysts during analysis (prompt-over-code). See `figs-activepassive.md` for the pattern, stative adjective exclusions, and worked examples.

Precedent evidence is positive-only. Finding published TN examples supports a classification. Finding none is only meaningful if the chapter has published TNs.

## Spawning Sub-Agents

Use `Task` to spawn sub-agents. When spawning two analysts in parallel, call
Task twice in a single message so they run concurrently. Each sub-agent writes
its output to a file; the orchestrator reads the files after both tasks complete.

**You must actively poll for completion.** After spawning tasks, immediately call
`TaskGet` in a loop to check their status. Do NOT just say "I'll wait" — you must
make a tool call on every turn or the session will end. Poll both task IDs with
`TaskGet` until both show `completed` status, then read their output files and
proceed to the next wave. Apply the same pattern for the Wave 3 challenger task.

If `TeamCreate` and `Agent` are available (CLI mode), use them instead per
`orchestration-conventions.md`. The wave structure is identical either way.

## Wave 2: Issue Identification

Read `analyst-domains.md` for domain assignments. Spawn both analysts in
parallel. Each analyst receives:

- The agent instructions from `.claude/agents/issue-identification.md`
- Their domain assignment (structure or rhetoric)
- Paths to all input files:
  - Human ULT (`$TMP/ult_plain.usfm`)
  - Human UST (`$TMP/ust_plain.usfm`) if available
  - Alignment JSON (`$TMP/alignments.json`)
  - ULT/UST divergence patterns (`$TMP/ult_ust_diff.tsv`)
  - Automated detections (`$TMP/detected_issues.tsv`)
  - Editor notes (`data/editor-notes/<BOOK>.md`) if available

Wait for both analysts to complete before proceeding.

## Wave 3: Challenge

Read `challenger-protocol.md`. Spawn a challenger sub-agent (`model: "sonnet"`).

The challenger reads both analyst TSVs (`$TMP/wave2_structure.tsv`, `$TMP/wave2_rhetoric.tsv`) and writes rulings to `$TMP/wave3_challenges.tsv`.

**ULT coherence check**: The human ULT is authoritative. If it already handles the construct naturally (e.g., already made a passive active, already unpacked a figure), drop the issue. Flag the issue, not the text.

Wait for the challenger to complete before proceeding.

Output: `$TMP/wave3_challenges.tsv`

## Wave 4a: Merge

Read `merge-procedure.md`. The orchestrator merges all findings, applies rulings, deduplicates, and orders.

Output: `output/issues/<BOOK>/<BOOK>-<CH>.tsv`
With verse range: `output/issues/<BOOK>/<BOOK>-<CH>-v<START>-<END>.tsv`

## Gemini Review (optional, activation only)

Only run if `--gemini` is explicitly passed. Skip by default. If running: read `gemini-review-wave.md`. Only the `issues` stage applies (deep-issue-id doesn't generate ULT/UST).

Note: the Gemini review script requires Python and is only available in CLI/host mode, not inside the Docker pipeline container.

## Guiding Principle

The human ULT/UST is authoritative. Issues adapt to the text, not the other way around. If the human rendering already resolves a potential issue, there is no issue to flag.

## Output

Without verse range: `output/issues/<BOOK>/<BOOK>-<CH>.tsv`
With verse range: `output/issues/<BOOK>/<BOOK>-<CH>-v<START>-<END>.tsv`

After all chunks are complete, concatenate into `output/issues/<BOOK>/<BOOK>-<CH>.tsv` (strip duplicate headers, preserve verse ordering).

Same format as base issue-identification (see that skill for full rules — key points: ULT text must be copied verbatim, use `&` only for genuinely discontinuous phrases):
```
[book]	[chapter:verse]	[supportreference]	[ULT text]			[explanation if needed]
```

## Flow

```
Setup:    Fetch human ULT/UST from Door43 master (or use pipeline context)
          read_usfm_chapter -> plain text (chapter-filtered)
          compare_ult_ust -> divergence patterns
          detect_abstract_nouns -> detected_issues.tsv
          build_tn_index

Wave 2:   Task: Structure ──────┐  (2 parallel sub-agents,
          Task: Rhetoric ───────┘   each writes TSV to $TMP/)

Wave 3:   Task: Challenger ─────── reads both TSVs, writes rulings

Wave 4a:  Orchestrator merges ──── applies rulings, deduplicates

Gemini:   gemini-review-wave.md --stage issues (CLI/host only, optional)
```
