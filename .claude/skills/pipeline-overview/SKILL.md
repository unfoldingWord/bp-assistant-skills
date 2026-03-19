---
name: pipeline-overview
description: Overview of the unfoldingWord Book Package pipeline. Use when asking which skill handles a task, how pipeline stages connect, or what the workflow order is.
---

# Pipeline Overview

## Purpose
This skill provides an overview of the unfoldingWord Book Package creation pipeline and guides you to the appropriate specialized skill for each stage.

## The Nine-Stage Pipeline

The full book package pipeline (`makeBP`) orchestrates these stages with maximum parallelization:

| Stage | Skill | Description |
|-------|-------|-------------|
| 1. Literal Translation | `ULT-gen` | Hebrew USFM to literal English (ULT) |
| 2. Issue Identification | `issue-identification` | Find translation issues across 94 issue types |
| 3. Simplified Translation | `UST-gen` | T4T to meaning-based English (UST) |
| 4. Chapter Introduction | `chapter-intro` | Translator-oriented chapter intros |
| 5. Translation Notes | `tn-writer` | Generate notes from identified issues |
| 6. Translation Questions | `tq-writer` | Update Q&A content for current ULT/UST |
| 7. ULT Alignment | `ULT-alignment` | Word-level Hebrew-to-ULT alignment |
| 8. UST Alignment | `UST-alignment` | Phrase-level Hebrew-to-UST alignment |
| 9. Repo Insertion | `repo-insert` | Insert into Door43 repos, commit, create PRs |

## When to Use Each Skill

| Task | Skill |
|------|-------|
| Creating ULT text | `ULT-gen` |
| Finding what needs notes | `issue-identification` (agent) |
| Creating UST text | `UST-gen` |
| Writing chapter introductions | `chapter-intro` |
| Writing translation notes | `tn-writer` |
| Checking note quality | `tn-quality-check` |
| Writing notes for long chapters | `parallel-batch` |
| Quick one-off note writing | `tn-quick` |
| Updating translation questions | `tq-writer` |
| Aligning ULT to Hebrew | `ULT-alignment` |
| Aligning UST to Hebrew | `UST-alignment` |
| Running both alignments | `align-all-parallel` |
| Pushing to Door43 | `repo-insert` |
| Verifying a Door43 push | `repo-verify` |
| Comparing AI vs editor output | `editor-compare` |
| Getting a second opinion | `gemini-review` |
| Creating a new issue type | `create-issue-description` |
| Adversarial issue-id on human text | `deep-issue-id` |
| Reconciling issues after human edits | `post-edit-review` |

## Orchestrators

### makeBP (`/makeBP`)
End-to-end book package for a chapter. Runs all 9 stages with maximum parallelization and model assignments per stage.

**Skill**: `.claude/skills/makeBP/SKILL.md`

### Initial Pipeline (`/initial-pipeline`)
Coordinates ULT-gen, issue-id, and UST-gen as a team for a chapter. 6-wave pipeline with adversarial issue identification, ULT feedback loop, and UST generated last (so it can model handling identified issues). Always uses 2-analyst adversarial issue identification with challenger.

**Skill**: `.claude/skills/initial-pipeline/SKILL.md`

### Post-Human-Edit Review (`/post-edit-review`)
After humans edit ULT/UST, adapts existing issues to match their changes. Diff-based review that drops, updates, or adds issues without re-running full identification.

**Skill**: `.claude/skills/post-edit-review/SKILL.md`

### Parallel Batch (`/parallel-batch`)
Split long chapters (50+ issues, e.g. PSA 119) into verse-range chunks and run tn-writer in parallel, then merge results.

**Skill**: `.claude/skills/parallel-batch/SKILL.md`

## Common Workflows

### "Run the full pipeline for [passage]"
Use `/makeBP` for end-to-end, or `/initial-pipeline` for just ULT + issues + UST.

### "Humans edited the ULT/UST, update issues"
Use `/post-edit-review` to reconcile issues with human changes.

### "Write notes for [passage]"
Use `/write-notes` via Zulip, or manually: run `issue-identification`, then `tn-writer`, then `tn-quality-check`.

### "Compare what the editor changed"
Use `/editor-compare` to identify systematic preferences and update glossary/quick-ref.

### "Push content to Door43"
Use `/repo-insert` to insert into repo clones, commit, and create PRs. Then `/repo-verify` to confirm.

### "Create skill for [issue type]"
Use `/create-issue-description` to create a new identification skill.

## Supporting Skills

### Utilities
Shared scripts: USFM parsing (usfm-js), Proskomma queries, alignment validation, Hebrew Bible fetching, Strong's index building, curly quotes, and more.

**Skill**: `.claude/skills/utilities/SKILL.md`

### Hebrew Reference
Reference material for Hebrew language patterns and vocabulary. (Placeholder -- to be developed.)

**Skill**: `.claude/skills/hebrew-reference/SKILL.md`

## Authoritative Sources

All skills draw from these sources (in order of authority):
1. **Issues Resolved** (`data/issues_resolved.txt`) -- Content team decisions (final authority)
2. **TN Templates** (`data/templates.csv`) -- Official note templates
3. **Canonical Glossary CSVs** (read-only; never modified by AI)
4. **Prior Rendering Decisions** (`data/quick-ref/`) -- Accumulated per-run decisions
5. **Published Translation Notes** -- Human-identified examples
6. **Translation Academy** (`data/ta-flat/`) -- Definitions and explanations
7. **Editor Feedback** (`data/editor-feedback/`) -- Accumulated preferences from editor-compare runs
