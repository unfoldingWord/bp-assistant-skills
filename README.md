# BP Assistant Skills

[![GitHub](https://img.shields.io/badge/github-unfoldingWord%2Fbp--assistant--skills-blue)](https://github.com/unfoldingWord/bp-assistant-skills)

AI-assisted creation of unfoldingWord Book Packages (BP) -- ULT, UST, translation notes, translation questions, chapter intros, and word-level alignments -- driven entirely by Claude Code skills.

**Companion repo:** [bp-assistant](https://github.com/unfoldingWord/bp-assistant) -- Zulip bot that orchestrates these skills via the Claude Agent SDK.

## Architecture

The system runs as a **Zulip bot** inside a Docker container on an OCI ARM64 server. Users trigger pipelines via Zulip messages; Claude Code executes the appropriate skills. It can also run locally under Windows/WSL for development.

**Design philosophy: code where verifiable, prompts where judgment is needed.** Deterministic scripts handle mechanical, verifiable tasks (USFM parsing, Hebrew quote extraction, TSV splitting/merging, ID generation, git operations, Door43 push). LLM prompts handle semantic decisions requiring linguistic judgment (translation, issue identification, note writing). This split evolved from experience -- AI was unreliable and slow at deterministic tasks (confabulating git results, botching file operations), while scripts couldn't handle the contextual judgment calls. The `test-poc` skill exists to A/B test where the boundary falls for new tasks.

## Getting Started

### Setup

```bash
# Clone the repo
git clone https://github.com/unfoldingWord/bp-assistant-skills.git
cd bp-assistant-skills

# Install Node dependencies (used by utility scripts)
npm install

# Fetch reference data (Hebrew Bible, Translation Words, etc.)
# These are gitignored and must be fetched separately:
python3 .claude/skills/utilities/scripts/fetch_hebrew_bible.py
python3 .claude/skills/utilities/scripts/build_strongs_index.py
# Other data directories (en_tw, published-tns, ta-flat, etc.) should be
# cloned from their respective Door43 repos into data/
```

### Running skills interactively

Skills are designed to run under Claude Code. Start a session in the repo root:

```bash
claude
```

Then ask Claude to run any skill, e.g., "generate ULT for PSA 23" or "write notes for HAB 3".

### Running via the bot

When deployed alongside the [bp-assistant](https://github.com/unfoldingWord/bp-assistant) bot, skills are invoked automatically via Zulip commands. The bot mounts this repo at `/workspace` inside Docker and uses the Claude Agent SDK to execute skills.

## Pipeline Overview

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

The `initial-pipeline` skill runs stages 1-3 as a coordinated 6-wave pipeline with an adversarial issue identification loop and ULT feedback.

## Skills

All skills live in `.claude/skills/`. Each has a `SKILL.md` defining the prompt and a `scripts/` directory for deterministic tooling.

### Core Generation
- **`ULT-gen`** -- Hebrew USFM to highly literal English preserving source form and structure
- **`UST-gen`** -- T4T to natural meaning-based English with implicit information made explicit
- **`chapter-intro`** -- Translator-oriented chapter introductions

### Issue Identification
- **`issue-identification`** -- 94 translation issue types (figures of speech, abstract nouns, grammatical patterns, cultural concepts), each with its own skill file
- **`deep-issue-id`** -- Multi-agent adversarial issue identification: 2 domain analysts (structure + rhetoric) + challenger. Supports `--verses` for chunked analysis
- **`post-edit-review`** -- Diff-based adaptation of issues after human edits to ULT/UST

### Note & Question Writing
- **`tn-writer`** -- Deterministic prep script + LLM note generation following style guide
- **`tn-quality-check`** -- Mechanical checks (ID format, Hebrew quotes, AT syntax, bold accuracy) plus optional deep semantic review
- **`parallel-batch`** -- Split long chapters into verse-range chunks, run tn-writer in parallel, merge results (respects PSA 119 stanza boundaries)
- **`tq-writer`** -- Update translation questions to align with current ULT/UST

### Alignment
- **`ULT-alignment`** -- Word-level Hebrew-to-ULT; AI produces index-based JSON, script converts to aligned USFM
- **`UST-alignment`** -- Phrase-level Hebrew-to-UST with radical restructuring and implied information handling
- **`align-all-parallel`** -- Run both alignments in parallel as subagents

### Orchestration
- **`makeBP`** -- End-to-end book package for a chapter with maximum parallelization
- **`initial-pipeline`** -- 6-wave coordinated pipeline (ULT, issues, UST) with adversarial feedback loop
- **`pipeline-overview`** -- Guides to the appropriate skill for each stage

### Review & Feedback
- **`editor-compare`** -- Compare editor-edited ULT/UST against AI output; identifies preferences and feeds them back into glossary and skill instructions. Protects canonical files from modification with a write-guard and weekly refresh check.
- **`gemini-review`** -- Independent Gemini-based second-opinion reviewer across all pipeline stages
- **`test-poc`** -- A/B comparison of prompt-over-code vs previous script workflows

### Quick Tools
- **`tn-quick`** -- Quick scratchpad note writing outside the full pipeline

### Infrastructure
- **`repo-insert`** -- Insert ULT, UST, or TN content into Door43 repo clones, commit, create PRs via Gitea API
- **`repo-verify`** -- Verify that a push landed on Door43 by comparing local and remote content
- **`create-issue-description`** -- Create or update issue identification skill files
- **`utilities`** -- Shared scripts: USFM parsing (`usfm-js`), Proskomma queries, alignment validation, Hebrew Bible fetching, Strong's index building, curly quotes, and more

## Project Structure

```
.claude/
  skills/           # All skill definitions and scripts
  agents/           # Subagent definitions (issue-identification)
  hooks/            # Git hooks (check-untracked.sh)

data/               # Reference data (not committed)
  hebrew_bible/     # Hebrew USFM with Strong's numbers and morphology
  en_tw/            # English Translation Words
  published-tns/    # Published Translation Notes
  published_ult/    # Published ULT (Hebrew aligned)
  published_ust/    # Published UST (Hebrew aligned)
  t4t/              # Translation for Translators
  ta-flat/          # Translation Academy (flat format)
  glossary/         # Hebrew vocabulary, biblical phrases, measurements, sacrifices
  editor-feedback/  # Editor corrections and preference tracking
  cache/            # Generated indexes (Strong's, etc.)
  quick-ref/        # Accumulated ULT-gen decisions (CSV)

output/             # Generated files, organized by book subfolder
  AI-ULT/           # Generated ULT
  AI-UST/           # Generated UST
  issues/           # Identified translation issues (TSV)
  notes/            # Generated translation notes (TSV)
  tq/               # Translation questions
  quality/          # Quality check reports
  editor-compare/   # Editor comparison reports
```

## Deployment

In production, this repo is mounted at `/workspace` inside the [bp-assistant](https://github.com/unfoldingWord/bp-assistant) Docker container. The bot uses the Claude Agent SDK to invoke skills and push results to [Door43](https://git.door43.org). See the companion repo for bot architecture, routing, and Docker setup.

## Authoritative Sources

Skills draw from these sources (in priority order):
1. **Issues Resolved** (`data/issues_resolved.txt`) -- Content team decisions (final authority)
2. **TN Templates** (`data/templates.csv`) -- Official note templates
3. **Canonical Glossary CSVs** (read-only; never modified by AI):
   - `data/glossary/hebrew_ot_glossary.csv` -- Standard ULT/UST renderings
   - `data/glossary/psalms_reference.csv` -- Psalms-specific terms
   - `data/glossary/sacrifice_terminology.csv` -- Sacrifice and offering vocabulary
   - `data/glossary/biblical_measurements.csv` -- Weights, volumes, distances
   - `data/glossary/biblical_phrases.csv` -- Grammatical and prophetic phrases
4. **Prior Rendering Decisions** (`data/quick-ref/ult_decisions.csv`, `ust_decisions.csv`) -- Accumulated per-run decisions
5. **Published Translation Notes** -- Human-identified examples
6. **Translation Academy** (`data/ta-flat/`) -- Definitions and explanations
7. **Editor Feedback** (`data/editor-feedback/`) -- Accumulated preferences from editor-compare runs

The 5 glossary CSVs and `issues_resolved.txt` are protected from modification. `editor-compare` enforces this with a write-guard; all generation skills (ULT-gen, UST-gen, tn-writer) treat them as read-only references.

## Dependencies

- Node.js 22+ (usfm-js ^3.4.3 for USFM parsing, Proskomma for word lookups)
- Python 3.10+ (data processing, Hebrew quote extraction, quality checks)
- [Claude Code CLI](https://docs.anthropic.com/en/docs/claude-code) (Agent SDK for skill execution)
