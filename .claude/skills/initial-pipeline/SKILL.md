---
name: initial-pipeline
description: Orchestrate ULT-gen, issue-id, and UST-gen as a coordinated team for a chapter. 6-wave pipeline with adversarial issue identification and ULT feedback loop. Supports --heavy for 4-agent issue identification.
---

# Initial Pipeline Orchestrator

Coordinates ULT-gen, issue-id, and UST-gen as a persistent team for a chapter. All agents are teammates that can interact across waves -- the ULT agent stays alive to revise its own work and answer queries, and the UST agent can consult anyone when it starts in Wave 6.

## Inputs

- **Book**: 3-letter abbreviation (PSA, GEN, 2SA, etc.)
- **Chapter**: number
- **Mode**: `--heavy` (optional) -- use 4 specialist analysts instead of the default 2

### Chapter Padding Convention

Zero-pad the chapter number for all filenames: 3 digits for PSA (e.g., `061`), 2 digits for other books (e.g., `03`). Use `<CH>` below to mean the padded form. This matches makeBP's convention so output files are found by downstream phases.

## Mode

Default (no flag): 2 analysts ("structure" and "rhetoric").

If `--heavy` is specified:
- Wave 2 uses 4 specialist analysts ("discourse", "grammar", "figurative", "speech")
- Wave 3 challenger reviews 4 TSVs instead of 2
- Wave 5 verification contacts 4 analysts instead of 2 (if Wave 5 runs)
- All other waves unchanged (ULT-gen, merge, ULT revision, UST-gen)

## Why Run Together

These three stages benefit from cross-checking:
- Issue-id catches ULT rendering problems early (before human review)
- ULT revisions from issue-id feedback improve the literal text
- UST is generated AFTER issue-id so it can model how to handle the identified issues
- Agents stay alive across waves -- the ULT translator can defend and revise its own choices, analysts can clarify their findings for UST

## Team Setup

Create a team for the full pipeline:

```
TeamCreate "pipeline-<BOOK>-<CHAPTER>"
```

Team name pattern: `pipeline-PSA-061`, `pipeline-GEN-01`, etc.

All agents below are spawned as teammates in this team.

### Working Directory

```bash
TMP=tmp/pipeline-<BOOK>-<CHAPTER>
mkdir -p $TMP
```

All intermediate files below use `$TMP` as the working directory.

### Build Published TN Index

```bash
python3 .claude/skills/utilities/scripts/build_tn_index.py
```

This builds/refreshes the index (daily cache). Use `--lookup` and `--issue` for precedent lookups during analysis:
```bash
python3 .claude/skills/utilities/scripts/build_tn_index.py --issue figs-metaphor
python3 .claude/skills/utilities/scripts/build_tn_index.py --lookup "tongue"
```

## Orchestrator Patience

Agents take time. Do not:
- Send shutdown requests until ALL waves are complete and final outputs are written
- Send duplicate messages or nudge too quickly
- Proceed to the next wave until the current wave's agents confirm completion

Do:
- Wait for each agent's confirmation message before proceeding
- Allow agents time to cross-read and interact
- Only send shutdown_request after Wave 6 output is written
- You may gently nudge agents, or ask what they are waiting for if they seem stuck

## Teammate Lifetimes

| Teammate | Spawn | Active Work | Passive/Queryable | Shutdown |
|----------|-------|-------------|-------------------|----------|
| ult-gen | Wave 1 | Waves 1, 4b | Waves 2-3, 5-6 | After cleanup |
| structure | Wave 2 | Waves 2, 3, 5 | Wave 6 | After cleanup |
| rhetoric | Wave 2 | Waves 2, 3, 5 | Wave 6 | After cleanup |
| challenger | Wave 3 | Wave 3 | -- | After Wave 3 rulings |
| ust-gen | Wave 6 | Wave 6 | -- | After cleanup |

### Heavy Mode Lifetimes

| Teammate | Spawn | Active Work | Passive/Queryable | Shutdown |
|----------|-------|-------------|-------------------|----------|
| ult-gen | Wave 1 | Waves 1, 4b | Waves 2-3, 5-6 | After cleanup |
| discourse | Wave 2 | Waves 2, 3, 5 | Wave 6 | After cleanup |
| grammar | Wave 2 | Waves 2, 3, 5 | Wave 6 | After cleanup |
| figurative | Wave 2 | Waves 2, 3, 5 | Wave 6 | After cleanup |
| speech | Wave 2 | Waves 2, 3, 5 | Wave 6 | After cleanup |
| challenger | Wave 3 | Wave 3 | -- | After Wave 3 rulings |
| ust-gen | Wave 6 | Wave 6 | -- | After cleanup |

"Passive/Queryable" means the agent is alive but waiting. Other agents can DM it for clarification. It responds but doesn't initiate work.

## Wave 1: ULT Draft

Spawn `ult-gen` as a teammate (`subagent_type: "general-purpose"`, with `team_name` set, name: "ult-gen").

The ULT agent:
1. Translates Hebrew to literal English for the chapter (following ULT-gen skill)
2. Writes draft to `output/AI-ULT/<BOOK>/<BOOK>-<CH>.usfm`
3. Sends message to team-lead: "ULT draft written"
4. Stays alive -- holds for messages from later waves

Include in the ULT agent's prompt:
- Invoke the ULT-gen skill for the chapter
- After writing the draft, send a message to team-lead confirming it's written
- Then wait for messages. You will receive:
  - Queries from the challenger about your rendering decisions (Wave 3)
  - Revision instructions from team-lead with specific changes to apply (Wave 4b)
  - Clarification queries from analysts or the UST agent (Waves 5-6)
- Respond to each message as it arrives
- Do not mark your task as completed until you receive a shutdown request

Do NOT spawn Wave 2 until the ULT draft message is received.

UST is NOT generated here. UST needs the issue-id output to know what translation issues exist so it can model handling them.

## Wave 2: Issue Identification (2 teammates)

Spawn 2 teammates (`subagent_type: "issue-identification"`, with `team_name` set). Each analyst reads:
- ULT draft from Wave 1 (`output/AI-ULT/<BOOK>/<BOOK>-<CH>.usfm`)
- Published TN index (via `build_tn_index.py --lookup`/`--issue`)

Each writes their TSV to `$TMP/wave2_*.tsv`. As they work, they read each other's output files for cross-checking. When they find genuine disagreements, they send DMs to the relevant analyst using SendMessage.

Include in each analyst's prompt:
- The output format guardrail (see Output Format section below)
- Instruction to read the other analyst's TSV file as it appears
- Instruction to use SendMessage for disagreements worth flagging
- **Hold protocol**: After writing your TSV, send a message to team-lead confirming your file is written, then wait. You will receive:
  - Challenges from the challenger agent (Wave 3) -- defend your classifications
  - Verification requests from team-lead (Wave 5) -- re-check against revised ULT (only if ULT was revised)
  - Queries from the UST agent (Wave 6) -- clarify issues as needed
- Do not mark your task as completed until you receive a shutdown request

### Structure Analyst (teammate name: "structure")
Grammar and discourse structure, from macro to micro level. Discourse markers, participant tracking, paragraph structure, connectors between clauses, quotation structure, genre indicators, passives, abstract nouns, possession, pronouns, ellipsis, word-level syntax. Integrates automated detection output first. Focuses on writing-*, grammar-connect-*, figs-activepassive, figs-abstractnouns, figs-possession, writing-pronouns, figs-ellipsis, and similar structural issues.

Output: `$TMP/wave2_structure.tsv`

### Rhetoric Analyst (teammate name: "rhetoric")
Figures of speech, speech acts, and cultural references. Metaphor, metonymy, simile, synecdoche, personification, merism, hendiadys, doublet, idiom, rhetorical questions, imperatives, exclamations, irony, hyperbole, litotes, euphemism, poetry markers, parallelism. Cross-references the biblical imagery classification lists in figs-metonymy.md and figs-metaphor.md.

Output: `$TMP/wave2_rhetoric.tsv`

As you work, read the other analyst's TSV file when it appears. If you find the same phrase classified differently, send a DM to flag the disagreement.

Wait for both analysts to send their "file written" messages. Do NOT proceed to Wave 3 until both files exist.

### Heavy Mode: 4 Analysts

If `--heavy`, spawn 4 teammates instead of 2 (`subagent_type: "issue-identification"`, with `team_name` set). Same inputs, cross-reading, hold protocol, and output format as default mode.

#### Discourse Analyst (teammate name: "discourse")
Macro-level grammar and structure. Discourse markers, participant tracking, paragraph structure, connectors between clauses, quotation structure, genre indicators. Focuses on writing-* and grammar-connect-* issue types.

Output: `$TMP/wave2_discourse.tsv`

#### Grammar Analyst (teammate name: "grammar")
Micro-level grammar within clauses. Passives, abstract nouns, possession, pronouns, ellipsis, word-level syntax. Focuses on figs-activepassive, figs-abstractnouns, figs-possession, writing-pronouns, figs-ellipsis, and similar word/phrase-level issues.

Output: `$TMP/wave2_grammar.tsv`

#### Figurative Language Analyst (teammate name: "figurative")
Figures of speech. Metaphor, metonymy, simile, synecdoche, personification, merism, hendiadys, doublet, idiom. Cross-references the biblical imagery classification lists in figs-metonymy.md and figs-metaphor.md. Focuses on figs-* issue types.

Output: `$TMP/wave2_figurative.tsv`

#### Speech Acts & Literary Analyst (teammate name: "speech")
Rhetorical devices and speech acts. Rhetorical questions, imperatives, exclamations, irony, hyperbole, litotes, euphemism, poetry markers, parallelism. Focuses on figs-rquestion, figs-imperative, figs-exclamations, figs-hyperbole, writing-poetry, and figs-parallelism.

Output: `$TMP/wave2_speech.tsv`

Each agent has a primary domain but overlaps with the others. When agents identify the same phrase, they should compare classifications. Disagreement is productive -- it's better to surface a conflict than to let a wrong classification pass unchallenged.

Wait for all 4 analysts to send their "file written" messages to team-lead. Do NOT proceed to Wave 3 until all 4 files exist.

## Wave 3: Challenge and Defend

Spawn the Challenger as a teammate (name: "challenger"). The Wave 2 analysts and ULT agent are all still alive.

### Challenge Phase
The Challenger:
1. Reads all wave 2 TSVs
2. Identifies issues to challenge (misclassifications, missed overlaps, ULT coherence failures)
3. Groups challenges by analyst
4. Sends one batch DM to each analyst with their challenges
5. DMs `ult-gen` to ask about specific rendering decisions when relevant (e.g., "In v3 you rendered the construct chain as X -- was that a deliberate structural preservation?")

Challenge criteria:
- Is this the right issue type? Could it be a commonly confused alternative?
- Tests: metaphor vs metonymy, doublet vs hendiadys, idiom vs metaphor, doublet vs parallelism
- Cross-references issues_resolved and the biblical imagery classification lists
- Does NOT find new issues -- only challenges existing ones
- Pays special attention to disagreements surfaced in wave 2
- Resolves disagreements between Wave 2 agents
- Identifies duplicates where multiple agents flagged the same issue
- **ULT coherence check**: For each issue, does it match what the AI ULT actually renders? Uses DMs to `ult-gen` to understand rendering intent. If the ULT rendering already handles a construct naturally, flag the ULT for adjustment or drop the note as appropriate.
  - Heuristic: If Hebrew has a named grammatical structure (construct chain, passive, etc.), ULT should preserve it literally. If it's just word order with no structural name, ULT can use natural English.
- **Grammar issues are independent**: Abstract nouns, passives (figs-abstractnouns,
  figs-activepassive) are script-detected and AI-verified. They cannot be subsumed
  by, merged into, or dropped in favor of figurative issues on the same phrase.
  Keep both layers. Other grammar-level issues (figs-possession, figs-ellipsis,
  figs-nominaladj) should also generally not be dropped or merged with figurative
  issues.

### Defend Phase
Each analyst wakes up, reads their challenges, and sends a defense DM back to the Challenger. The ULT agent responds to any queries about its rendering decisions. One round only -- no infinite back-and-forth.

### Ruling Phase
The Challenger reads all defenses and ULT agent responses, makes final rulings: KEEP, DROP, RECLASSIFY, or MERGE_DUPLICATE for each challenged issue. Also notes any ULT revisions needed (passed to the orchestrator for Wave 4b).

Output: `$TMP/wave3_challenges.tsv` (all items with resolutions)

After writing rulings, the Challenger sends a DM to each analyst: "Rulings complete." (Analysts continue holding for Wave 5.)

Send `shutdown_request` to the challenger after rulings are written -- it has no further role.

## Wave 4a: Merge

Orchestrator merges all findings:
- Merges all wave 2 findings
- Applies wave 3 challenge outcomes (rulings override wave 2)
- Resolves remaining conflicts
- Deduplicates (same phrase, same issue type only -- different issue types on the same phrase are not duplicates)
- Grammar issues (abstract nouns, passives, possession, ellipsis, nominaladj) always survive alongside figurative issues on the same phrase
- Orders: first-to-last by ULT position within each verse, longest-to-shortest when phrases nest
- Enforces the output format guardrail (brief hints only)
- Writes `$TMP/merged_issues.tsv`

## Wave 4b: ULT Revision

Send a message to `ult-gen` (still alive from Wave 1) with the ULT revision requests from Wave 3. Include:
- Specific verse/phrase references
- What to adjust and why (from the challenger's rulings and ULT coherence checks)
- Which structural preservations to keep

The ULT agent:
1. Reads the revision requests
2. Applies changes to the ULT draft
3. Writes revised ULT (draft 2) to `output/AI-ULT/<BOOK>/<BOOK>-<CH>.usfm`
4. Sends message to team-lead: "ULT revision complete"

This is more natural than a separate agent applying changes -- the original translator revises their own work with specific feedback.

Wait for the ULT agent's confirmation before proceeding.

## Wave 5: Verification

**Skip condition**: If Wave 4b produced no ULT changes (challenger found no rendering issues), skip Wave 5 entirely. Write the merged issues directly to final output and proceed to Wave 6. The analysts already verified their work during Wave 2 cross-reading and Wave 3 challenge/defend -- re-verifying against an unchanged ULT adds cost without value.

**When Wave 5 runs** (ULT was revised in 4b):

Send a message to each Wave 2 analyst (still alive): "Re-check your findings against the revised ULT at output/AI-ULT/<BOOK>/<BOOK>-<CH>.usfm. Drop anything that no longer applies after the revision. Flag anything new the revision introduced."

Each analyst:
1. Reads the revised ULT (draft 2)
2. Compares against their original findings + challenge rulings
3. Can DM `ult-gen` for clarification on specific changes
4. Writes verification notes to `$TMP/wave5_*.tsv`
5. Sends message to team-lead: "Verification complete"

Wait for all analysts to confirm (2 default, 4 in heavy mode), then update the merged issues based on verification feedback.

Final issues written to `output/issues/<BOOK>/<BOOK>-<CH>.tsv`.

### Final Check
Before writing to output/issues/, verify ordering within each verse: first-to-last by ULT position, longest-to-shortest when phrases nest. The orchestrator performs this final write.

## Wave 6: UST Generation

Spawn `ust-gen` as a teammate (`subagent_type: "general-purpose"`, with `team_name` set, name: "ust-gen").

The UST agent reads:
- The final revised ULT (draft 2) at `output/AI-ULT/<BOOK>/<BOOK>-<CH>.usfm`
- The final issues TSV at `output/issues/<BOOK>/<BOOK>-<CH>.tsv`
- T4T source text
- UST Strong's index (`build_ust_index.py --lookup`/`--compare`) for published UST rendering precedent

The UST agent can query other teammates for clarification:
- DM `ult-gen`: "What was your reasoning for the construct chain rendering in v5?"
- DM analysts: "The issue on v3 says 'metonymy - lip represents speech'. Can you confirm the scope -- is it just 'lip' or the whole phrase 'lip of falsehood'?"

These queries are optional -- only when the UST agent genuinely needs clarification that isn't evident from the files.

Include in the UST agent's prompt:
- Invoke the UST-gen skill for the chapter
- You have access to the ULT agent and the issue analysts as teammates (2 default, 4 in heavy mode). If the issues TSV or ULT text leaves something ambiguous, DM them to clarify before guessing.
- UST models how to handle each identified issue -- it shows the translator what the text means in natural language, with figures unpacked, implicit info made explicit, passives made active, etc.

The UST agent:
1. Generates UST (following UST-gen skill)
2. Writes to `output/AI-UST/<BOOK>/<BOOK>-<CH>.usfm`
3. Writes alignment hints to `output/AI-UST/hints/<BOOK>/<BOOK>-<CH>.json` (per UST-gen Step 7.5)
4. Sends message to team-lead: "UST complete"

## Cleanup

After Wave 6 output is confirmed:
1. Send `shutdown_request` to all live teammates (default: ult-gen, structure, rhetoric, ust-gen; in heavy mode: ult-gen, discourse, grammar, figurative, speech, ust-gen; and challenger if still alive)
2. Wait for shutdown confirmations
3. `TeamDelete` to clean up team resources

## Outputs

1. `output/AI-ULT/<BOOK>/<BOOK>-<CH>.usfm` -- revised ULT (draft 2, post-issue-id feedback)
2. `output/AI-UST/<BOOK>/<BOOK>-<CH>.usfm` -- UST (informed by issues)
3. `output/AI-UST/hints/<BOOK>/<BOOK>-<CH>.json` -- alignment hints from UST generator
4. `output/issues/<BOOK>/<BOOK>-<CH>.tsv` -- verified issues (post-ULT-revision check)

## Output Format (Firewall)

The explanation column in issue TSVs is a brief classification hint. It describes WHY the issue exists, not HOW to handle it. This applies to every agent (Wave 2 analysts, Challenger, and Merger).

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
Setup:    TeamCreate "pipeline-<BOOK>-<CHAPTER>"
          mkdir working directory, build TN index

Wave 1:   ult-gen (teammate) ──── generates ULT draft, holds
          |
          | "ULT draft written"
          v
Wave 2:   structure ───────────┐  (2 teammates, cross-read files,
          rhetoric ────────────┘   DM on disagreements, hold)
          |
          | both "file written"
          v
Wave 3:   challenger (teammate) ── challenges 2 analysts via DM
          analysts defend ──────── one round of defend/respond
          challenger <-> ult-gen ── queries about rendering intent
          challenger rules ─────── writes rulings, notifies analysts
          |
          v
Wave 4a:  orchestrator merges ──── (applies rulings, deduplicates)
Wave 4b:  team-lead -> ult-gen ─── (revision instructions via DM)
          ult-gen revises ──────── (writes ULT draft 2)
          |
          |── if ULT revised ──────────────────────────┐
          |                                             v
          |                              Wave 5: analysts re-check
          |                                             |
          |── if ULT unchanged ─── skip Wave 5 ────────┤
          |                                             |
          v                                             v
          orchestrator writes final issues TSV

Wave 6:   ust-gen (teammate) ───── reads final ULT + issues
          ust-gen <-> ult-gen ──── (optional: rendering queries)
          ust-gen <-> analysts ─── (optional: issue clarification)
          ust-gen writes UST
          |
          | "UST complete"
          v
Cleanup:  shutdown_request all -> TeamDelete
```

### Heavy Mode Flow

```
Setup:    TeamCreate "pipeline-<BOOK>-<CHAPTER>"
          mkdir working directory, build TN index

Wave 1:   ult-gen (teammate) ──── generates ULT draft, holds
          |
          | "ULT draft written"
          v
Wave 2:   discourse ──────────┐
          grammar ────────────┤  (4 teammates, cross-read files,
          figurative ─────────┤   DM on disagreements, hold)
          speech ─────────────┘
          |
          | all 4 "file written"
          v
Wave 3:   challenger (teammate) ── challenges analysts via DM
          analysts defend ──────── one round of defend/respond
          challenger <-> ult-gen ── queries about rendering intent
          challenger rules ─────── writes rulings, notifies analysts
          |
          v
Wave 4a:  orchestrator merges ──── (applies rulings, deduplicates)
Wave 4b:  team-lead -> ult-gen ─── (revision instructions via DM)
          ult-gen revises ──────── (writes ULT draft 2)
          |
          |── if ULT revised ──────────────────────────┐
          |                                             v
          |                              Wave 5: analysts re-check
          |                                             |
          |── if ULT unchanged ─── skip Wave 5 ────────┤
          |                                             |
          v                                             v
          orchestrator writes final issues TSV

Wave 6:   ust-gen (teammate) ───── reads final ULT + issues
          ust-gen <-> ult-gen ──── (optional: rendering queries)
          ust-gen <-> analysts ─── (optional: issue clarification)
          ust-gen writes UST
          |
          | "UST complete"
          v
Cleanup:  shutdown_request all -> TeamDelete
```

## Lessons Learned (PSA 61)

- **Coverage vs accuracy**: Parallel independent analysis (wave 2) optimizes for coverage.
  Adversarial review (wave 3) optimizes for accuracy. Differentiating the wave 2 agents
  by domain and having them check each other gives both.
- **Heart classification**: Without a challenger, a wrong skill file entry (heart = metaphor)
  went unchallenged. The challenger agent cross-references authoritative lists.
- **ULT/issue-id coherence**: Two failure modes:
  1. ULT unnecessarily preserves Hebrew form -> adjust ULT, drop note (PSA 61:2 word order)
  2. ULT incorrectly flattens Hebrew structure -> correct ULT, keep note (PSA 61:3 construct)
  Wave 4b handles both by having the ULT agent revise its own work, and wave 5 verifies
  the issues still hold.
- **UST after issue-id**: UST generated in isolation can't model issue handling. Generating
  it after issue-id means it can show translators what each figure/construction means in
  plain language. With the team feature, UST can also ask the analysts directly when the
  TSV leaves scope or classification ambiguous.
- **Note ordering**: Within each verse, first-to-last by ULT position, longest-to-shortest
  when phrases nest. Issue-id should output in this order; assemble_notes.py enforces it.
- **Persistent agents**: The ULT agent revising its own work in Wave 4b produces better
  results than a separate agent applying changes -- the original translator understands
  its own rendering decisions and can make targeted fixes.

## Lessons Learned (PSA 88)

- **Skip Wave 5 when ULT unchanged**: If the challenger finds no ULT rendering issues
  and Wave 4b produces no changes, Wave 5 verification is redundant -- analysts would
  re-check against the same text they already analyzed. Skip directly to writing final
  issues and launching Wave 6. This saves a full round of agent turns.
- **4 analysts produce clean but overlapping work**: With 4 domain-specialist analysts
  on an 18-verse psalm, the 94 raw issues contained 18 duplicates (same phrase, same
  type across analysts) and only 1 misclassification. The challenger's main value was
  deduplication rather than error correction. This supports making 2-analyst mode the
  default -- the coverage/accuracy tradeoff favors fewer agents for typical chapters.
- **ULT agent as verifier**: Even when Wave 5 was run redundantly, the ULT agent caught
  2 valid drops (duplicate pronoun note, abstract noun subsumed by metaphor) and 1 valid
  addition (figs-irony on "free among the dead"). The ULT translator's perspective on
  its own rendering decisions adds unique verification value.
- **Dark psalms with no resolution**: PSA 88 is unique in the Psalter -- pure lament with
  no hope turn. The UST needs to preserve this tone rather than softening it. The issue
  identification correctly captured the death/darkness imagery cluster without imposing
  resolution that isn't in the text.
