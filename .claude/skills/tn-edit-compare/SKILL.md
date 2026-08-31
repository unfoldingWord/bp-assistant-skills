---
name: tn-edit-compare
description: Compare editor-edited Translation Notes (TN TSV) against the prior version to learn note-level preferences, and propose rows for tn_decisions.csv (read by tn-writer) and issue_decisions.csv (read by issue-identification). Read-only PROPOSER — it never writes; use tn-edit-record to record confirmed rows. Use when reviewing the -be- branch TN edits surfaced by the overnight Sensor.
allowed-tools: Read, Grep, Glob
---

# TN Edit Compare (proposer)

The TN counterpart to `editor-compare`. TN is row-keyed TSV, not USFM, so it has
its own comparator. Given a book where a human editor changed Translation Notes
on a `-be-` branch, identify the systematic note-level preferences and **propose**
them — so the next `tn-writer` run drafts notes the way the editors actually want
them.

**This skill is read-only.** It has no `Write`/`Edit`, no `Bash`, and no
write-capable MCP tool, so it cannot append to a decision store even when the
runner grants blanket permission (`permissionMode: bypassPermissions`) or when
cwd is a live git worktree. That is deliberate: the automated overnight path must
be a proposer only, and the guard is the tool list rather than prose an agent can
read past. Recording is a separate, interactive skill: **`tn-edit-record`**.

This skill compares and proposes only; it never writes memory (Write/Edit are
deliberately absent from its allowed-tools). The recording half lives in the
`tn-edit-record` skill.

## Prerequisites

- A review task from the overnight Sensor: `{ repo: en_tn, book, editor, chapters }`.
- The mechanical row-keyed diff. The Sensor already wrote it to
  `data/overnight-review/<date>/proposals.jsonl` (filter to this book). If you
  need to compute it manually (outside the overnight path), run this in a
  terminal where Bash is available:
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
If a row already covers it, propose **strengthening** that row (quote the existing
row in your proposal) rather than proposing a duplicate.

## Step 3 — Phase B: canonical-conflict check

TN classification has canonical authorities. Grep them; if they contradict the
editor's change, **do not propose** it — surface it for human escalation instead:
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

## Step 5 — Emit proposals (never write)

Emit the surviving findings as your result. Write nothing — no decision store, no
`SKILL.md` body, no `data/issues_resolved.txt`, no protected glossary. The
downstream consumer materializes the rows, so the canonical-conflict and
PR-review gates still apply:

- **Automated / overnight use** — your emitted JSON *is* the deliverable. The
  overnight runner collects it into the proposal feed, and a human-merged PR
  applies it.
- **Interactive use** — show the proposals to the editor. Once the editor
  approves (their approval is the gate), hand the approved subset to
  **`tn-edit-record`**, which owns the write.

Emit one object per proposal:
```json
{"store":"tn_decisions","reference":"<Reference>","supportReference":"<SupportReference>",
 "note":"<concise note preference>","book":"<BOOK or ALL>","context":"<CH:VS context>",
 "scope":"general|context-specific","evidence":"<editor + book/chapter the change came from>"}
```
```json
{"store":"issue_decisions","phrase":"<phrase or anchor>","issueType":"<SupportReference issue type>",
 "book":"<BOOK or ALL>","context":"<CH:VS context>","verdict":"keep|drop","notes":"<why>",
 "scope":"general|context-specific","evidence":"<editor + book/chapter the change came from>"}
```
For a proposal that strengthens an existing row, add
`"strengthens":"<the existing CSV row verbatim>"`. `tn-edit-record` translates
these objects into CSV rows; the column order and quoting rules live there.

## Step 6 — Results-first summary

Per `CLAUDE.md`: lead with what changed. List each preference proposed (with
scope + the editor + book/chapter evidence), each item skipped as a duplicate,
and each canonical conflict held for escalation. No preamble, no trailing
questions.
