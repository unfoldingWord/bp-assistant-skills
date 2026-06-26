---
name: golden-benchmark
description: Score pipeline output against published golden chapters (JOS 1, NAM 1, MAL 1) and run regression checks from closed bugs. Use when asked to benchmark the pipeline, measure a skill change, or check whether output meets the published bar.
allowed-tools: Read, Grep, Glob, Bash, Task
---

## Purpose

Turn "does the output feel polished?" into numbers that can be compared before and after a skill change. The benchmark compares freshly generated ULT/UST/TN for a golden chapter against the published human-polished version (v88 release era), and re-tests every previously fixed quality bug.

The golden set spans three genres from the team's best published books:

| Chapter | Genre | Published notes |
|---------|-------|-----------------|
| JOS 1 | narrative | 53 |
| NAM 1 | poetry / prophecy | 62 |
| MAL 1 | prophetic disputation | 79 |

Golden fixtures live in `golden/` (committed, pinned to the release recorded in `golden/meta.json`). Refresh them only deliberately, with `scripts/fetch_golden.mjs`.

## How to Run

### 1. Generate the chapter as if unpublished

Run the normal pipeline for the golden chapter (e.g. `initial-pipeline JOS 1`, or `makeBP` phases through tn-writer). Output lands in the standard locations (`output/AI-ULT/JOS/JOS-01.usfm`, `output/AI-UST/JOS/JOS-01.usfm`, `output/notes/JOS/JOS-01.tsv`). Do not push benchmark runs to Door43.

### 2. Score against the published version

```bash
node .claude/skills/golden-benchmark/scripts/score_benchmark.mjs --book JOS --chapter 1
```

Writes `output/benchmark/JOS/JOS-01-scorecard.md` (readable) and `.json` (for comparing runs). Scores whatever generated files exist and skips the rest, so partial runs (ULT only) are fine.

### 3. Run regression checks

```bash
node .claude/skills/utilities/scripts/validation/run_regression_checks.mjs \
  --stage ULT --file output/AI-ULT/JOS/JOS-01.usfm --book JOS --chapter 1
node .claude/skills/utilities/scripts/validation/run_regression_checks.mjs \
  --stage TN --file output/notes/JOS/JOS-01.tsv --book JOS --chapter 1
```

Every closed quality issue that could be encoded mechanically lives in `.claude/skills/utilities/regression/regression-checks.json`. A FAIL means a previously fixed mistake has returned — treat it as a blocker for the change being tested.

## Reading the Scorecard

- **Mean token F1** — how close each verse's wording is to published (1.0 = identical). Track the trend, not the absolute number; a change that drops F1 noticeably on a golden chapter deserves a look at the listed worst verses before shipping.
- **Verse coverage** — must always be complete; anything less is a structural failure, not a style difference.
- **TN type@verse recall** — of the notes the human team wrote, how many did we also flag (same verse, same issue type)? **Precision** is the reverse: how many of ours did the humans also have? Low precision is over-noting; low recall means translators lose help the published books give them.
- **Convention problems** — mechanical style violations in generated notes (AT format, IDs, template phrasing). Published chapters score zero here, so any nonzero count is ground to make up.
- **Unmatched lists** — the concrete verses/types to read first when deciding whether a difference is a real miss or a defensible judgment call.

## Honest Caveats

- Generation can consult published precedent (Strong's index, published ULT/UST), and the golden books are part of that precedent. Scores are therefore an upper bound on unpublished-book quality. The benchmark's primary value is **regression tracking** — comparing the same chapter across skill versions — not absolute capability measurement.
- Token F1 punishes legitimate synonym choices the same as real errors. Read the worst-verse diffs before concluding a change made things worse.
- A self-test (`--self-test`) scores golden against itself and must produce perfect text scores; use it after editing the scorer.

## Typical Workflow for a Skill Change

1. Before the change: generate + score a golden chapter, keep the scorecard JSON.
2. Apply the skill change.
3. Regenerate the same chapter, score again, diff the two scorecards.
4. Run regression checks on the new output.
5. Ship the skill change only if scores held (or improved) and regressions are clean.

## Refreshing Fixtures

```bash
node .claude/skills/golden-benchmark/scripts/fetch_golden.mjs            # all three chapters
node .claude/skills/golden-benchmark/scripts/fetch_golden.mjs --book NAM --chapter 1
```

Refetching changes the target the team is measured against — do it only when the published source itself was improved, and commit the updated fixtures with a note about why.

## Related

- `tests/` at the repo root (`npm test`) — unit tests for the validators and the alignment converter; run before committing script changes.
- [repo-insert](../repo-insert/SKILL.md) Step 2.5 — the same validators as a pre-push gate.
- [pipeline-overview](../pipeline-overview/SKILL.md) — where generation stages fit.
