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

### Working Directory

Use a project-local tmp directory (sandbox may block `/tmp/claude/`):
```bash
TMP=tmp/deep-issue-id
mkdir -p $TMP
```

All paths below use `$TMP` as the working directory.

### 1. Fetch and Parse

```bash
python3 .claude/skills/utilities/scripts/fetch_door43.py <BOOK> > $TMP/book_ult.usfm
python3 .claude/skills/utilities/scripts/fetch_door43.py <BOOK> --type ust > $TMP/book_ust.usfm 2>/dev/null || true

node .claude/skills/utilities/scripts/usfm/parse_usfm.js $TMP/book_ult.usfm \
  --chapter <N> \
  --output-json $TMP/alignments.json \
  --output-plain $TMP/ult_plain.usfm

node .claude/skills/utilities/scripts/usfm/parse_usfm.js $TMP/book_ust.usfm \
  --chapter <N> \
  --plain-only > $TMP/ust_plain.usfm 2>/dev/null || true
```

Note: `--chapter` filters both alignment JSON and plain text output. The UST parse also needs `--chapter <N>` to avoid dumping the whole book.

### 2. Compare ULT/UST

```bash
python3 .claude/skills/issue-identification/scripts/compare_ult_ust.py \
  $TMP/ult_plain.usfm $TMP/ust_plain.usfm \
  --chapter <N> --output $TMP/ult_ust_diff.tsv
```

### 3. Run Automated Detection

```bash
python3 .claude/skills/issue-identification/scripts/detection/detect_activepassive.py \
  $TMP/alignments.json --format tsv > $TMP/detected_issues.tsv

python3 .claude/skills/issue-identification/scripts/detection/detect_abstract_nouns.py \
  $TMP/alignments.json --format tsv >> $TMP/detected_issues.tsv
```

### 4. Build Published TN Index

```bash
python3 .claude/skills/utilities/scripts/build_tn_index.py
```

This builds/refreshes the index (daily cache). Use `--lookup` and `--issue` for precedent lookups during analysis (not raw grep):
```bash
python3 .claude/skills/utilities/scripts/build_tn_index.py --issue figs-metaphor
python3 .claude/skills/utilities/scripts/build_tn_index.py --lookup "tongue"
```

## Team Setup

Create a team for cross-agent interaction:

```
TeamCreate "deep-issue-<BOOK>-<CHAPTER>"
```

Team name pattern: `deep-issue-PSA-120`, `deep-issue-GEN-01`, etc.

All agents below are spawned as teammates in this team.

## Orchestrator Patience

Agents take time. Do not:
- Send shutdown requests until ALL waves are complete and the final merge is written
- Send duplicate shutdown requests

Do:
- Wait for each analyst's "file written" message before proceeding to Wave 3
- Wait for the challenger's "rulings complete" message before proceeding to Wave 4
- Only send shutdown_request after the merge is written to output/issues/
- You may gently nudge agents, or ask what they are waiting for if they seem stuck.

## Wave 2: Issue Identification (4 team analysts)

Spawn 4 teammates (`subagent_type: "issue-identification"`, with `team_name` set). Each analyst reads:
- Human ULT (`$TMP/ult_plain.usfm`)
- Human UST (`$TMP/ust_plain.usfm`) if available
- Alignment JSON (`$TMP/alignments.json`)
- ULT/UST divergence patterns (`$TMP/ult_ust_diff.tsv`)
- Automated detections (`$TMP/detected_issues.tsv`)

Each writes their TSV to `$TMP/wave2_*.tsv`. As they work, they read each other's output files for cross-checking. When they find genuine disagreements, they send DMs to the relevant analyst using SendMessage.

Example interaction: Figurative analyst reads Grammar's output, sees "lip of falsehood" tagged as figs-possession but thinks figs-metonymy is the primary issue. Sends a DM to Grammar: "v2 'lip of falsehood' -- I have this as figs-metonymy (lip = speech). Your figs-possession is also valid but should it be secondary?"

This is lightweight -- not forced on every issue, just available when analysts genuinely disagree.

Include in each analyst's prompt:
- The output format guardrail (see Output Format section below)
- Instruction to read other analysts' TSV files as they appear
- Instruction to use SendMessage for disagreements worth flagging
- **Hold for Wave 3**: After writing your TSV, do NOT mark your task as completed. Send a message to team-lead confirming your file is written, then wait for DMs from the challenger agent. You will receive challenges to defend -- respond with one defense DM back to the challenger. After the challenger confirms rulings are complete, then mark your task completed.

### Discourse Analyst (teammate name: "discourse")
Macro-level grammar and structure. Discourse markers, participant tracking, paragraph structure, connectors between clauses, quotation structure, genre indicators. Focuses on writing-* and grammar-connect-* issue types.

Output: `$TMP/wave2_discourse.tsv`

### Grammar Analyst (teammate name: "grammar")
Micro-level grammar within clauses. Passives, abstract nouns, possession, pronouns, ellipsis, word-level syntax. Integrates automated detection output first. Focuses on figs-activepassive, figs-abstractnouns, figs-possession, writing-pronouns, figs-ellipsis.

Output: `$TMP/wave2_grammar.tsv`

### Figurative Language Analyst (teammate name: "figurative")
Figures of speech. Metaphor, metonymy, simile, synecdoche, personification, merism, hendiadys, doublet, idiom. Cross-references the biblical imagery classification lists in figs-metonymy.md and figs-metaphor.md. Focuses on figs-* issue types.

Output: `$TMP/wave2_figurative.tsv`

### Speech Acts & Literary Analyst (teammate name: "speech")
Rhetorical devices and speech acts. Rhetorical questions, imperatives, exclamations, irony, hyperbole, litotes, euphemism, poetry markers, parallelism. Focuses on figs-rquestion, figs-imperative, figs-exclamations, figs-hyperbole, writing-poetry, figs-parallelism.

Output: `$TMP/wave2_speech.tsv`

Each agent has a primary domain but overlaps with the others. When agents identify the same phrase, they should compare classifications. Disagreement is productive -- it's better to surface a conflict than to let a wrong classification pass unchallenged.

Wait for all 4 analysts to send their "file written" messages to team-lead. Do NOT mark Wave 2 tasks complete yet -- analysts must stay active to defend challenges in Wave 3. Only proceed to Wave 3 once all 4 files exist.

## Wave 3: Challenge and Defend

Spawn the Challenger as a 5th teammate (name: "challenger"). The Wave 2 analysts stay alive for this round.

### Challenge Phase
The Challenger:
1. Reads all wave 2 TSVs
2. Identifies issues to challenge (misclassifications, missed overlaps, ULT coherence failures)
3. Groups challenges by analyst
4. Sends one batch DM to each analyst with their challenges

Challenge criteria:
- Is this the right issue type? Could it be a commonly confused alternative?
- Tests: metaphor vs metonymy, doublet vs hendiadys, idiom vs metaphor, doublet vs parallelism
- Cross-references issues_resolved and the biblical imagery classification lists
- Does NOT find new issues -- only challenges existing ones
- Resolves disagreements between Wave 2 agents (e.g., one agent kept an issue another dropped)
- Identifies duplicates where multiple agents flagged the same issue
- **ULT coherence check**: For each issue, does it match what the human ULT actually renders? If the human ULT already handles the construct naturally (e.g., already made a passive active, already unpacked a figure), drop the issue. The human ULT is authoritative -- flag the issue, not the text.
- **Grammar issues are independent**: Abstract nouns, passives (figs-abstractnouns,
  figs-activepassive) are script-detected and AI-verified. They cannot be subsumed
  by, merged into, or dropped in favor of figurative issues on the same phrase.
  Keep both layers. Other grammar-level issues (figs-possession, figs-ellipsis,
  figs-nominaladj) should also generally not be dropped or merged with figurative
  issues.

### Defend Phase
Each analyst wakes up, reads their challenges, and sends a defense DM back to the Challenger. One round only -- no infinite back-and-forth.

### Ruling Phase
The Challenger reads all defenses and makes final rulings: KEEP, DROP, RECLASSIFY, or MERGE_DUPLICATE for each challenged issue.

After writing rulings, the Challenger sends a DM to each analyst: "Rulings complete, you may shut down." This releases analysts from their hold so they can mark their tasks completed.

Output: `$TMP/wave3_challenges.tsv` (all items with resolutions)

## Wave 4: Merge

Orchestrator or Merger agent merges all findings.

### Translational Decision Advisor
- Merges all wave 2 findings
- Applies wave 3 challenge outcomes (rulings override wave 2)
- Resolves remaining conflicts
- Deduplicates (same phrase, same issue type only -- different issue types on the same phrase are not duplicates)
- Grammar issues (abstract nouns, passives, possession, ellipsis, nominaladj) always survive alongside figurative issues on the same phrase
- Orders: first-to-last by ULT position within each verse, longest-to-shortest when phrases nest
- Enforces the output format guardrail (brief hints only)
- Produces final issues TSV

### Final Check
Before writing to output/issues/, verify ordering within each verse: first-to-last by ULT position, longest-to-shortest when phrases nest.

## Cleanup

After Merger completes:
1. Send `shutdown_request` to all 5 teammates (discourse, grammar, figurative, speech, challenger)
2. Wait for shutdown confirmations
3. `TeamDelete` to clean up team resources

## Guiding Principle

The human ULT/UST is authoritative. Issues adapt to the text, not the other way around. If the human rendering already resolves a potential issue, there is no issue to flag.

## Output

`output/issues/<BOOK>-<CHAPTER>.tsv`

Same format as base issue-identification:
```
[book]	[chapter:verse]	[supportreference]	[ULT text]			[explanation if needed]
```

### Output Format (Firewall)

The explanation column is a brief classification hint. It describes WHY the issue exists, not HOW to handle it. This applies to every agent (Wave 2 analysts, Challenger, and Merger).

Rules:
- 1-10 words maximum
- Why the issue exists, not how to handle it
- No "If your language..." phrasing
- No "Alternate translation:" suggestions
- No translation note templates or proto-notes
- No advice to the translator -- that is the TN writer's job

Good:
```
metonymy - lip represents speech
rhetorical question - declares certainty of punishment
abstract noun - could be verb
doublet - two words for emphasis
metaphor - refuge as physical shelter
passive - agent is God
```

Bad (never produce these):
```
If your language does not use abstract nouns, you could express "salvation" as a verb
Alternate translation: "the things he says"
This is a metaphor. The psalmist speaks of God as if he were a fortress.
```

Include these rules in every agent prompt (Wave 2 analysts, Challenger batch, Merger).

## Flow

```
Setup:    Fetch human ULT/UST from Door43 master
          Parse -> alignment JSON + plain text (chapter-filtered)
          Compare ULT/UST divergence patterns
          Run automated detection (passives, abstract nouns)
          Build published TN index

Team:     TeamCreate "deep-issue-<BOOK>-<CHAPTER>"

Wave 2:   Discourse ──────────┐
          Grammar ────────────┤  (4 teammates, cross-read files,
          Figurative ─────────┤   DM on disagreements,
          Speech ─────────────┘   stay alive for Wave 3)

Wave 3:   Challenger spawns ──── challenges each analyst via DM
          Analysts defend ──────  one round of defend/respond
          Challenger rules ─────  writes final rulings

Wave 4:   Merger ─────────────── (applies rulings, deduplicates,
                                   enforces output format firewall)

Cleanup:  shutdown_request all → TeamDelete
```
