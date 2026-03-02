# Merge Procedure

Merge all Wave 2 findings after Wave 3 rulings.

## Steps

1. **Apply rulings**: Wave 3 challenge outcomes override Wave 2 classifications
   (KEEP, DROP, RECLASSIFY, MERGE_DUPLICATE).
2. **Deduplicate**: Same phrase + same issue type = duplicate (drop one).
   Different issue types on the same phrase are NOT duplicates -- keep both,
   UNLESS they are competing figurative analyses (see rule 4).
3. **Grammar independence**: Grammar issues (abstract nouns, passives,
   possession, ellipsis, nominaladj) always survive alongside figurative issues
   on the same phrase.
4. **Figurative exclusivity**: When the same phrase has multiple figurative
   issue types (e.g., figs-synecdoche + figs-metonymy + figs-idiom), keep
   only the single best fit per the decision hierarchy in
   `skills/issue-identification/SKILL.md`. Does not override rule 3.
5. **Order**: First-to-last by ULT position within each verse,
   longest-to-shortest when phrases nest.
6. **Output format**: Enforce the output format guardrail -- brief classification
   hints only (see `agents/issue-identification.md` lines 9-31).

## Final Check

Before writing to the output path, verify ordering within each verse:
first-to-last by ULT position, longest-to-shortest when phrases nest.
