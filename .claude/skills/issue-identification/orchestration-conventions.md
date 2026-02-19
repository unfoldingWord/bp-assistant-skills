# Orchestration Conventions

Shared conventions for multi-agent issue-identification orchestrators
(deep-issue-id and initial-pipeline).

## Chapter Padding

Zero-pad the chapter number for all filenames: 3 digits for PSA (e.g., `067`),
2 digits for other books (e.g., `03`). Use `<CH>` to mean the padded form.
This matches makeBP's convention so output files are found by downstream phases.

## Model Assignments

| Role | Model | Rationale |
|------|-------|-----------|
| Orchestrator | sonnet | Coordination and merge logic |
| Analysts (Wave 2) | opus | Deep Hebrew linguistic classification |
| Challenger (Wave 3) | sonnet | Structured deduplication and ruling |

## Orchestrator Patience

Agents take time. Do not:
- Send shutdown requests until ALL waves are complete and final outputs are written
- Send duplicate messages or nudge too quickly
- Proceed to the next wave until the current wave's agents confirm completion

Do:
- Wait for each agent's confirmation message before proceeding
- Allow agents time to cross-read and interact
- You may gently nudge agents, or ask what they are waiting for if they seem stuck

## Team Tool-Call Rules

`TeamCreate`, `SendMessage`, `shutdown_request`, and `TeamDelete` are direct
orchestrator tool calls -- never delegate them to a subagent.
