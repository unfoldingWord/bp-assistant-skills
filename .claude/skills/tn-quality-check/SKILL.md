---
name: tn-quality-check
description: Check AI-generated translation notes for quality issues including missing quotes, broken references, and style problems. Use when asked to quality-check notes, validate TN output, or review notes before delivery.
---

# Translation Note Quality Checker

Check AI-generated translation notes for quality issues before delivery. Runs mechanical checks plus a full semantic review.

## Workspace Tools Execution

Run workspace tools via the blessed CLI wrapper:

    node /app/src/workspace-tools-cli.js <tool_name> '<json-args>'

stdout is the tool result (identical to what the MCP tool returns). For args that
contain quotes, markdown, or newlines (e.g. the `note` text in update_note_text),
pass `-` as the second argument and pipe the JSON object on stdin via a heredoc.
Fallback (if Bash is unavailable): call `mcp__workspace-tools__<tool_name>` with
the same args.

**Prohibited:** Follow the shared structured-edit policy in `.claude/skills/reference/structured-edit-policy.md` — no ad-hoc scripts, no hand-`Edit` of the notes JSON/TSV, no `Edit` retries after "string to replace not found".

## Pipeline Context

If `--context <path>` is provided, read the context.json file for authoritative ULT/UST paths and persistent artifact paths. Use these instead of searching for files or writing to `/tmp/`.

## Prerequisites

- Assembled TN TSV (from tn-writer Step 5 assembly)
- prepared-notes JSON (from `runtime.preparedNotes` in context.json, or fallback path if no context)
- Plain ULT and UST USFM files (from context.json `sources.ult`/`sources.ustPlain` if available — use `ustPlain`, not `ust` which contains raw alignment markers)
- Book code (for master TN ID collision check)

## Parameters

- `<BOOK>` = uppercase 3-letter book code (e.g., `PSA`)
- `<CHAPTER>` = plain chapter number (e.g., `71`)
- `<CH>` = zero-padded chapter for filenames: 3 digits for PSA (e.g., `071`), 2 digits for other books (e.g., `03`)
- `--notes <path>` = (optional) explicit path to the notes TSV file. When provided, use this path instead of the default `output/notes/<BOOK>/<BOOK>-<CH>.tsv`.

## Locating the Notes TSV

If `--notes <path>` is provided, use that path directly.

Otherwise, look for the notes TSV in order:
1. `output/notes/<BOOK>/<BOOK>-<CH>.tsv` (standard full-chapter)
2. `output/notes/<BOOK>/<BOOK>-<CH>-vv*.tsv` (verse-range shard, e.g. `ZEC-13-vv3-9.tsv`)

If neither exists, report an error and exit.

Call the resolved path `<NOTES_TSV>`.

## Naming the Report (`<REPORT>`)

Derive the report path from `<NOTES_TSV>`'s **own basename** — never from the
chapter alone. Take the notes basename, drop the `.tsv` extension, append
`-quality.md`, and place it under `output/quality/<BOOK>/`:

| `<NOTES_TSV>`                       | `<REPORT>`                                        |
| ----------------------------------- | ------------------------------------------------- |
| `output/notes/ZEC/ZEC-13.tsv`       | `output/quality/ZEC/ZEC-13-quality.md`            |
| `output/notes/ZEC/ZEC-13-vv3-9.tsv` | `output/quality/ZEC/ZEC-13-vv3-9-quality.md`      |

A partial-chapter run reviews only its own shard, so its report **must** keep the
shard's verse-range suffix. Writing a verse-range review to the chapter-level
name (`ZEC-13-quality.md`) fails the pipeline's expected-output check and
discards the whole run's work, even though the report itself is correct (issue
#150). This mirrors `deep-issue-id`: a shard run produces the shard artifact and
nothing else — never a chapter-level file.

## Workflow

**Required final output:** Every run of this skill MUST end by (over)writing `<REPORT>` (see "Naming the Report" above) in Step 5. The pipeline checks that file's mtime against chapter start and fails the chapter as `stale_output` if it was not written in the current run, and fails it as `missing_output` if it was written under any other name. This holds even when there are no issues to fix, when Step 4 exits early, or when a report already exists from a prior run.

### Step 0: Fix Trailing Newlines

Run:

    node /app/src/workspace-tools-cli.js fix_trailing_newlines '{"file":"<NOTES_TSV>"}'

Strips any literal `\n` from the end of Note cells in-place. Run this before any other checks.

### Step 1: Run Mechanical Checks

Run (fill each value as described below):

    node /app/src/workspace-tools-cli.js check_tn_quality '{"tsvPath":"<tsvPath>","preparedJson":"<preparedJson>","ultUsfm":"<ultUsfm>","ustUsfm":"<ustUsfm>","book":"<book>","output":"<output>"}'

- `tsvPath`
- `preparedJson`
- `ultUsfm` — use `sources.ult` (plain ULT) from context.json
- `ustUsfm` — use `sources.ustPlain` (not `sources.ust`) from context.json
- `book`
- `output: runtime.tnQualityFindings` from context.json when available, otherwise `tmp/claude/tn_quality_findings.json`

Read the stderr output for a summary. Read `runtime.tnQualityFindings` from context.json when available, otherwise `tmp/claude/tn_quality_findings.json`, for full details.

### Step 2: Review Findings

Read the findings JSON. Report the summary counts (errors, warnings, clean notes). List errors first, then warnings. For each, show the reference, ID, category, and message.

### Step 3: Semantic Review

Read the full TSV and the findings JSON. For each note (especially those not flagged by the script), check the following. Write findings to the report as you go.

#### 3a. Note addresses correct issue type

Read the SupportReference column to identify the issue type (e.g., `figs-metaphor`, `figs-parallelism`). Read the note text. Verify:

- Does the note use the standard verbiage for this figure of speech? Check the style guide's Figure of Speech Verbiage table.
- A `figs-metaphor` note should discuss an image or comparison.
- A `figs-parallelism` note should describe two phrases meaning similar things.
- A `grammar-connect-*` note should identify the logical connection.

Flag notes that describe the wrong issue type.

**Do not reclassify a valid SupportReference.** Step 3a is only for flagging notes whose SupportReference is genuinely wrong. If the note's text already matches the SupportReference template and standard verbiage, leave the SupportReference alone — even if a different issue type might also plausibly apply. The quality-check pass must not overwrite a SupportReference that the issue-identification skill has correctly assigned.

**Specifically: do not change `writing-foreground` "behold" notes to `figs-exclamations`.** Per `issue-identification/figs-exclamations.md` and `issue-identification/writing-foreground.md`, "behold" calling attention to information (the vast majority of cases — "Behold, I am sending...", "behold, a man came", "And behold") is **`writing-foreground`** (speaker says "look" to foreground information). Only the rare case of "behold" expressing genuine visual surprise is `figs-exclamations`. If a note's SupportReference is `writing-foreground` and the note discusses "behold" as an attention-getter (look = listen), this is correct — do not flag it and do not reclassify it to `figs-exclamations`. Related: "Behold me" (inferior to superior) is `writing-politeness`; "Behold me" (Yahweh announcing action) is `figs-idiom`. None of these should be reclassified to `figs-exclamations` by the quality-check pass.

#### 3b. Template adherence

For each issue type, check that the note follows the template pattern. The note should read like a natural adaptation of the template, not a completely different structure. Flag notes that deviate significantly from the expected template shape.

Specifically check that fixed template phrases are preserved verbatim. For example, figs-abstractnouns uses "you could express the same idea in another way" -- flag any note that changes this to "with a verb," "using a verbal form," or other variations. Also watch for drift where one note introduces non-template wording and subsequent notes of the same type repeat that drift.

#### 3c. AT naturalness (full substitution review)

For each note with an AT: mentally substitute the AT for the gl_quote in the ULT verse. Read the full sentence. Flag any that:
- Read unnaturally or have broken grammar
- Have verb agreement problems
- Leave dangling modifiers or orphaned words at the boundary
- Don't actually resolve the translation issue
- AT introduces closing punctuation (period, comma, question mark) that is not in the gl_quote, unless the note is specifically proposing a punctuation change to the ULT

This is the semantic complement to the script's mechanical AT fit check (Check 7 + 10).

#### 3d. AT derived from ULT, not borrowed from UST

An AT should read like a targeted edit of the ULT — changing only what the note's issue requires and leaving everything else intact. The mechanical check (check 6) catches verbatim UST matches and high word overlap, but subtler borrowing slips through. For each note with an AT, check whether the AT's phrasing tracks the ULT with a focused substitution, or whether it appears to have been lifted from the UST instead. An AT that restructures the whole clause or resolves multiple issues at once is a sign of UST borrowing — the AT should only address the single issue its note describes.

#### 3e. Antithetical parallelism filtering

If a `figs-parallelism` note exists, check whether the two phrases express:
- **Similar ideas** (synonymous parallelism) -- the note is appropriate
- **Opposite ideas** (antithetical parallelism) -- the note should not exist; flag for removal

#### 3f. Note suppression opportunities

If a semantic note (idiom, metaphor, metonymy) covers the same phrase or overlapping text as a structural note (possession, activepassive) in the same verse, flag the structural note as potentially redundant. The semantic note is more informative and usually subsumes the structural one.

#### 3g. Duplicate or combinable notes

Flag notes in the same verse that:
- Address the same phrase with overlapping issue types
- Could be combined into a single note (e.g., two `grammar-connect` notes for the same connector)
- Are made redundant by another note's AT

#### 3h. "Here" rule compliance

The mechanical check (check 24) catches the most common violations. In semantic review, verify that notes flagged by check 24 are genuinely wrong (not false positives), and look for subtler cases the script may miss (e.g., "Here, **The** king..." where the bolded word starts with uppercase).

#### 3i. Restructuring quote scope

For figs-infostructure, grammar-connect-logic-goal, grammar-connect-logic-result, or any note suggesting text reordering: verify the gl_quote spans the entire area being restructured, and the AT shows the full restructured text. Flag notes where the quote captures only a fragment of the reordering.

#### 3j. Parallelism quote scope

For figs-parallelism notes: verify the gl_quote includes both complete parallel phrases, not just key words. Flag notes where only nouns or fragments are quoted. Also check whether the parallelism involves ellipsis (words implied from the other phrase) — if so, flag that a figs-ellipsis note may also be needed.

#### 3k. Cross-verse interpretive consistency

Scan for notes that reference or depend on interpretations from nearby verses. Specifically:

- **Pronoun back-references**: When a `writing-pronouns` note says "it/they/this refers to X from verse N," check that the note on verse N interprets X the same way. For example, if a v9 note says "inheritance" is a metaphor for God's people, a v10 note cannot say "it refers to the land, that is, the inheritance."
- **Carried figures**: When a note explains a metaphor or figure, and a later note references the same image, verify the interpretations match.
- **Alternate translations across verses**: When two notes address the same concept (same Hebrew word, same referent), check that their ATs are compatible. If one AT renders a term as "people" and another renders the same referent as "land," flag the conflict.

Flag inconsistencies with the specific note IDs and the conflicting interpretations so the writer can reconcile them.

#### 3l. Selectivity review

Compare the chapter's note count to the published density band for its genre (see `.claude/skills/golden-benchmark/golden/calibration.json` and the Selectivity section in `issue-identification/SKILL.md`; the budget is about 1.5x the published band). If the chapter runs over, identify the weakest notes for removal — the `remove_note` tool (via the CLI wrapper) is the fix path in Step 4. Cut first: grammar-connect-* and writing-* rows beyond a pattern's first occurrence in the chapter, then other notes a competent translator would not need. Never remove figs-activepassive notes (content-team decision: every instance gets a note).

### Step 4: Fix Issues

For each issue found in Steps 1-3, fix it directly in the source files. Do not just report — fix.

Guardrails for this step:
- Use deterministic tools first.
- If a bounded AI rescue pass is enabled by the pipeline, keep it to one pass and unresolved IDs only.
- Do not perform open-ended manual JSON surgery loops.
- Do not create recurring marker/delete-line patch workflows.

**For note text issues** (template drift, wrong verbiage, AT naturalness, "Here" rule, wrong issue type, cross-verse inconsistency):
- Run `update_note_text` via STDIN heredoc (the `note` text carries free text). Use `generatedJson` (= `runtime.generatedNotes` from context.json, or the fallback `tmp/claude/generated_notes.json`), the affected `id`, and the full replacement `note` text. Do not hand-`Edit` the JSON.

      node /app/src/workspace-tools-cli.js update_note_text - <<'JSON'
      {"generatedJson":"<generatedJson>","id":"<id>","note":"<replacement note text>"}
      JSON

**For quote boundary issues** (restructuring scope, parallelism scope, orphaned words):
- Run `update_prepared_quote` via STDIN heredoc (it carries quote slugs). Use `preparedJson` (= `runtime.preparedNotes`, or fallback `tmp/claude/prepared_notes.json`), the affected `id`, and the changed `glQuote` / `glQuoteRoundtripped` / `origQuote` fields. Do not hand-`Edit` the JSON.

      node /app/src/workspace-tools-cli.js update_prepared_quote - <<'JSON'
      {"preparedJson":"<preparedJson>","id":"<id>","glQuote":"<glQuote>","glQuoteRoundtripped":"<glQuoteRoundtripped>","origQuote":"<origQuote>"}
      JSON

**For invalid support references** (`unknown_sref` — the issue type is not in the list, e.g. an invented slug like `figs-paronomasia`):
- The SupportReference must be a valid issue type from `data/translation-issues.csv`. Re-select the correct one rather than deleting the note — Hebrew wordplay / sound play (words from the same root) is `writing-poetry`, not a `figs-paronomasia` of its own.
- Set the corrected slug with `update_prepared_quote` via STDIN heredoc, passing the affected `id` and the `sref` field (e.g. `sref: "writing-poetry"`). If the note text was written for the wrong type, also fix it with `update_note_text`.

      node /app/src/workspace-tools-cli.js update_prepared_quote - <<'JSON'
      {"preparedJson":"<preparedJson>","id":"<id>","sref":"writing-poetry"}
      JSON

**For removal** (antithetical parallelism notes, redundant structural notes, over-budget notes from the selectivity review):
- Run `remove_note` via STDIN heredoc with the `id`, `generatedJson` (= `runtime.generatedNotes`), and `tsvFile` (the assembled TSV) — it drops the entry from the JSON and the matching TSV row in one call.

      node /app/src/workspace-tools-cli.js remove_note - <<'JSON'
      {"id":"<id>","generatedJson":"<generatedJson>","tsvFile":"<tsvFile>"}
      JSON

After any changes to the generated-notes JSON or prepared-notes JSON, re-run assembly and post-processing once:

Re-assemble, then run curly-quote post-processing (`inPlace: true`):

    node /app/src/workspace-tools-cli.js assemble_notes '{"preparedJson":"<runtime.preparedNotes>","generatedJson":"<runtime.generatedNotes>","output":"<NOTES_TSV>"}'
    node /app/src/workspace-tools-cli.js curly_quotes '{"input":"<NOTES_TSV>","inPlace":true}'

After fixing, you may re-run `check_tn_quality` **at most once** to verify the fixes landed. If issues persist after that one re-check, add them to the quality report as "unresolved — needs manual review" and continue to Step 5. Do not run a third check cycle. "Stop" here means stop the re-check loop, not the skill — Step 5 still runs.

### Step 5: Write Report (mandatory — do not skip)

**This step is unconditional.** Every invocation of tn-quality-check MUST end by writing (overwriting) the report file below in the current run. Skipping Step 5 — because "nothing needed fixing," because you already wrote it earlier in the run, because you thought you were done after Step 4, or because a report already exists on disk — causes the pipeline's post-run freshness check to raise `stale_output` and fail the chapter (see issue #115). A pre-existing file at this path from a prior run is **not** proof that this step ran; the pipeline compares the file's mtime against chapter start.

Write the final quality report to `<REPORT>` — the path derived from `<NOTES_TSV>`'s basename in "Naming the Report" above — as the final action of this skill (after any fixes, re-checks, or early exits). For a verse-range shard this filename carries the `-vv<START>-<END>` suffix; do not shorten it to the chapter name.

```markdown
# TN Quality Report: <BOOK> <CHAPTER>          <!-- add " (verses <START>-<END>)" for a shard run -->

## Summary
- Notes checked: N
- Errors found: N (all fixed)
- Warnings: N
- Clean: N

## Fixes Applied
[for each fix: reference, ID, what was wrong, what was changed]

## Remaining Warnings
[warnings not fixed, with rationale for leaving them]

## Semantic Review
[findings from Step 3 grouped by category, noting which were fixed]
```

## Mechanical Checks Reference

The script runs these checks:

```
 #  Category                        Severity    What it checks
 1  id_format                       error       ID matches [a-z][a-z0-9]{3}
 2  id_duplicate                    error       No duplicate IDs in file
 3  id_collision                    error       No ID collisions with master TN on Door43
 4  empty_quote / no_hebrew         error       Quote column has Hebrew characters
 5  at_syntax                       error       ATs use [square brackets]
 6  at_matches_ust                  error       AT text appears verbatim in UST (exact substring match)
 6b at_not_ust                      warning     AT text has >85% word overlap with UST phrasing
 7  gl_quote_not_in_ult             error       gl_quote appears in ULT verse (expected for discontinuous quotes using ... notation)
 8  bold_not_in_ult                 error       Bolded text appears verbatim in ULT verse
 9  rc_link_in_note                 error       Note column has no rc:// links
17  unknown_sref                    error       SupportReference issue type exists in data/translation-issues.csv (no invented slugs like figs-paronomasia)
10  orphaned_conjunction/prep       warning     No orphaned words before AT in substitution
10b dropped_conjunction             warning     gl_quote starts with conjunction but AT drops it
11  writer_in_psalms                warning     PSA: use attributed name or "the psalmist", never "the writer" or "the author"
12  straight_quotes                 warning     No straight quote characters
13  at_capitalization               warning     AT capitalization matches sentence position
14  abstract_noun_in_at             error       figs-abstractnouns AT must not contain abstract nouns
15  at_ending_punctuation           warning     AT does not introduce ending punctuation absent from gl_quote (skips figs-rquestion ? -> ./!)
16  narrow_parallelism_quote        warning     figs-parallelism gl_quote covers both full parallel phrases
20  multiverse_language             warning     Note text references multiple verses (e.g., "verses 2, 5, and 6")
20  multiverse_backref              warning     Note back-references another verse (e.g., "as in verse 3")
20  multiverse_duplicate            warning     Near-duplicate notes (same issue type, adjacent verses, 75%+ content overlap)
21  rquestion_missing_punctuation   warning     figs-rquestion AT should end with . or ! (not ? or bare)
22  missing_at                      error       Note must include Alternate translation when template requires one
23  single_quotes                   error       Single quotes must not be used as quotation marks (use double curly quotes; single apostrophe only for possessives)
24  here_rule                       warning     Note starts with "Here" — next content must be a bolded lowercase quote (not "Here David is saying...")
25  template_phrase_missing         warning     figs-abstractnouns/rquestion/metaphor notes include expected fixed template phrase
25c self_talk_leak                  warning     Note may contain model deliberation instead of note text ("wait, actually...", first person, template sub-type names)
25c preamble_paragraph              warning     Multi-paragraph note whose first paragraph lacks the template phrase — possible preamble before the real note
```

**Note on `self_talk_leak` / `preamble_paragraph`**: these catch the model reasoning out loud inside the Note column (MIC 5:7, 2026-08-03). They are warnings by design — an editor rewriting one leaked note is far cheaper than a blocked push losing a chapter of notes. The pattern set was tuned to zero false positives across 368 published notes (JOS 1/3, MAL 1, NAM 1, and tn_OBA).

Two candidate patterns were tried and deliberately removed, because they match canonical published note wording: a bare "actually", and "This is a/an <figure>" — the latter flagged 3.3% of Obadiah, whose standard phrasing is exactly "This is an idiom that means...". If you are tempted to widen these patterns, measure against published notes first; the repair pass deletes what the detector flags, so a false positive here costs real note content.

These two findings are the only ones with an **automatic repair pass**. `repairSelfTalkNotes` in `notes-pipeline.js` runs right after the mechanical check: each flagged note goes back to the model alone with its template, asking for the note text only. A rewrite is accepted only if it is no longer than the original, reads clean, and — when a template could be resolved for that note — still contains the template's fixed phrase. Otherwise the original is kept and the row is tagged `ISSUE:SELF_TALK` in the Tags column. Rows with no generated text (chapter intros, failed generations) are tagged rather than repaired, and anything past the 25-note-per-chapter repair cap is tagged too. The check then re-runs, so the findings you read reflect the repaired text.

So by the time you see one of these warnings in Step 1, repair has already been attempted and failed the gate — treat a surviving `self_talk_leak` (or an `ISSUE:SELF_TALK` tag) as needing a hand-written fix, not another automated attempt.

**Note on orphaned preposition/conjunction warnings after gl_quote expansion**: When a gl_quote has been expanded to include a leading preposition or conjunction (the correct fix for orphaned words at the AT boundary), the script may still report `orphaned_conjunction` or `orphaned_prep` warnings. These are false positives -- the word now appears both in the expanded gl_quote and at the start of the AT, which is the intended behavior. During the deep semantic review (Step 3c), verify the actual substitution reads naturally rather than trusting these warnings at face value.

## When to Run

- After every tn-writer iteration (Step 5 assembly, Step 7 final review; AT generation happens in the pipeline)
- Before final delivery (full quality gate)
- After parallel-batch merge (catch cross-chunk issues)

Door43 CI validation runs separately as part of repo-insert, not here.
