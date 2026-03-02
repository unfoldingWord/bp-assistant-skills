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
- **Grammar issues are independent**: Abstract nouns (figs-abstractnouns) and
  passives (figs-activepassive) are script-detected and AI-verified. They
  cannot be subsumed by, merged into, or dropped in favor of figurative issues
  on the same phrase. Keep both layers. Other grammar-level issues
  (figs-possession, figs-ellipsis, figs-nominaladj) should also generally not
  be dropped or merged with figurative issues.

## Defend Phase

Each analyst wakes up, reads their challenges, and sends a defense DM back to
the Challenger. One round only -- no infinite back-and-forth.

## Ruling Phase

The Challenger reads all defenses and makes final rulings for each challenged
issue: **KEEP**, **DROP**, **RECLASSIFY**, or **MERGE_DUPLICATE**.

After writing rulings to `$TMP/wave3_challenges.tsv`, the Challenger sends a
DM to each analyst confirming rulings are complete.
