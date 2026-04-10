---
name: tn-quality-check
description: Check AI-generated translation notes for quality issues including missing quotes, broken references, and style problems. Use when asked to quality-check notes, validate TN output, or review notes before delivery.
---

# Translation Note Quality Checker

Check AI-generated translation notes for quality issues before delivery. Runs mechanical checks plus a full semantic review.

## MCP-First Execution

In restricted runs, use workspace MCP tools instead of direct shell/python commands:
- `mcp__workspace-tools__fix_trailing_newlines`
- `mcp__workspace-tools__check_tn_quality`
- `mcp__workspace-tools__assemble_notes`
- `mcp__workspace-tools__curly_quotes`

## Pipeline Context

If `--context <path>` is provided, read the context.json file for authoritative ULT/UST paths (`sources.ult`, `sources.ust`) and persistent artifact paths (`runtime.preparedNotes`, `runtime.generatedNotes`, `runtime.tnQualityFindings`). Use these instead of searching for files or writing to `/tmp/`.

## Prerequisites

- Assembled TN TSV (from tn-writer Step 8-9)
- prepared-notes JSON (from `runtime.preparedNotes` in context.json, or fallback path if no context)
- Plain ULT and UST USFM files (from context.json `sources.ult`/`sources.ust` if available)
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
2. `output/notes/<BOOK>/<BOOK>-<CH>-v*.tsv` (verse-range variant, e.g. `HAB-03-v1-2.tsv`)

If neither exists, report an error and exit.

## Workflow

### Step 0: Fix Trailing Newlines

Use `mcp__workspace-tools__fix_trailing_newlines` with `file: <NOTES_TSV>`.

Strips any literal `\n` from the end of Note cells in-place. Run this before any other checks.

### Step 1: Run Mechanical Checks

Use `mcp__workspace-tools__check_tn_quality` with:
- `tsvPath`
- `preparedJson`
- `ultUsfm`
- `ustUsfm`
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

### Step 4: Fix Issues

For each issue found in Steps 1-3, fix it directly in the source files. Do not just report — fix.

Guardrails for this step:
- Use deterministic tools first.
- If a bounded AI rescue pass is enabled by the pipeline, keep it to one pass and unresolved IDs only.
- Do not perform open-ended manual JSON surgery loops.
- Do not create recurring marker/delete-line patch workflows.

**For note text issues** (template drift, wrong verbiage, AT naturalness, "Here" rule, wrong issue type, cross-verse inconsistency):
- Edit the generated-notes path from context.json (`runtime.generatedNotes`) or the fallback `tmp/claude/generated_notes.json` — update the note text for the affected ID(s).

**For quote boundary issues** (restructuring scope, parallelism scope, orphaned words):
- Edit the prepared-notes path from context.json (`runtime.preparedNotes`) or the fallback `tmp/claude/prepared_notes.json` — update `gl_quote`, `gl_quote_roundtripped`, and `orig_quote` for the affected item(s).

**For removal** (antithetical parallelism notes, redundant structural notes):
- Remove the row from the assembled TSV directly. Also remove the entry from the generated-notes JSON.

After any changes to the generated-notes JSON or prepared-notes JSON, re-run assembly and post-processing once:

Re-assemble with `mcp__workspace-tools__assemble_notes`, then run `mcp__workspace-tools__curly_quotes` (`inPlace: true`).

After fixing, you may re-run `check_tn_quality` **at most once** to verify the fixes landed. If issues persist after that one re-check, add them to the quality report as "unresolved — needs manual review" and stop. Do not run a third check cycle.

### Step 5: Write Report

Write the final quality report to `output/quality/<BOOK>/<BOOK>-<CH>-quality.md`:

```markdown
# TN Quality Report: <BOOK> <CHAPTER>

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
```

**Note on orphaned preposition/conjunction warnings after gl_quote expansion**: When a gl_quote has been expanded to include a leading preposition or conjunction (the correct fix for orphaned words at the AT boundary), the script may still report `orphaned_conjunction` or `orphaned_prep` warnings. These are false positives -- the word now appears both in the expanded gl_quote and at the start of the AT, which is the intended behavior. During the deep semantic review (Step 3c), verify the actual substitution reads naturally rather than trusting these warnings at face value.

## When to Run

- After every tn-writer iteration (Step 7 AT fit cycle, Step 8 assembly)
- Before final delivery (full quality gate)
- After parallel-batch merge (catch cross-chunk issues)

Door43 CI validation runs separately as part of repo-insert, not here.
