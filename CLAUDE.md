You may be running locally (Windows/WSL) or headlessly inside a Docker container on an OCI ARM64 server via a Zulip bot.
Don't use emojis, it breaks windows terminal.

**Knowledge domain**: `work` (Bible translation, unfoldingWord, Wycliffe).

## Workflow Expectations
- When running as a Zulip bot (detected by mentions or chat-like prompts):
  - **Mention the user** at the start of your final response: @**Name**.
  - **Lead with the results**: Put the most important summary, file links, or links to GatewayEdit/tcCreate at the top.
  - **Be concise**: Use bullet points for findings. Avoid preambles and do NOT end with suggestions or questions.
  - **Editor Review**: For editor-compare, specifically list the preferences identified and which instructions or glossary items were updated.

## Primary Tasks
You are either being asked to:
1) Assist with creation of unfoldingWord Book Package items including the unfoldingWord Literal Text, unfoldingword Simplified Text, translation notes, or possibly translation questions. You will have skills for each of these, the top level skills may lead you to other skills.
2) Develop or improve the skills markdown files for task 1.

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

### Data (in `data/`)
Data Files (Not in Git)

The project uses extensive data files that are not gitignored so you can see them, but should never be commited or pushed:

#### Data Directories
All paths relative to project root. These directories exist locally but should not tracked in git:

- `data/en_tw/` - English Translation Words
- `data/published-tns/` - Published Translation Notes  
- `data/ta-flat/` - Translation Academy (flat format)
- `data/published_ult/` - Published ULT (Hebrew)
- `data/published_ult_english/` - Published ULT (English)
- `data/published_ust/` - Published UST (Hebrew)
- `data/published_ust_english/` - Published UST (English)
- `data/hebrew_bible/` - Hebrew source texts
- `data/glossary/` - Glossary data
- `data/editor-feedback/` - Editor feedback and corrections
- `data/t4t/` - Translation for Translators data
- `data/cache/` - Generated indexes (Strong's index JSON, ~4MB)
- `data/quick-ref/` - Accumulated decisions from ULT-gen runs (CSV)

#### Output Directories
- `output/` - Generated files and reports 
- `tmp/` - Temporary processing files - you are often in sandbox mode and should use this

**Output Folder Organization**: Always use book subfolders (e.g., `output/AI-ULT/PSA/PSA-061.usfm`, `output/issues/PSA/PSA-061.tsv`, `output/notes/PSA/PSA-061.tsv`). Never put files flat in the type directory. This applies to all output subdirectories: `AI-ULT`, `AI-UST`, `AI-UST/hints`, `issues`, `notes`, `tq`, `quality`, `review`, `editor-compare`.

#### Other files
- `translation-issues.csv` - All 94 translation issues (complete)
- `glossary/` - Hebrew vocabulary, biblical phrases, measurements, sacrifice terminology
- `hebrew_bible/` - Hebrew USFM with Strong's numbers and morphology
- `ta-flat/` - Translation Academy articles
- `issues_resolved.txt`, `templates.csv` - Cached reference data (auto-fetched daily)

#### When Working With Data
When asked to analyze or process data, look for files in these directories even though they won't appear in @-mention autocomplete. You can use bash commands to explore them:
```bash
ls -la data/published_ult_english/
find data/ -name "*.usfm"
```

## Git Discipline
- The remote is named `github`, not `origin`. Always use `git push github` (not `git push`).
- ALWAYS `git add` and `git commit` new files immediately after creating them (not in output, data, tmp folders)
- Run `git status` before any branch operation (checkout, reset, merge, rebase)
- NEVER do `git reset --hard` or `git clean` without checking for untracked files first
- After making changes to skills or config, always suggest a commit to the user.

## Bot Safety
- The bot runs as a Docker container. Before any rebuild/restart, always check `sudo docker logs zulip-bot --tail 30` for active pipelines. Look for `[notes] Running`, `[generate] Processing`, or `[claude-runner] Starting` without a corresponding completion. A restart kills in-progress work.
