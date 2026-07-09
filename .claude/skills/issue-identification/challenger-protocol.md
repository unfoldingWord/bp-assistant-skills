# Challenger Protocol

The challenger is spawned as a teammate (`model: "sonnet"`, name: "challenger")
after all Wave 2 analysts confirm their files are written.

## Challenge Phase

The Challenger:
1. Reads all wave 2 TSVs
2. Identifies issues to challenge (misclassifications, missed overlaps,
   ULT coherence failures)
3. Groups challenges by analyst
4. Sends one batch DM to each analyst with their challenges

## Challenge Criteria

- Is this the right issue type? Could it be a commonly confused alternative?
  Tests: metaphor vs metonymy, doublet vs hendiadys, idiom vs metaphor,
  doublet vs parallelism (see Commonly Confused table in
  `skills/issue-identification/SKILL.md`)
- Cross-references `data/issues_resolved.txt` and the biblical imagery
  classification lists in figs-metonymy.md and figs-metaphor.md
- Does the same phrase carry multiple figurative tags? If so, these are
  competing analyses -- challenge all but the best fit using the decision
  hierarchy in "Competing Figurative Analyses" in SKILL.md.
- Does NOT find new issues -- only challenges existing ones
- Resolves disagreements between Wave 2 agents (e.g., one kept an issue
  another dropped)
- Identifies duplicates where multiple agents flagged the same issue
- **Is the issue noteworthy?** Beyond classification, challenge on translator
  need: would a competent translator plausibly err here without a note? Issues
  that fail this bar are TRIVIAL and can be challenged for dropping even when
  correctly classified. Prime candidates: repeat occurrences of a formulaic
  marker already flagged earlier in the chapter, and discourse-family notes
  (grammar-connect-*, writing-*) beyond the genre's published base rate (see
  the Selectivity section in `skills/issue-identification/SKILL.md`).
- **Grammar issues are independent**: Abstract nouns (figs-abstractnouns) and
  passives (figs-activepassive) are systematically detected (abstract nouns
  by script, passives during verse-by-verse analysis) and AI-verified. They
  cannot be subsumed by, merged into, or dropped in favor of figurative issues
  on the same phrase — and figs-activepassive issues are never dropped
  (content-team decision: every instance gets a note). Other
  grammar-level issues (figs-possession, figs-ellipsis, figs-nominaladj)
  should not be dropped or merged in favor of figurative issues on the same
  phrase, though they remain subject to the noteworthiness bar on their own
  merits.

## Defend Phase

Each analyst wakes up, reads their challenges, and sends a defense DM back to
the Challenger. One round only -- no infinite back-and-forth.

## Ruling Phase

The Challenger reads all defenses and makes final rulings for each challenged
issue: **KEEP**, **DROP**, **RECLASSIFY**, or **MERGE_DUPLICATE**. DROP is a
valid ruling on translator-need grounds alone — a correctly classified issue
that a competent translator would handle unaided does not earn a note.

After writing rulings to `$TMP/wave3_challenges.tsv`, the Challenger sends a
DM to each analyst confirming rulings are complete.
