---
name: tn-edit-record
description: Record editor-approved TN preference rows proposed by tn-edit-compare into data/quick-ref/tn_decisions.csv (read by tn-writer) and data/quick-ref/issue_decisions.csv (read by issue-identification). Interactive only — never invoke from the automated overnight path, which is PROPOSER-only.
allowed-tools: Read, Grep, Glob, Write, Edit, Bash
---

# TN Edit Record (writer)

The write half of the TN edit-review loop. `tn-edit-compare` proposes; this skill
records. The split is the mechanical guard that keeps the automated overnight
path from writing unreviewed preference rows: `tn-edit-compare` has no
`Write`/`Edit`, so the only way to reach a decision store is to run *this* skill
deliberately.

## When NOT to use this skill

- **Never in the automated / overnight path.** That path runs
  `tn-edit-compare` as a PROPOSER: it emits rows, a human-merged PR materializes
  them. If you are running unattended (no editor in the loop to approve), stop —
  emit the rows instead.
- **Never without an editor's approval of the specific rows.** The editor's
  approval is the gate, exactly as in `editor-compare`'s Turn-3 discipline.

## Step 1 — Take approved proposals only

Input is the proposal objects emitted by `tn-edit-compare` (Step 5 there), pruned
to the subset the editor approved. Do not re-derive proposals here and do not
record anything the editor did not explicitly confirm.

## Step 2 — Re-check dedup and canonical conflicts before writing

The proposals may be stale by the time they are approved, so re-run the two gates:
```bash
grep -i "<SupportReference or phrase>" data/quick-ref/tn_decisions.csv
grep -i "<phrase>" data/quick-ref/issue_decisions.csv
grep -i "<phrase>" data/issues_resolved.txt
```
- A row already covers it → **strengthen** that row (edit it in place) rather
  than appending a duplicate. If the proposal carries a `strengthens` field, use
  that verbatim CSV row as the exact locator to find the row to edit; otherwise
  grep to find it.
- `data/issues_resolved.txt`, `data/templates.csv`, or a protected glossary
  contradicts it → **do not write**; surface it for human escalation.

## Step 3 — Write the rows

Translate proposal fields to CSV columns as follows:

**Note-phrasing / quote-selection preferences** go to `data/quick-ref/tn_decisions.csv`
(read by `tn-writer`). Columns:
`Reference,SupportReference,Note,Book,Context,Date,Source`:
```
<Reference>,<SupportReference>,<concise note preference>,<BOOK or ALL>,<CH:VS context>,<YYYY-MM-DD>,editor
```
Field mapping from proposal object:
- `reference` → Reference
- `supportReference` → SupportReference
- `note` → Note
- `book` → Book (`ALL` when scope=general; book code such as `PSA` when
  scope=context-specific — the proposal's `book` field already carries the right
  value, `scope` is just an explicit label for the same distinction)
- `context` → Context
- today's date → Date
- `editor` → Source (hardcoded; the `evidence` field is captured in the Step 4
  summary for provenance but is not written to a CSV column)

**Keep/drop (over-/under-flagging) signal** goes to `data/quick-ref/issue_decisions.csv`
(read by `issue-identification`). Columns:
`Phrase,IssueType,Book,Context,Notes,Date,Source` — put the `keep` or `drop`
verdict in `Context`:
```
<phrase or anchor>,<SupportReference issue type>,<BOOK or ALL>,<CH:VS context — keep|drop>,<why>,<YYYY-MM-DD>,editor
```
Field mapping from proposal object:
- `phrase` → Phrase
- `issueType` → IssueType
- `book` → Book (same scope rule as above)
- `context` + `verdict` → Context (format: `<CH:VS context> — keep|drop`)
- `notes` → Notes
- today's date → Date
- `editor` → Source (the `evidence` field goes to the Step 4 summary, not here)

Quote any field that contains a comma, double-quote, or newline (wrap in double
quotes, doubling internal quotes — RFC 4180) so the row stays well-formed.

**Never** write any `SKILL.md` body, `data/issues_resolved.txt`, or a protected
glossary (`hebrew_ot_glossary.csv`, `psalms_reference.csv`,
`sacrifice_terminology.csv`, `biblical_phrases.csv`, `biblical_measurements.csv`)
from this skill. Only `data/quick-ref/tn_decisions.csv` and
`data/quick-ref/issue_decisions.csv` may be modified.

## Step 4 — Results-first summary

Per `CLAUDE.md`: lead with what changed. List each row written (with scope +
evidence + book/chapter), each item skipped as a duplicate or strengthened in
place, and each canonical conflict held for escalation. No preamble, no trailing
questions.
