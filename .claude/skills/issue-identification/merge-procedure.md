# Merge Procedure

Merge all Wave 2 findings after Wave 3 rulings.

## Steps

1. **Apply rulings**: Wave 3 challenge outcomes override Wave 2 classifications
   (KEEP, DROP, RECLASSIFY, MERGE_DUPLICATE).
2. **Deduplicate**: Same phrase + same issue type = duplicate (drop one).
3. **One issue per phrase**: Set aside figs-explicit and figs-ellipsis rows
   and keep them (content-team decision 2026-10-01: lean toward these for
   second-language editors). Then group the remaining issues in a verse whose
   ULT quotes are the same or overlap. Each group keeps one issue:
   figs-activepassive if present (content-team decision: every instance gets a
   note), else writing-foreground on "behold", else the type in the highest
   tier below. Keep a second issue in the group only when it is a different
   layer from the kept one (grammar beside a figure, or a figure beside
   grammar) AND its type is in tier A. Drop the rest. figs-activepassive is
   never dropped.
   - **Tier A** (editors keep 85%+): figs-merism, figs-metaphor, figs-simile,
     figs-exclamations, figs-metonymy.
   - **Tier B** (editors keep 70-84%; also any type not listed): figs-doublet,
     figs-idiom, translate-symaction, figs-imperative, figs-personification,
     grammar-connect-logic-result.
   - **Tier C** (editors keep under 70%): figs-abstractnouns, figs-rquestion,
     figs-parallelism, writing-pronouns, figs-nominaladj, figs-possession.

   Tiers come from the editor-history rows in
   `data/quick-ref/issue_decisions.csv`; a book-specific row there overrides
   the ALL tier for that book. Two figurative types on one phrase are competing
   analyses: keep the best fit per the decision hierarchy in
   `skills/issue-identification/SKILL.md`, not both.
4. **Hard density ceiling**: Ceiling = verses x 1.2 x the genre's
   `chapterDensity.median` in `golden-benchmark/golden/calibration.json`
   (about 3.1/verse narrative, 3.7 poetry, 5.2 prophecy). Use the chapter's own
   genre: a narrative chapter in a prophetic book uses narrative. Above the
   ceiling, drop the lowest-confidence rows until the count is at or under it.
   Drop tier C first, then tier B, then tier A. Within a tier, drop first the
   discourse-family rows (grammar-connect-*, writing-*), then rows only one
   analyst raised or the challenger reclassified. Never drop figs-activepassive,
   "behold", figs-explicit or figs-ellipsis rows to meet the ceiling. The
   ceiling is a limit, not a target: below it, still cut rows a competent
   translator would handle unaided.
5. **Order**: First-to-last by ULT position within each verse,
   longest-to-shortest when phrases nest.
6. **Output format**: Enforce the output format guardrail -- brief classification
   hints only (see `agents/issue-identification.md` lines 9-31).

## Final Check

Before writing to the output path, verify ordering within each verse:
first-to-last by ULT position, longest-to-shortest when phrases nest.
