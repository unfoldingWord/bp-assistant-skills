---
name: tn-quality-check
description: Check AI-generated translation notes for quality issues including missing quotes, broken references, and style problems. Use when asked to quality-check notes, validate TN output, or review notes before delivery.
---

# Translation Note Quality Checker

Check AI-generated translation notes for quality issues before delivery. Two modes: fast (script only, mechanical checks) and deep (script + semantic review).

## Prerequisites

- Assembled TN TSV (from tn-writer Step 8-9)
- `prepared_notes.json` (from tn-writer Step 2a)
- Plain ULT and UST USFM files
- Book code (for master TN ID collision check)

## Parameters

- `<BOOK>` = uppercase 3-letter book code (e.g., `PSA`)
- `<CHAPTER>` = plain chapter number (e.g., `71`)
- `<CH>` = zero-padded chapter for filenames: 3 digits for PSA (e.g., `071`), 2 digits for other books (e.g., `03`)

## Workflow

### Step 1: Run Mechanical Checks

```bash
python3 .claude/skills/tn-quality-check/scripts/check_tn_quality.py \
    output/notes/<BOOK>/<BOOK>-<CH>.tsv \
    --prepared-json /tmp/claude/prepared_notes.json \
    --ult-usfm /tmp/claude/ult_plain.usfm \
    --ust-usfm /tmp/claude/ust_plain.usfm \
    --book <BOOK> \
    --output /tmp/claude/tn_quality_findings.json
```

Read the stderr output for a summary. Read `/tmp/claude/tn_quality_findings.json` for full details.

### Step 2: Review Findings (fast mode stops here)

Read the findings JSON. Report the summary counts (errors, warnings, clean notes).

For **fast mode** (`--fast` or when the user just wants a quick check): stop here and report the findings. List errors first, then warnings. For each, show the reference, ID, category, and message.

If no errors and no warnings, report the notes as clean.

### Step 3: Semantic Review (deep mode only)

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

This is the semantic complement to the script's mechanical AT fit check (Check 7 + 10).

#### 3d. Antithetical parallelism filtering

If a `figs-parallelism` note exists, check whether the two phrases express:
- **Similar ideas** (synonymous parallelism) -- the note is appropriate
- **Opposite ideas** (antithetical parallelism) -- the note should not exist; flag for removal

#### 3e. Note suppression opportunities

If a semantic note (idiom, metaphor, metonymy) covers the same phrase or overlapping text as a structural note (possession, activepassive) in the same verse, flag the structural note as potentially redundant. The semantic note is more informative and usually subsumes the structural one.

#### 3f. Duplicate or combinable notes

Flag notes in the same verse that:
- Address the same phrase with overlapping issue types
- Could be combined into a single note (e.g., two `grammar-connect` notes for the same connector)
- Are made redundant by another note's AT

#### 3g. "Here" rule compliance

If a note starts with "Here, ", verify the next content is a **bolded quote from the verse** starting with a lowercase letter. Flag violations like "Here David is saying..." or "Here the author is speaking..."

### Step 4: Write Report

Write the final quality report to `output/quality/<BOOK>/<BOOK>-<CH>-quality.md`:

```markdown
# TN Quality Report: <BOOK> <CHAPTER>

## Summary
- Notes checked: N
- Errors: N
- Warnings: N
- Clean: N

## Errors
[list each error with reference, ID, category, message]

## Warnings
[list each warning]

## Semantic Review (deep mode)
[findings from Step 3, grouped by category]

## Recommended Fixes
[for each error/warning, suggest the specific fix]
```

## Mechanical Checks Reference

The script runs these 13 checks:

| # | Category | Severity | What it checks |
|---|----------|----------|----------------|
| 1 | id_format | error | ID matches `[a-z][a-z0-9]{3}` |
| 2 | id_duplicate | error | No duplicate IDs in file |
| 3 | id_collision | error | No ID collisions with master TN on Door43 |
| 4 | empty_quote / no_hebrew | error | Quote column has Hebrew characters |
| 5 | at_syntax | error | ATs use `[square brackets]` |
| 6 | at_matches_ust | error/warn | AT text is not identical to UST phrasing |
| 7 | gl_quote_not_in_ult | error | gl_quote appears in ULT verse (expected for discontinuous quotes using `...` notation) |
| 8 | bold_not_in_ult | error | Bolded text appears verbatim in ULT verse |
| 9 | rc_link_in_note | error | Note column has no `rc://` links |
| 10 | orphaned_conjunction/prep | warning | No orphaned words before AT in substitution |
| 11 | writer_in_psalms | warning | Uses "the psalmist", not "the writer" (PSA only) |
| 12 | straight_quotes | warning | No straight quote characters |
| 13 | at_capitalization | warning | AT capitalization matches sentence position |

**Note on orphaned preposition/conjunction warnings after gl_quote expansion**: When a gl_quote has been expanded to include a leading preposition or conjunction (the correct fix for orphaned words at the AT boundary), the script may still report `orphaned_conjunction` or `orphaned_prep` warnings. These are false positives -- the word now appears both in the expanded gl_quote and at the start of the AT, which is the intended behavior. During the deep semantic review (Step 3c), verify the actual substitution reads naturally rather than trusting these warnings at face value.

## When to Run

- **Fast mode**: After every tn-writer iteration (Step 7 AT fit cycle, Step 8 assembly). Quick sanity check.
- **Deep mode**: Before final delivery. Full quality gate.
- **After parallel-batch merge**: Run on the merged TSV to catch cross-chunk issues.
