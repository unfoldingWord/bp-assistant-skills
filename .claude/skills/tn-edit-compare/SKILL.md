---
name: tn-edit-compare
description: Compare editor-edited Translation Notes (TN TSV) against the prior version to learn note-level preferences. Proposes findings for tn_decisions.csv (read by tn-writer) and issue_decisions.csv (read by issue-identification); recording confirmed findings is tn-edit-record's job. Use when reviewing the -be- branch TN edits surfaced by the overnight Sensor.
allowed-tools: Read, Grep, Glob, Bash
---

# TN Edit Compare

The TN counterpart to `editor-compare`. TN is row-keyed TSV, not USFM, so it has
its own comparator. Given a book where a human editor changed Translation Notes
on a `-be-` branch, identify the systematic note-level preferences and feed them
back into the decision stores — so the next `tn-writer` run drafts notes the way
the editors actually want them.

This skill compares and proposes only; it never writes memory (Write/Edit are
deliberately absent from its allowed-tools). The recording half lives in the
`tn-edit-record` skill.

## Prerequisites

- A review task from the overnight Sensor: `{ repo: en_tn, book, editor, chapters }`.
- The mechanical row-keyed diff. The Sensor already wrote it to
  `data/overnight-review/<date>/proposals.jsonl` (filter to this book), OR
  compute it directly:
  ```bash
  node -e "const {prepareCompareTn}=require(process.env.BP_APP_REPO+'/src/workspace-tools/tsv-tools.js'); \
    const fs=require('fs'); \
    const r=prepareCompareTn({oldPath:'OLD.tsv', newPath:'NEW.tsv', book:'PSA'}); \
    console.log(JSON.stringify(r.summary)); for(const c of r.changes) console.log(JSON.stringify(c));"
  ```
  Each change is one of `reworded` / `quote-changed` / `dropped` / `added`
  (cosmetic, whitespace-only, and ID-only deltas are already filtered out).

## Step 1 — Interpret each change into a hypothesis

For every change, ask *why* the editor made it and whether it generalizes:

| changeType | What it usually means | Candidate preference |
|---|---|---|
| `reworded` | The note's wording was off (too literal, unclear, wrong register) | note-phrasing rule for that `SupportReference` |
| `quote-changed` | The Quote anchored the wrong span | quote-selection rule (which words to anchor) |
| `dropped` | The note wasn't warranted (over-flagging) | a *keep/drop* signal: this `SupportReference` is over-suggested in this context |
| `added` | A note was missing (under-flagging) | a *keep/drop* signal: flag this `SupportReference` here |

## Step 2 — Phase A: dedup against existing memory

Before proposing anything, grep what's already captured:
```bash
grep -i "<SupportReference or phrase>" data/quick-ref/tn_decisions.csv
grep -i "<phrase>" data/quick-ref/issue_decisions.csv
```
If a row already covers it, propose **strengthening** that row rather than a
duplicate.

## Step 3 — Phase B: canonical-conflict check

TN classification has canonical authorities. Grep them; if they contradict the
editor's change, **do not record** it — surface it for human escalation instead:
- `data/issues_resolved.txt` (highest authority on how issues are classified)
- `data/templates.csv` (note-template authority)
- the protected rendering glossaries, when a preference touches a Hebrew term or
  rendering: `data/glossary/hebrew_ot_glossary.csv`, `data/glossary/psalms_reference.csv`,
  `data/glossary/sacrifice_terminology.csv`, `data/glossary/biblical_phrases.csv`,
  `data/glossary/biblical_measurements.csv`

If no canonical source addresses it, proceed.

## Step 4 — Classify scope (general vs context-specific)

- **general** — the same change recurs across **≥2 chapters or ≥2 books** (check
  the diff and prior journal entries). Scope `Book = ALL`.
- **context-specific** — confined to one chapter/verse. Scope `Book` to the book
  code and note the context; never generalize a single occurrence.

## Step 5 — Hand off; never write (mirror editor-compare's Turn-3)

Like `editor-compare`, do not write memory before the finding is confirmed —
and this skill does not write memory at all:
- **Interactive use** — confirm the finding with the editor first (the editor's
  approval is the gate). To record the confirmed decisions, invoke the
  `tn-edit-record` skill and hand it the confirmed findings; it owns the exact
  CSV row formats and the append.
- **Automated / overnight use** — run as a PROPOSER only: emit the findings as
  your result (JSON) and write nothing. The overnight runner / a human-merged PR
  materializes them, so the canonical-conflict and PR-review gates still apply.
  Never invoke `tn-edit-record` from an unattended run.

Target stores, for orientation only (the write instructions live in
`tn-edit-record`): note-phrasing / quote-selection preferences go to
`data/quick-ref/tn_decisions.csv` (read by `tn-writer`); keep/drop
(over-/under-flagging) signals go to `data/quick-ref/issue_decisions.csv`
(read by `issue-identification`).

## Step 6 — Results-first summary

Per `CLAUDE.md`: lead with what changed. List each preference proposed (with
tier + the editor + book/chapter evidence), each item skipped as a duplicate,
and each canonical conflict held for escalation. No preamble, no trailing
questions.
