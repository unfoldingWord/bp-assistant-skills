# Workspace — Development Context

This file is for interactive Claude Code sessions only. Skills at runtime get the root CLAUDE.md.

**Knowledge domain**: `work` (Bible translation, unfoldingWord, Wycliffe).

## Skill Editing Guidelines
- Take a light hand to skill edits. Avoid all caps, or 'critical' type language. If an issue is underrepresented we want to nudge not shove.
- When you find yourself writing paragraphs of "here's what I recommend" followed by "alternatively" or multiple options, stop and ask the user instead of deciding unilaterally. This applies even with bypass permissions on.

## Project Structure

### Skills (in `.claude/skills/`)

**Core Generation**
- `ULT-gen/` - Hebrew USFM to literal English translation
- `UST-gen/` - T4T to meaning-based simplified translation
- `chapter-intro/` - Translator-oriented chapter introductions

**Issue Identification**
- `issue-identification/` - 94 translation issue type skills (complete)
- `deep-issue-id/` - Multi-agent adversarial issue identification for human-authored text
- `post-edit-review/` - Diff-based issue adaptation after human edits to ULT/UST

**Note & Question Writing**
- `tn-writer/` - Translation note generation (scripts for mechanical extraction, prompts for semantic content)
- `tn-quality-check/` - Mechanical + semantic quality checks on generated notes
- `tn-quick/` - Quick scratchpad note writing outside the full pipeline
- `parallel-batch/` - Split long chapters into chunks, run tn-writer in parallel, merge
- `tq-writer/` - Update translation questions for current ULT/UST

**Alignment**
- `ULT-alignment/` - Word-level Hebrew-to-ULT alignment
- `UST-alignment/` - Phrase-level Hebrew-to-UST alignment
- `align-all-parallel/` - Run both alignments as parallel subagents

**Orchestration**
- `makeBP/` - End-to-end book package for a chapter (all stages)
- `initial-pipeline/` - 6-wave coordinated pipeline (ULT, issues, UST) with adversarial feedback
- `pipeline-overview/` - Guides to the appropriate skill for each stage

**Review & Feedback**
- `editor-compare/` - Compare editor-edited ULT/UST against AI output, update glossary/quick-ref
- `gemini-review/` - Independent Gemini-based second-opinion reviewer
- `test-poc/` - A/B comparison of prompt-over-code vs previous script approaches

**Infrastructure**
- `repo-insert/` - Insert content into Door43 repos, commit, create PRs
- `repo-verify/` - Verify that a push landed on Door43 by comparing local and remote
- `create-issue-description/` - Create new issue identification skills
- `utilities/` - Shared scripts (alignment, USFM parsing, Proskomma, fetch tools)
- `hebrew-reference/` - Hebrew language reference (placeholder)

## Git Discipline
- The remote is named `github`, not `origin`. Always use `git push github` (not `git push`).
- ALWAYS `git add` and `git commit` new files immediately after creating them (not in output, data, tmp folders)
- Run `git status` before any branch operation (checkout, reset, merge, rebase)
- NEVER do `git reset --hard` or `git clean` without checking for untracked files first
- After making changes to skills or config, always suggest a commit to the user.

## Bot Safety
- The bot runs as a Docker container. Before any rebuild/restart, always check `docker logs zulip-bot --tail 30` for active pipelines. Look for `[notes] Running`, `[generate] Processing`, or `[claude-runner] Starting` without a corresponding completion. A restart kills in-progress work.

