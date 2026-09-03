# STATE.md — bp-assistant-skills

What this project **is**: the durable gotchas and lessons that do not live in
the skill files or git history. Read it before non-trivial work. Never a
session log — what you just did belongs in the commit message and PR body.

## Gotchas

- **Golden fixtures are CRLF.** `scripts/score_benchmark.mjs` `parseTnRows`
  must split on `\r?\n`; splitting on `\n` alone left a stray `\r` on the header's
  last field and silently emptied every `note` field for all convention checks
  (fixed 2026-09-02).
- **Some skill files have mixed CRLF/LF line endings** (`writing-pronouns.md`,
  `figs-gendernotations.md`). Editor tools normalize untouched lines and produce
  large phantom diffs. Check `git diff --ignore-cr-at-eol` against `git diff`
  before committing and rewrite byte-for-byte if they differ.
- **`score_benchmark.mjs` convention-problem counts from before 2026-09-02 are
  not comparable with later runs.** The CRLF bug above had emptied every note
  field, so the template-phrase convention checks (e.g. "figs-abstractnouns
  note missing template phrase") were guaranteed false positives, not real
  findings.

## Lessons learned

- **The model never writes "see how" notes.** Pointers and "This also occurs in
  verses …" lists are generated deterministically by bp-assistant
  (`recurrence-index.js`, `runSeeHowDetection`) from `prepared_notes.json`
  fields `programmatic_note` and `also_occurs_verses`. issue-identification
  flags the first occurrence of a repeated phrase only; tn-writer uses the
  programmatic sentence verbatim. Any skill text that asks the model to write
  its own pointer is a regression.
- **`seeHowSharePct` in the golden benchmark is reported, not gated.** The
  see-how rule is the spec; the metric exists to make drift visible.

## Escalated

- None.
