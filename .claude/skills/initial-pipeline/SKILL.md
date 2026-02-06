---
name: initial-pipeline
description: Orchestrate ULT-gen, issue-id, and UST-gen as a coordinated team for a chapter. 6-wave pipeline with adversarial issue identification and ULT feedback loop.
---

# Initial Pipeline Orchestrator

Coordinates ULT-gen, issue-id, and UST-gen as a single team for a chapter.

## Inputs

- **Book**: 3-letter abbreviation (PSA, GEN, 2SA, etc.)
- **Chapter**: number

## Why Run Together

These three stages benefit from cross-checking:
- Issue-id catches ULT rendering problems early (before human review)
- ULT revisions from issue-id feedback improve the literal text
- UST is generated AFTER issue-id so it can model how to handle the identified issues
- Nobody works in isolation -- the stages inform each other

## Team Composition

### Wave 1: ULT Draft
- **ULT-gen agent**: Translates Hebrew to literal English for the chapter

UST is NOT generated here. UST needs the issue-id output to know what
translation issues exist so it can model handling them. 

### Wave 2: Issue Identification (4 agents, parallel, adversarial)

All four agents read the ULT draft from wave 1. Each works independently but
all are constantly checking each other's work -- reading each other's output,
questioning classifications, and flagging disagreements. Use `build_tn_index.py --lookup` and `--issue` for precedent lookups instead of raw grep against published TNs. If one agent calls
something a metaphor and another calls it metonymy, that conflict should be
surfaced, not silently ignored.

- **Discourse Analyst**: Macro-level grammar and structure. Discourse markers,
  participant tracking, paragraph structure, connectors between clauses,
  quotation structure, genre indicators. Focuses on writing-* and
  grammar-connect-* issue types.

- **Grammar Analyst**: Micro-level grammar within clauses. Passives, abstract
  nouns, possession, pronouns, ellipsis, word-level syntax. Focuses on
  figs-activepassive, figs-abstractnouns, figs-possession, writing-pronouns,
  figs-ellipsis, and similar word/phrase-level issues.

- **Figurative Language Analyst**: Figures of speech. Metaphor, metonymy,
  simile, synecdoche, personification, merism, hendiadys, doublet, idiom.
  Cross-references the biblical imagery classification lists in figs-metonymy.md
  and figs-metaphor.md. Focuses on figs-* issue types.

- **Speech Acts & Literary Analyst**: Rhetorical devices and speech acts.
  Rhetorical questions, imperatives, exclamations, irony, hyperbole, litotes,
  euphemism, poetry markers, parallelism. Focuses on figs-rquestion,
  figs-imperative, figs-exclamations, figs-hyperbole, writing-poetry, and
  figs-parallelism.

Each agent has a primary domain but overlaps with the others. When agents
identify the same phrase, they should compare classifications. Disagreement
is productive -- it's better to surface a conflict than to let a wrong
classification pass unchallenged.

### Wave 3: Challenge and Defend (after wave 2)

This is a debate, not a one-sided review. The Challenger questions classifications
and the wave 2 agents defend their work. If an agent can't justify a classification,
it gets revised. If the agent makes a compelling case, the classification stands.

- **Classification Challenger**: For every classification from wave 2, checks:
  - Is this the right issue type? Could it be a commonly confused alternative?
  - Tests: metaphor vs metonymy, doublet vs hendiadys, idiom vs metaphor, doublet vs parallelism
  - Cross-references issues_resolved and the biblical imagery classification lists
  - Does NOT find new issues -- only challenges existing ones
  - Pays special attention to disagreements surfaced in wave 2
- **Wave 2 agents defend**: When challenged, the original agent argues for their
  classification with evidence from the text, published TNs, or issues_resolved.
  The Challenger can accept the defense or escalate to the Merger (wave 4a).
- **ULT Reviewer**: Cross-checks issue-id output against ULT rendering:
  - figs-infostructure candidates: Is the Hebrew word order structurally significant?
    If not, flag the ULT for adjustment and drop the note.
  - figs-possession and grammar notes: Does the ULT preserve the Hebrew structure
    the note is about?
  - Heuristic: If Hebrew has a named grammatical structure (construct chain, passive, etc.),
    ULT should preserve it literally. If it's just word order with no structural name,
    ULT can use natural English.

### Wave 4a: Merge
- **Translational Decision Advisor**: Merges wave 2 findings, applies wave 3 feedback,
  resolves conflicts, produces final issues TSV.

### Wave 4b: Apply ULT Revisions
- Apply the ULT Reviewer's changes to the ULT draft.
- Produces the revised ULT (draft 2).

### Wave 5: Verification
- Wave 2 agents (or a subset) re-check their findings against the revised ULT.
- Anything that no longer applies after the ULT revision gets dropped.
- Anything new introduced by the revision gets flagged.

### Wave 6: UST Generation
- **UST-gen agent**: Creates simplified translation from T4T, informed by:
  - The final revised ULT (draft 2)
  - The final issues TSV
  - The UST Strong's index (`build_ust_index.py --lookup`/`--compare`) for published UST rendering precedent
  - UST models how to handle each identified issue -- it shows the translator
    what the text means in natural language, with figures unpacked, implicit
    info made explicit, passives made active, etc.

## Flow

```
Wave 1:   ULT-gen ─────────────────────────────────────────────┐
                                                               │
Wave 2:   Discourse Analyst ───┐                               │
          Grammar Analyst ─────┤ (all read ULT draft,          │
          Figurative Lang. ────┤  check each other's work,     │
          Speech Acts/Lit. ────┘  surface disagreements)        │
                                                               │
Wave 3:   Challenger ──────┐ (challenges, wave 2 defends)       │
          ULT Reviewer ────┘ (checks ULT vs issues)            │
                                                               │
Wave 4a:  Merger ──────────── (final issues TSV)               │
Wave 4b:  ULT Revision ───── (applies changes -> ULT draft 2) │
                                                               │
Wave 5:   Verification ───── (wave 2 re-checks against        │
                               revised ULT, drop/add)          │
                                                               │
Wave 6:   UST-gen ─────────── (reads final ULT + issues,      │
                               models issue handling)          │
```

## Outputs

1. `output/AI-ULT/<BOOK>-<CHAPTER>.usfm` -- revised ULT (draft 2, post-issue-id feedback)
2. `output/AI-UST/<BOOK>-<CHAPTER>.usfm` -- UST (informed by issues)
3. `output/issues/<BOOK>-<CHAPTER>.tsv` -- verified issues (post-ULT-revision check)

## Lessons Learned (PSA 61)

- **Coverage vs accuracy**: Parallel independent analysis (wave 2) optimizes for coverage.
  Adversarial review (wave 3) optimizes for accuracy. Differentiating the wave 2 agents
  by domain and having them check each other gives both.
- **Heart classification**: Without a challenger, a wrong skill file entry (heart = metaphor)
  went unchallenged. The challenger agent cross-references authoritative lists.
- **ULT/issue-id coherence**: Two failure modes:
  1. ULT unnecessarily preserves Hebrew form -> adjust ULT, drop note (PSA 61:2 word order)
  2. ULT incorrectly flattens Hebrew structure -> correct ULT, keep note (PSA 61:3 construct)
  Wave 4b handles both by revising the ULT, and wave 5 verifies the issues still hold.
- **UST after issue-id**: UST generated in isolation can't model issue handling. Generating
  it after issue-id means it can show translators what each figure/construction means in
  plain language.
- **Note ordering**: Within each verse, first-to-last by ULT position, longest-to-shortest
  when phrases nest. Issue-id should output in this order; assemble_notes.py enforces it.