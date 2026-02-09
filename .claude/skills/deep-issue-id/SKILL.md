---
name: deep-issue-id
description: Multi-agent adversarial issue identification against human ULT/UST from Door43 master. 4 parallel domain analysts + challenger debate, without AI text generation.
---

# Deep Issue Identification (Human ULT/UST)

Adversarial multi-agent issue identification against human-authored ULT/UST from repo master. Same analytical depth as initial-pipeline waves 2-3-4a, but skips AI text generation since the human text already exists.

## Inputs

- **Book**: 3-letter abbreviation (PSA, GEN, 2SA, etc.)
- **Chapter**: number

## Setup (orchestrator runs directly)

### 1. Fetch and Parse

```bash
python3 .claude/skills/utilities/scripts/fetch_door43.py <BOOK> > /tmp/claude/book_ult.usfm
python3 .claude/skills/utilities/scripts/fetch_door43.py <BOOK> --type ust > /tmp/claude/book_ust.usfm 2>/dev/null || true

node .claude/skills/utilities/scripts/usfm/parse_usfm.js /tmp/claude/book_ult.usfm \
  --chapter <N> \
  --output-json /tmp/claude/alignments.json \
  --output-plain /tmp/claude/ult_plain.usfm

node .claude/skills/utilities/scripts/usfm/parse_usfm.js /tmp/claude/book_ust.usfm \
  --plain-only > /tmp/claude/ust_plain.usfm 2>/dev/null || true
```

### 2. Compare ULT/UST

```bash
python3 .claude/skills/issue-identification/scripts/compare_ult_ust.py \
  /tmp/claude/ult_plain.usfm /tmp/claude/ust_plain.usfm \
  --chapter <N> --output /tmp/claude/ult_ust_diff.tsv
```

### 3. Run Automated Detection

```bash
python3 .claude/skills/issue-identification/scripts/detection/detect_activepassive.py \
  /tmp/claude/alignments.json --format tsv > /tmp/claude/detected_issues.tsv

python3 .claude/skills/issue-identification/scripts/detection/detect_abstract_nouns.py \
  /tmp/claude/alignments.json --format tsv >> /tmp/claude/detected_issues.tsv
```

### 4. Build Published TN Index

```bash
python3 .claude/skills/issue-identification/scripts/build_tn_index.py <BOOK> <N>
```

Use `--lookup` and `--issue` for precedent lookups during analysis (not raw grep).

## Wave 2: Issue Identification (4 agents, parallel, adversarial)

Spawn 4 Task agents (`subagent_type: "issue-identification"`). Each agent reads:
- Human ULT (`/tmp/claude/ult_plain.usfm`)
- Human UST (`/tmp/claude/ust_plain.usfm`) if available
- Alignment JSON (`/tmp/claude/alignments.json`)
- ULT/UST divergence patterns (`/tmp/claude/ult_ust_diff.tsv`)
- Automated detections (`/tmp/claude/detected_issues.tsv`)

Each works independently but all cross-check each other's work, reading each other's output, questioning classifications, and surfacing disagreements.

### Discourse Analyst
Macro-level grammar and structure. Discourse markers, participant tracking, paragraph structure, connectors between clauses, quotation structure, genre indicators. Focuses on writing-* and grammar-connect-* issue types.

Output: `/tmp/claude/wave2_discourse.tsv`

### Grammar Analyst
Micro-level grammar within clauses. Passives, abstract nouns, possession, pronouns, ellipsis, word-level syntax. Integrates automated detection output first. Focuses on figs-activepassive, figs-abstractnouns, figs-possession, writing-pronouns, figs-ellipsis.

Output: `/tmp/claude/wave2_grammar.tsv`

### Figurative Language Analyst
Figures of speech. Metaphor, metonymy, simile, synecdoche, personification, merism, hendiadys, doublet, idiom. Cross-references the biblical imagery classification lists in figs-metonymy.md and figs-metaphor.md. Focuses on figs-* issue types.

Output: `/tmp/claude/wave2_figurative.tsv`

### Speech Acts & Literary Analyst
Rhetorical devices and speech acts. Rhetorical questions, imperatives, exclamations, irony, hyperbole, litotes, euphemism, poetry markers, parallelism. Focuses on figs-rquestion, figs-imperative, figs-exclamations, figs-hyperbole, writing-poetry, figs-parallelism.

Output: `/tmp/claude/wave2_speech.tsv`

Each agent has a primary domain but overlaps with the others. When agents identify the same phrase, they should compare classifications. Disagreement is productive -- it's better to surface a conflict than to let a wrong classification pass unchallenged.

## Wave 3: Challenge and Defend

Spawn a Challenger agent after wave 2 completes.

### Classification Challenger
For every classification from wave 2, checks:
- Is this the right issue type? Could it be a commonly confused alternative?
- Tests: metaphor vs metonymy, doublet vs hendiadys, idiom vs metaphor, doublet vs parallelism
- Cross-references issues_resolved and the biblical imagery classification lists
- Does NOT find new issues -- only challenges existing ones
- Pays special attention to disagreements surfaced in wave 2
- **ULT coherence check**: For each issue, does it match what the human ULT actually renders? If the human ULT already handles the construct naturally (e.g., already made a passive active, already unpacked a figure), drop the issue. The human ULT is authoritative -- flag the issue, not the text.

Wave 2 agents defend: When challenged, the original agent argues for their classification with evidence from the text, published TNs, or issues_resolved. The Challenger can accept the defense or escalate to the Merger.

Output: `/tmp/claude/wave3_challenges.tsv` (challenged items with resolutions)

## Wave 4: Merge

Spawn a Merger agent (or orchestrator handles directly for smaller chapters).

### Translational Decision Advisor
- Merges all wave 2 findings
- Applies wave 3 challenge outcomes
- Resolves remaining conflicts
- Deduplicates (same phrase, overlapping issues)
- Orders: first-to-last by ULT position within each verse, longest-to-shortest when phrases nest
- Produces final issues TSV

## Guiding Principle

The human ULT/UST is authoritative. Issues adapt to the text, not the other way around. If the human rendering already resolves a potential issue, there is no issue to flag.

## Output

`output/issues/<BOOK>-<CHAPTER>.tsv`

Same format as base issue-identification:
```
[book]	[chapter:verse]	[supportreference]	[ULT text]			[explanation if needed]
```

## Flow

```
Setup:    Fetch human ULT/UST from Door43 master
          Parse -> alignment JSON + plain text
          Compare ULT/UST divergence patterns
          Run automated detection (passives, abstract nouns)
          Build published TN index

Wave 2:   Discourse Analyst ───┐
          Grammar Analyst ─────┤  (all read human ULT/UST,
          Figurative Lang. ────┤   detection output, divergences,
          Speech Acts/Lit. ────┘   check each other's work)

Wave 3:   Challenger ──────────── (challenges classifications,
                                   checks ULT coherence,
                                   wave 2 agents defend)

Wave 4:   Merger ─────────────── (final issues TSV)
```
