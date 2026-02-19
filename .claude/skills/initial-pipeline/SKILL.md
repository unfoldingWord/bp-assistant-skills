---
name: initial-pipeline
description: Orchestrate ULT-gen, issue-id, and UST-gen as a multi-agent pipeline for a single chapter. Use when asked to run the pipeline, generate content for a chapter, or start a new chapter.
---

# Initial Pipeline Orchestrator

Coordinates ULT-gen, issue-id, and UST-gen as a persistent team for a chapter. All agents are teammates that can interact across waves -- the ULT agent stays alive to revise its own work and answer queries, and the UST agent can consult anyone when it starts in Wave 6.

This skill orchestrates issue-identification agents. Shared orchestration
patterns are in sibling reference files (read each at the relevant stage):
- `orchestration-conventions.md` (start)
- `analyst-domains.md` (Wave 2)
- `challenger-protocol.md` (Wave 3)
- `merge-procedure.md` (Wave 4a)
- `gemini-review-wave.md` (Wave 7)

Analysts receive `.claude/agents/issue-identification.md` when spawned.

## Inputs

- **Book**: 3-letter abbreviation (PSA, GEN, 2SA, etc.)
- **Chapter**: number

## Why Run Together

These three stages benefit from cross-checking:
- Issue-id catches ULT rendering problems early (before human review)
- ULT revisions from issue-id feedback improve the literal text
- UST is generated AFTER issue-id so it can model how to handle the identified issues
- Agents stay alive across waves -- the ULT translator can defend and revise its own choices, analysts can clarify their findings for UST

## Team Setup

Read `orchestration-conventions.md` for chapter padding, model assignments, and patience rules. Pipeline-specific: only send `shutdown_request` after Wave 6 output is written.

```
TeamCreate "pipeline-<BOOK>-<CHAPTER>"
```

Team name pattern: `pipeline-PSA-061`, `pipeline-GEN-01`, etc.

### Working Directory

```bash
TMP=tmp/pipeline-<BOOK>-<CHAPTER>
mkdir -p $TMP
```

### Build Published TN Index

```bash
python3 .claude/skills/utilities/scripts/build_tn_index.py
```

This builds/refreshes the index (daily cache). Use `--lookup` and `--issue` for precedent lookups during analysis:
```bash
python3 .claude/skills/utilities/scripts/build_tn_index.py --issue figs-metaphor
python3 .claude/skills/utilities/scripts/build_tn_index.py --lookup "tongue"
```

## Teammate Lifetimes

| Teammate | Spawn | Active Work | Passive/Queryable | Shutdown |
|----------|-------|-------------|-------------------|----------|
| ult-gen | Wave 1 | Waves 1, 4b | Waves 2-3, 5-6 | After cleanup |
| structure | Wave 2 | Waves 2, 3, 5 | Wave 6 | After cleanup |
| rhetoric | Wave 2 | Waves 2, 3, 5 | Wave 6 | After cleanup |
| challenger | Wave 3 | Wave 3 | -- | After Wave 3 rulings |
| ust-gen | Wave 6 | Wave 6 | -- | After cleanup |

"Passive/Queryable" means the agent is alive but waiting. Other agents can DM it for clarification. It responds but doesn't initiate work.

## Wave 1: ULT Draft

Spawn `ult-gen` as a teammate (`subagent_type: "general-purpose"`, `model: "opus"`, with `team_name` set, name: "ult-gen").

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

## Wave 2: Issue Identification

Read `analyst-domains.md` for domain assignments and cross-reading protocol. Spawn both analysts with `subagent_type: "issue-identification"`, `model: "opus"`, and `team_name` set.

Each analyst reads:
- ULT draft from Wave 1 (`output/AI-ULT/<BOOK>/<BOOK>-<CH>.usfm`)
- Published TN index (via `build_tn_index.py --lookup`/`--issue`)

Each writes their TSV to `$TMP/wave2_*.tsv`.

**Hold protocol**: After writing your TSV, send a message to team-lead confirming your file is written, then wait. You will receive:
- Challenges from the challenger agent (Wave 3) -- defend your classifications
- Verification requests from team-lead (Wave 5) -- re-check against revised ULT (only if ULT was revised)
- Queries from the UST agent (Wave 6) -- clarify issues as needed
- Do not mark your task as completed until you receive a shutdown request

Wait for both analysts to send their "file written" messages. Do NOT proceed to Wave 3 until both files exist.

## Wave 3: Challenge and Defend

Read `challenger-protocol.md`. Spawn the challenger (`model: "sonnet"`, name: "challenger"). The Wave 2 analysts and ULT agent are all still alive.

Pipeline-specific additions:
- The challenger also DMs `ult-gen` to ask about specific rendering decisions when relevant (e.g., "In v3 you rendered the construct chain as X -- was that a deliberate structural preservation?")
- **ULT coherence heuristic**: If Hebrew has a named grammatical structure (construct chain, passive, etc.), ULT should preserve it literally. If it's just word order with no structural name, ULT can use natural English.
- The challenger notes any ULT revisions needed (passed to orchestrator for Wave 4b).

After writing rulings, the challenger sends "Rulings complete" to each analyst. Analysts continue holding for Wave 5.

Send `shutdown_request` to the challenger after rulings are written -- it has no further role.

Output: `$TMP/wave3_challenges.tsv`

## Wave 4a: Merge

Read `merge-procedure.md`. Orchestrator merges all findings. Writes `$TMP/merged_issues.tsv`.

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

Wait for both analysts to confirm, then update the merged issues based on verification feedback.

Final issues written to `output/issues/<BOOK>/<BOOK>-<CH>.tsv`.

### Final Check
Before writing to output/issues/, verify ordering within each verse: first-to-last by ULT position, longest-to-shortest when phrases nest. The orchestrator performs this final write.

## Wave 6: UST Generation

Spawn `ust-gen` as a teammate (`subagent_type: "general-purpose"`, `model: "opus"`, with `team_name` set, name: "ust-gen").

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
- You have access to the ULT agent and the issue analysts as teammates. If the issues TSV or ULT text leaves something ambiguous, DM them to clarify before guessing.
- UST models how to handle each identified issue -- it shows the translator what the text means in natural language, with figures unpacked, implicit info made explicit, passives made active, etc.

The UST agent:
1. Generates UST (following UST-gen skill)
2. Writes to `output/AI-UST/<BOOK>/<BOOK>-<CH>.usfm`
3. Writes alignment hints to `output/AI-UST/hints/<BOOK>/<BOOK>-<CH>.json` (per UST-gen Step 7.5)
4. Sends message to team-lead: "UST complete"

## Wave 7: Gemini Review (optional, default on)

Read `gemini-review-wave.md`. After Wave 6, run Gemini as independent reviewer. Skip if `--skip-gemini` is passed.

Pipeline runs three stages: `ult`, `issues`, and `ust`.

```bash
python3 .claude/skills/utilities/scripts/gemini_review.py --stage ult --book <BOOK> --chapter <CHAPTER>
python3 .claude/skills/utilities/scripts/gemini_review.py --stage issues --book <BOOK> --chapter <CHAPTER>
python3 .claude/skills/utilities/scripts/gemini_review.py --stage ust --book <BOOK> --chapter <CHAPTER>
```

## Cleanup

After Wave 7 (or Wave 6 if `--skip-gemini`):
1. Send `shutdown_request` to all live teammates (ult-gen, structure, rhetoric, ust-gen; and challenger if still alive)
2. Wait for shutdown confirmations
3. `TeamDelete` to clean up team resources

## Troubleshooting

- **Agent never sends "file written" message**: The sub-agent may have stalled or encountered an error silently. Check the agent's output log. If the agent is idle, send it a follow-up message asking for status. Restart the agent if unresponsive after 2 attempts.
- **ULT agent does not respond to revision requests**: The agent may have lost context. Re-send the revision request with the full file path and specific line numbers. If still unresponsive, terminate and re-spawn the agent.
- **Team cleanup fails**: Orphaned agent processes can remain after pipeline completion. Use `TeamDelete` to clean up, or manually check `~/.claude/teams/` for stale team files.

## Outputs

1. `output/AI-ULT/<BOOK>/<BOOK>-<CH>.usfm` -- revised ULT (draft 2, post-issue-id feedback)
2. `output/AI-UST/<BOOK>/<BOOK>-<CH>.usfm` -- UST (informed by issues)
3. `output/AI-UST/hints/<BOOK>/<BOOK>-<CH>.json` -- alignment hints from UST generator
4. `output/issues/<BOOK>/<BOOK>-<CH>.tsv` -- verified issues (post-ULT-revision check)

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
Wave 7:   Gemini review (ult, issues, ust stages)
          |
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
