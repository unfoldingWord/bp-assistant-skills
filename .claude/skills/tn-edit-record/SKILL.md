---
name: tn-edit-record
description: Record editor-confirmed TN preference findings from tn-edit-compare into the decision stores — tn_decisions.csv (read by tn-writer) and issue_decisions.csv (read by issue-identification). Interactive use only. Use when an editor has confirmed tn-edit-compare findings and asks to record them.
allowed-tools: Read, Grep, Glob, Write, Edit, Bash
---

# TN Edit Record

**Interactive / human-confirmed use ONLY.** This skill appends rows to the
decision stores and must NEVER be invoked by unattended automation (the
overnight runner, cron pipelines, or any `bypassPermissions` batch run).
Automated runs use `tn-edit-compare` as a PROPOSER — emit JSON, write
nothing — and a human-merged PR materializes the rows. If you are running
unattended and reading this: stop, do not write, report the findings as your
result instead.

The recording half of `tn-edit-compare`. Input: findings the editor has already
confirmed (each with Reference/phrase, SupportReference, the preference, scope
from Step 4, and context). The editor's approval is the gate — do not record
unconfirmed hypotheses.

## Step 1 — Re-check for duplicates before appending

Before recording anything, grep what's already captured:
```bash
grep -i "<SupportReference or phrase>" data/quick-ref/tn_decisions.csv
grep -i "<phrase>" data/quick-ref/issue_decisions.csv
```
If a row already covers it, **strengthen** that row rather than appending a duplicate.

## Step 2 — Append the rows

Write note-phrasing / quote-selection preferences to
`data/quick-ref/tn_decisions.csv` (read by `tn-writer`). Columns:
`Reference,SupportReference,Note,Book,Context,Date,Source`:
```
<Reference>,<SupportReference>,<concise note preference>,<BOOK or ALL>,<CH:VS context>,<YYYY-MM-DD>,editor
```
Write keep/drop (over-/under-flagging) signal to
`data/quick-ref/issue_decisions.csv` (read by `issue-identification`). Columns:
`Phrase,IssueType,Book,Context,Notes,Date,Source` — put the `keep` or `drop`
verdict in `Context`:
```
<phrase or anchor>,<SupportReference issue type>,<BOOK or ALL>,<CH:VS context — keep|drop>,<why>,<YYYY-MM-DD>,editor
```
Quote any field that contains a comma, double-quote, or newline (wrap in double
quotes, doubling internal quotes — RFC 4180) so the row stays well-formed.
Use `Source: editor` for human-attributed rulings. Never write any `SKILL.md`
body, `data/issues_resolved.txt`, or a protected glossary
(`hebrew_ot_glossary.csv`, `psalms_reference.csv`, `sacrifice_terminology.csv`,
`biblical_phrases.csv`, `biblical_measurements.csv`) from this skill.

## Step 3 — Results-first summary

Per `CLAUDE.md`: lead with what changed. List each row appended (file + row),
each existing row strengthened, and each item skipped as a duplicate. No
preamble, no trailing questions.
