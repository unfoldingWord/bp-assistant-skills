---
name: post-edit-review
description: After humans edit ULT/UST, adapt existing issues and notes to match the edited text. Use when humans have edited ULT/UST and issues need reconciliation.
---

# Post-Human-Edit Review Orchestrator

After humans edit the ULT/UST, adapt existing issues to match their changes.

## Pipeline Context

If `--context <path>` is provided, read the context.json file. It contains:
- `sources.ult` — the current human-edited ULT from Door43 master (fetched fresh by the pipeline runner)
- `sources.ust` — the current human-edited UST from Door43 master

Use these as the authoritative human-edited text. Compare against the AI-generated versions in `output/AI-ULT/{BOOK}/` and `output/AI-UST/{BOOK}/`.

## Inputs

- **Book**: 3-letter abbreviation (PSA, GEN, 2SA, etc.)
- **Chapter**: number
- AI-generated ULT/UST (from `output/AI-ULT/{BOOK}/`, `output/AI-UST/{BOOK}/`)
- Human-edited ULT/UST — from `--context` sources (preferred) or fetch via `mcp__workspace-tools__fetch_door43`
- Existing issues TSV (from `output/issues/{BOOK}/`)

## When This Runs

Humans receive the AI-generated ULT and UST. They edit both. After their edits
are committed, this review reconciles the existing issues with the human-edited text.

## Guiding Principle

The human editor's ULT/UST is authoritative. We don't second-guess their translation
choices -- we adapt our issues to match the text they've produced. If a human flattens a
construct chain, we drop the figs-possession issue rather than flagging their edit. If they
reorder a verse, we update the gl_quote rather than arguing for the original order.

## What Can Change

Human edits affect existing issues in three ways:

1. **Issue becomes redundant** -- human resolved the issue in their ULT/UST.
   The issue addresses something that no longer exists in the text. Drop it.

2. **Issue needs updating** -- human reworded a phrase but the underlying issue persists.
   The gl_quote no longer matches the ULT. Update it to fit the human's phrasing.

3. **New issue appears** -- human edit creates a translation issue that wasn't in the
   AI-generated text. Add an issue for it.

## Step 0: Quick Diff Gate

**Model: Haiku** — this is a diff check, not a reasoning task.

Run this before spinning up any agents. If there are no human edits, skip the full pipeline immediately.

### Procedure

1. **Fetch master ULT and UST** from Door43 via `mcp__workspace-tools__fetch_door43`.
   - This is mandatory — no fallback to cached copies.
   - Retry up to 5 times on any failure. If all 5 attempts fail, abort the entire skill with a clear error message.

2. **Load aligned AI-generated files**:
   - ULT: `output/AI-ULT/{BOOK}/{BOOK}-{CHAPTER}-aligned.usfm`
   - UST: `output/AI-UST/{BOOK}/{BOOK}-{CHAPTER}-aligned.usfm`
   - These are the post-alignment versions. Use them, not the raw generated files.

3. **Extract the target chapter** from both the fetched master and the AI-generated files.
   - Locate `\c <CHAPTER>` markers to find the start line.
   - The chapter ends at the next `\c` marker or end of file.
   - Slice out only that chapter's content from each file.

4. **Diff the slices** — literal comparison, no stripping or normalization.
   - Diff master ULT chapter vs AI-generated ULT chapter.
   - Diff master UST chapter vs AI-generated UST chapter.

5. **Gate decision**:
   - If **both diffs are empty**: print `No human edits detected — skipping post-edit review.` and exit the skill cleanly (success). Do not write any output files. The pipeline runner will advance normally to the next step.
   - If **any diff exists**: proceed to the Diff Analyzer and Issue Reconciler below.

## Team Composition

Lighter-weight than the initial pipeline -- this is review, not full generation.

### Agent 1: Diff Analyzer
- Diffs human-edited ULT against AI-generated ULT (verse by verse)
- Diffs human-edited UST against AI-generated UST
- Categorizes each change:
  - **Rewording** (same meaning, different English) -> check gl_quote match
  - **Structural change** (changed voice, reordered, construct handling) -> check if issue still applies
  - **Content change** (different translation choice) -> may need new or revised issue
  - **Cosmetic** (punctuation, capitalization) -> usually safe to ignore
- Unchanged verses can be skipped entirely.

### Agent 2: Issue Reconciler
- For each existing issue in changed verses:
  - Does the gl_quote still appear in the human-edited ULT? If not, flag for update or removal.
  - Does the issue still exist? If not, mark for removal.
  - If the quote changed but the issue persists, update gl_quote.
- For each structural change found by Agent 1:
  - Does this create a new translation issue? If so, add it.

## Flow

```
Input:  AI-generated ULT/UST (from output/AI-ULT/{BOOK}/, output/AI-UST/{BOOK}/)
        Human-edited ULT/UST (from repo or provided files)
        Existing issues TSV (output/issues/{BOOK}/)

Agent 1: Diff Analyzer ──────┐
                              │
Agent 2: Issue Reconciler ────┘ (reads diffs + existing issues)

Output:  - Updated issues TSV
         - Change log (what was dropped, updated, added, and why)
```

## Outputs

1. `output/issues/<BOOK>/<BOOK>-<CHAPTER>.tsv` -- updated issues matching human ULT
2. `output/review/<BOOK>/<BOOK>-<CHAPTER>-changelog.tsv` -- what changed and why
3. Update `output/AI-ULT/{BOOK}/{BOOK}-{CHAPTER}.usfm` with the editor's text so downstream tools (tn-writer) use the authoritative version rather than stale AI text

## Edge Cases

- **Human added a verse division** (split or merged verses) -> reference numbers shift,
  all issues for affected verses need re-mapping
- **Human added implied words in {curly braces}** -> gl_quote matching needs to handle braces
  (already handled by strip_braces in verify_at_fit.py)
- **Human deleted a verse or section** -> all issues for that content should be dropped
