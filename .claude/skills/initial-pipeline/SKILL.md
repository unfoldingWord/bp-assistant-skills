---
name: initial-pipeline
description: Orchestrate ULT-gen, issue-id, and UST-gen as a multi-agent pipeline for a single chapter. Use when asked to run the pipeline, generate content for a chapter, or start a new chapter.
---

# Initial Pipeline Orchestrator

Coordinates ULT-gen, issue-id, and UST-gen as a persistent team for a chapter. All agents are teammates that can interact across waves -- the ULT agent stays alive to revise its own work and answer queries, and the UST agent can consult anyone when it starts in Wave 6.

This skill orchestrates issue-identification agents. Shared orchestration
patterns are in the issue-identification skill directory (read each at the relevant stage):
- `.claude/skills/issue-identification/orchestration-conventions.md` (start)
- `.claude/skills/issue-identification/analyst-domains.md` (Wave 2)
- `.claude/skills/issue-identification/challenger-protocol.md` (Wave 3)
- `.claude/skills/issue-identification/merge-procedure.md` (Wave 4a)
- `.claude/skills/issue-identification/gemini-review-wave.md` (Wave 7)

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

Read `.claude/skills/issue-identification/orchestration-conventions.md` for chapter padding, model assignments, and patience rules. Pipeline-specific: only send `shutdown_request` after Wave 6 output is written.

```
TeamCreate "pipeline-<BOOK>-<CHAPTER>"
```

Team name pattern: `pipeline-HAB-03`, `pipeline-PSA-119`, etc.

### Working Directory

Use this path convention for intermediate files:

`tmp/pipeline-<BOOK>-<CHAPTER>`

Do not rely on shell commands in restricted environments. When a tool needs to write a file under `tmp/`, pass that target path and let the tool create parent directories.

## Critical Orchestrator Rule

This pipeline uses async teammates. Narrative waiting is not enough.

Between waves, the orchestrator must explicitly:
1. Poll agent state with `TaskGet` or `TaskList`
2. Verify the expected files exist
3. Only then continue to the next wave

Do not return success after launching agents or after seeing partial progress.
The task is only complete after all required Wave 1-6 outputs exist on disk:
- `output/AI-ULT/<BOOK>/<BOOK>-<CH>.usfm`
- `output/issues/<BOOK>/<BOOK>-<CH>.tsv`
- `output/AI-UST/<BOOK>/<BOOK>-<CH>.usfm`

### Fetch T4T for the Book

Use `mcp__workspace-tools__fetch_t4t` with `{"books":["<BOOK>"]}`.

T4T is the base source for UST creation (Wave 6). All OT books are pre-fetched in `data/t4t/`, but run this to ensure the book is cached. The fetch tool skips if already cached.

### Build Published TN Index

Use `mcp__workspace-tools__build_tn_index` with `{}`.

This builds/refreshes the index (daily cache). Use `lookup` and `issue` arguments for precedent lookups during analysis:

- `mcp__workspace-tools__build_tn_index` with `{"issue":"figs-metaphor"}`
- `mcp__workspace-tools__build_tn_index` with `{"lookup":"tongue"}`

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

Read `.claude/skills/issue-identification/analyst-domains.md` for domain assignments and cross-reading protocol. Spawn both analysts with `subagent_type: "issue-identification"`, `model: "opus"`, and `team_name` set.

Each analyst reads:
- ULT draft from Wave 1 (`output/AI-ULT/<BOOK>/<BOOK>-<CH>.usfm`)
- Published TN index (via `mcp__workspace-tools__build_tn_index` with `lookup`/`issue`)

Each writes their TSV to `$TMP/wave2_*.tsv`.

**Hold protocol**: After writing your TSV, send a message to team-lead confirming your file is written, then wait. You will receive:
- Challenges from the challenger agent (Wave 3) -- defend your classifications
- Verification requests from team-lead (Wave 5) -- re-check against revised ULT (only if ULT was revised)
- Queries from the UST agent (Wave 6) -- clarify issues as needed
- Do not mark your task as completed until you receive a shutdown request

Wait for both analysts to send their "file written" messages. Do NOT proceed to Wave 3 until both files exist.

Required before Wave 3:
- Both Wave 2 analyst tasks show completed via `TaskGet` or `TaskList`
- `$TMP/wave2_structure.tsv` exists
- `$TMP/wave2_rhetoric.tsv` exists

## Wave 3: Challenge and Defend

Read `.claude/skills/issue-identification/challenger-protocol.md`. Spawn the challenger (`model: "sonnet"`, name: "challenger"). The Wave 2 analysts and ULT agent are all still alive.

Pipeline-specific additions:
- The challenger also DMs `ult-gen` to ask about specific rendering decisions when relevant (e.g., "In v3 you rendered the construct chain as X -- was that a deliberate structural preservation?")
- **ULT coherence heuristic**: If Hebrew has a named grammatical structure (construct chain, passive, etc.), ULT should preserve it literally. If it's just word order with no structural name, ULT can use natural English.
- The challenger notes any ULT revisions needed (passed to orchestrator for Wave 4b).

After writing rulings, the challenger sends "Rulings complete" to each analyst. Analysts continue holding for Wave 5.

Send `shutdown_request` to the challenger after rulings are written -- it has no further role.

Output: `$TMP/wave3_challenges.tsv`

Required before Wave 4a:
- Challenger task shows completed via `TaskGet` or `TaskList`
- `$TMP/wave3_challenges.tsv` exists

## Wave 4a: Merge

Read `.claude/skills/issue-identification/merge-procedure.md`. Orchestrator merges all findings. Writes `$TMP/merged_issues.tsv`.

Required before Wave 4b:
- `$TMP/merged_issues.tsv` exists

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

Two coherence patterns guide what to include in the revision instructions:
1. ULT unnecessarily preserves Hebrew form (no named grammatical structure) → adjust ULT, drop the corresponding issue
2. ULT incorrectly flattens a named Hebrew structure (construct chain, passive, etc.) → correct ULT to preserve it, keep the issue

This is more natural than a separate agent applying changes -- the original translator revises their own work with specific feedback.

Wait for the ULT agent's confirmation before proceeding.

Required before Wave 5 or final issues write:
- `ult-gen` task is still alive and has responded
- revised `output/AI-ULT/<BOOK>/<BOOK>-<CH>.usfm` exists

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

Required before Wave 6:
- If Wave 5 ran, both analyst verification tasks show completed
- `output/issues/<BOOK>/<BOOK>-<CH>.tsv` exists

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

Required before returning success:
- `ust-gen` task shows completed via `TaskGet` or `TaskList`
- `output/AI-UST/<BOOK>/<BOOK>-<CH>.usfm` exists
- `output/issues/<BOOK>/<BOOK>-<CH>.tsv` exists
- `output/AI-ULT/<BOOK>/<BOOK>-<CH>.usfm` exists

## Wave 7: Gemini Review (optional, activation only)

Read `.claude/skills/issue-identification/gemini-review-wave.md`. Only run if `--gemini` is explicitly passed. Skip by default.

Pipeline runs three stages: `ult`, `issues`, and `ust`.
In restricted shell-less environments, keep Wave 7 disabled unless a dedicated workspace MCP tool is added for Gemini review.

## Cleanup

After Wave 7 (or Wave 6 if Gemini was not requested):
1. Send `shutdown_request` to all live teammates (ult-gen, structure, rhetoric, ust-gen; and challenger if still alive)
2. Wait for shutdown confirmations
3. `TeamDelete` to clean up team resources

Do not treat cleanup as optional. The orchestrator remains responsible for the
team until shutdown is complete.

## Troubleshooting

- **Agent never sends "file written" message**: The sub-agent may have stalled or encountered an error silently. Check the agent's output log. If the agent is idle, send it a follow-up message asking for status. Restart the agent if unresponsive after 2 attempts.
- **ULT agent does not respond to revision requests**: The agent may have lost context. Re-send the revision request with the full file path and specific line numbers. If still unresponsive, terminate and re-spawn the agent.
- **Team cleanup fails**: Orphaned agent processes can remain after pipeline completion. Use `TeamDelete` to clean up, or manually check `~/.claude/teams/` for stale team files.
- **You launched agents and are now "waiting"**: Use `TaskGet` or `TaskList` immediately. Do not end the task while waiting for background teammates.

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
