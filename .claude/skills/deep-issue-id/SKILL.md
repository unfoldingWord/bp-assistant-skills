---
name: deep-issue-id
description: Multi-agent adversarial issue identification against human ULT/UST from Door43 master. 2 parallel domain analysts + challenger debate, without AI text generation. Supports --verses for chunked analysis of long chapters.
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

## Setup (orchestrator runs directly)

Read `orchestration-conventions.md` for chapter padding and model assignments.

### Working Directory

```bash
TMP=tmp/deep-issue-id/<BOOK>-<CH>       # e.g. tmp/deep-issue-id/PSA-119
mkdir -p $TMP
```

With verse range: `TMP=tmp/deep-issue-id/<BOOK>-<CH>-v<START>-<END>`

### Fetch and Parse

```bash
python3 .claude/skills/utilities/scripts/fetch_door43.py <BOOK> > $TMP/book_ult.usfm
python3 .claude/skills/utilities/scripts/fetch_door43.py <BOOK> --type ust > $TMP/book_ust.usfm 2>/dev/null || true

node .claude/skills/utilities/scripts/usfm/parse_usfm.js $TMP/book_ult.usfm \
  --chapter <N> [--verse <START>-<END>] \
  --output-json $TMP/alignments.json \
  --output-plain $TMP/ult_plain.usfm

node .claude/skills/utilities/scripts/usfm/parse_usfm.js $TMP/book_ust.usfm \
  --chapter <N> [--verse <START>-<END>] \
  --plain-only > $TMP/ust_plain.usfm 2>/dev/null || true
```

### Compare, Detect, Index

```bash
python3 .claude/skills/issue-identification/scripts/compare_ult_ust.py \
  $TMP/ult_plain.usfm $TMP/ust_plain.usfm \
  --chapter <N> --output $TMP/ult_ust_diff.tsv

python3 .claude/skills/issue-identification/scripts/detection/detect_abstract_nouns.py \
  $TMP/alignments.json --format tsv > $TMP/detected_issues.tsv

python3 .claude/skills/utilities/scripts/build_tn_index.py
```

Passive voice is identified by analysts during analysis (prompt-over-code). See `figs-activepassive.md` for the pattern, stative adjective exclusions, and worked examples.

Precedent evidence is positive-only. Finding published TN examples supports a classification. Finding none is only meaningful if the chapter has published TNs.

## Team Setup

```
TeamCreate "deep-issue-<BOOK>-<CHAPTER>"
```

Team name pattern: `deep-issue-PSA-120`, `deep-issue-GEN-01`, etc. With verse range: `deep-issue-PSA-119-v1-40`.

## Wave 2: Issue Identification

Read `analyst-domains.md` for domain assignments and cross-reading protocol. Spawn both analysts with `team_name` set.

Each analyst reads:
- Human ULT (`$TMP/ult_plain.usfm`)
- Human UST (`$TMP/ust_plain.usfm`) if available
- Alignment JSON (`$TMP/alignments.json`)
- ULT/UST divergence patterns (`$TMP/ult_ust_diff.tsv`)
- Automated detections (`$TMP/detected_issues.tsv`)

**Hold for Wave 3**: After writing your TSV, do NOT mark your task as completed. Send a message to team-lead confirming your file is written, then wait for DMs from the challenger agent. Defend your classifications in one round, then wait for the challenger's "rulings complete" message before marking your task completed.

Wait for both analysts to send their "file written" messages before proceeding to Wave 3.

## Wave 3: Challenge and Defend

Read `challenger-protocol.md`. Spawn the challenger (`model: "sonnet"`, name: "challenger").

**ULT coherence check**: The human ULT is authoritative. If it already handles the construct naturally (e.g., already made a passive active, already unpacked a figure), drop the issue. Flag the issue, not the text.

After the challenger writes rulings, it sends "Rulings complete" to each analyst, releasing them from hold.

Output: `$TMP/wave3_challenges.tsv`

## Wave 4a: Merge

Read `merge-procedure.md`. The orchestrator merges all findings, applies rulings, deduplicates, and orders.

Output: `output/issues/<BOOK>/<BOOK>-<CH>.tsv`
With verse range: `output/issues/<BOOK>/<BOOK>-<CH>-v<START>-<END>.tsv`

## Gemini Review

Read `gemini-review-wave.md`. After the merge writes the final issues TSV, run Gemini as independent reviewer. Only the `issues` stage applies (deep-issue-id doesn't generate ULT/UST).

```bash
python3 .claude/skills/utilities/scripts/gemini_review.py --stage issues --book <BOOK> --chapter <CHAPTER>
```

## Cleanup

After the merge (and optional Gemini review) completes:
1. Send `shutdown_request` to structure, rhetoric, challenger
2. Wait for shutdown confirmations
3. `TeamDelete` to clean up team resources

## Guiding Principle

The human ULT/UST is authoritative. Issues adapt to the text, not the other way around. If the human rendering already resolves a potential issue, there is no issue to flag.

## Output

Without verse range: `output/issues/<BOOK>/<BOOK>-<CH>.tsv`
With verse range: `output/issues/<BOOK>/<BOOK>-<CH>-v<START>-<END>.tsv`

After all chunks are complete, concatenate into `output/issues/<BOOK>/<BOOK>-<CH>.tsv` (strip duplicate headers, preserve verse ordering).

Same format as base issue-identification:
```
[book]	[chapter:verse]	[supportreference]	[ULT text]			[explanation if needed]
```

## Flow

```
Setup:    Fetch human ULT/UST from Door43 master
          Parse -> alignment JSON + plain text (chapter-filtered)
          Compare ULT/UST divergence patterns
          Run automated detection (abstract nouns)
          Build published TN index

Team:     TeamCreate "deep-issue-<BOOK>-<CHAPTER>"

Wave 2:   Structure ───────────┐  (2 teammates, cross-read files,
          Rhetoric ────────────┘   DM on disagreements,
                                   stay alive for Wave 3)

Wave 3:   Challenger spawns ──── challenges each analyst via DM
          Analysts defend ──────  one round of defend/respond
          Challenger rules ─────  writes final rulings

Wave 4a:  Merge ────────────────  (applies rulings, deduplicates)

Gemini:   gemini_review.py --stage issues

Cleanup:  shutdown_request all -> TeamDelete
```
