---
name: post-edit-review
description: After humans edit ULT/UST, adapt existing issues and notes to match the edited text. Use when humans have edited ULT/UST and issues need reconciliation.
---

# Post-Human-Edit Review Orchestrator

After humans edit the ULT/UST, adapt existing issues to match their changes.

## Pipeline Context

If `--context <path>` is provided, read the context.json file. It contains:
- `sources.ultMasterPlain` — the current human-edited ULT chapter, fetched fresh from Door43 master and stripped of alignment markers by the pipeline runner. Use this as the authoritative human-edited text.
- `sources.ust` — the current human-edited UST from Door43 master

## Inputs

- **Book**: 3-letter abbreviation (PSA, GEN, 2SA, etc.)
- **Chapter**: number
- AI-generated ULT: `output/AI-ULT/{BOOK}/{BOOK}-{CHAPTER}.usfm` (plain, pre-alignment version — do NOT load the `-aligned.usfm` files)
- AI-generated UST: `output/AI-UST/{BOOK}/{BOOK}-{CHAPTER}.usfm`
- Human-edited ULT: `context.sources.ultMasterPlain` (preferred) — already fetched and alignment-stripped by the pipeline runner. If context is unavailable, fetch via `mcp__workspace-tools__fetch_door43`.
- Human-edited UST: `context.sources.ust` (preferred), otherwise fetch via `mcp__workspace-tools__fetch_door43`
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
