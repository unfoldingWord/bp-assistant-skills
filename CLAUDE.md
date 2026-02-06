Check your environment. You are probably in windows. You may be in WSL.
Don't use emojis, it breaks windows terminal.

## Workflow Expectations
- When exploring or analyzing, write findings incrementally to a file rather than holding everything in context. Even interrupted sessions should leave a usable artifact.
- Before multi-step exploration, outline a short plan and confirm direction.
- When working on skills, check `.claude/skills/` for existing patterns before proposing new approaches.
- Plans have two tiers: an **approval plan** (concise, what/why, shown to user) and an **execution plan** (full detail, exact changes, saved to scratchpad so it survives context clears). The approval plan should reference the scratchpad file path.
- Script first design. If something can be scripted when making skills or otherwise working, script it, it is more accurate (if the script is written correctly).

## Primary Tasks
You are either being asked to:
1) Assist with creation of unfoldingWord Book Package items including the unfoldingWord Literal Text, unfoldingword Simplified Text, translation notes, or possibly translation questions. You will have skills for each of these, the top level skills may lead you to other skills.
2) Develop or improve the skills markdown files for task 1.

- Take a light hand to skill edits. Avoid all caps, or 'critical' type language. If an issue is underrepresented we want to nudge not shove.

## Project Structure

### Skills (in `.claude/skills/`)
- `pipeline-overview/` - Orchestration and workflow guidance
- `ULT-gen/` - Hebrew USFM to literal English translation
- `ULT-alignment/` - Word-level Hebrew-to-ULT alignment
- `UST-gen/` - T4T to meaning-based simplified translation
- `UST-alignment/` - Phrase-level Hebrew-to-UST alignment
- `issue-identification/` - 94 translation issue type skills (complete)
- `issue-to-tn/` - Convert identified issues to translation notes
- `repo-insert/` - Insert content into Door43 repos, commit, create PRs
- `create-issue-description/` - Create new issue identification skills
- `tn-writer/` - Translation note generation (script-first architecture)
- `hebrew-reference/` - Hebrew language reference (placeholder)
- `utilities/` - Shared scripts (alignment, USFM parsing, Proskomma, fetch tools)

### Data (in `data/`)
Data Files (Not in Git)

The project uses extensive data files that are gitignored but available locally:

#### Data Directories
All paths relative to project root. These directories exist locally but are not tracked in git:

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
- `output/` - Generated files and reports (gitignored)
- `tmp/` - Temporary processing files

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
- ALWAYS `git add` and `git commit` new files immediately after creating them (not in output folders)
- Run `git status` before any branch operation (checkout, reset, merge, rebase)
- NEVER do `git reset --hard` or `git clean` without checking for untracked files first
