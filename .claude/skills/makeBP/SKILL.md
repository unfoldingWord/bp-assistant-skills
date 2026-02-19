---
name: makeBP
description: End-to-end Book Package generation for a chapter, orchestrating all pipeline stages from ULT through repo-insert. Use when asked to make a book package, run everything for a chapter, or generate and push all content.
---

# Make Book Package

Generate a complete Book Package for a single chapter and push to Door43.

## Model Assignments

| Phase | Skill | Model | Rationale |
|-------|-------|-------|-----------|
| 1 | initial-pipeline | sonnet | Coordination + Wave 4a merge logic |
| 2 | chapter-intro | sonnet | Short templated writing, medium complexity |
| 2 | tq-writer | sonnet | Updating existing Q&A, constrained task |
| 2 | ULT-alignment | sonnet | Rule-based with linguistic judgment |
| 2 | UST-alignment | sonnet | Hints-guided phrase mapping |
| 3 | tn-writer | **opus** | Primary deliverable; Hebrew quote matching and AT writing require deep reasoning |
| 4 | repo-insert (x4) | **haiku** | Pure git operations, no reasoning needed |

## Context Window Strategy

The orchestrator (this agent) stays lightweight. Every generation phase runs as
a **Task subagent** so its work happens in a separate context window. The
orchestrator only holds:
- This skill (~200 lines)
- Task launch/result messages (~1-2k tokens each)
- A few bash script outputs for prep work

Never invoke sub-skills inline (via the Skill tool). Always delegate to Task
subagents. This keeps the orchestrator's context free for coordination across
all phases.

## Arguments

`/makeBP <book> <chapter> <username>`

| Argument | Example | Description |
|----------|---------|-------------|
| book | psa | Book abbreviation (3-letter) |
| chapter | 149 | Chapter number |
| username | deferredreward | Door43 username for commit message attribution |
| *(no mode flags)* | | *Issue-id always uses 2 analysts* |

## Setup

Normalize parameters:
- `BOOK` = uppercase 3-letter code (PSA)
- `CHAPTER` = plain number (149)
- `CH` = zero-padded for filenames (3 digits for PSA: `149`, 2 digits for other books: `03`)
- `USERNAME` = as provided (used in commit messages for attribution)

Load environment:
```bash
eval $(grep -v '^#' .env | xargs -d '\n' printf 'export %s\n')
```

## Dependency Graph

```
Phase 1: /initial-pipeline ──→ ULT + issues + UST        [1 Task subagent]
              │
Phase 2: ─────┼──→ /chapter-intro ──────┐                [4 Task subagents]
(parallel)    ├──→ /tq-writer            │
              ├──→ /ULT-alignment ───────┤
              └──→ /UST-alignment ───────┤
                                         ↓
Phase 3: ──────────→ /tn-writer (needs intro + alignments) [1 Task subagent]
              │
Phase 4: ─────┴──→ /repo-insert (all content, parallel)  [4 Task subagents]
```

Phase 3 starts after chapter-intro AND both ULT-alignment AND UST-alignment
complete. The tn-writer needs the aligned ULT for quote conversion (local file
instead of remote API), and the aligned UST to verify ATs don't duplicate
UST phrasing.

Total subagents across the run: 10 (sequential phases, not all at once).

## Phase 1: Initial Pipeline

Launch a **Task subagent** (`subagent_type: general-purpose`, `model: "sonnet"`) with a prompt to
invoke `/initial-pipeline {BOOK} {CHAPTER}` and follow its SKILL.md. The initial-pipeline skill manages
its own internal 6-wave team (ULT draft, adversarial issue-id,
challenge/defend, merge, ULT revision, verification, UST generation).

The subagent's context handles all that complexity. The orchestrator just waits
for completion and checks that the output files exist.

**Outputs to verify:**
- `output/AI-ULT/{BOOK}/{BOOK}-{CH}.usfm` -- revised ULT
- `output/AI-UST/{BOOK}/{BOOK}-{CH}.usfm` -- UST
- `output/issues/{BOOK}/{BOOK}-{CH}.tsv` -- verified issues

## Between Phases: Prepare Plain Text

The orchestrator runs these directly (small bash commands, no context cost):

```bash
node .claude/skills/utilities/scripts/usfm/parse_usfm.js \
  output/AI-ULT/{BOOK}/{BOOK}-{CH}.usfm --plain-only > /tmp/claude/ult_plain.usfm
node .claude/skills/utilities/scripts/usfm/parse_usfm.js \
  output/AI-UST/{BOOK}/{BOOK}-{CH}.usfm --plain-only > /tmp/claude/ust_plain.usfm
```

Determine verse count for repo-insert later:
```bash
LAST_VERSE=$(grep -oP '\\v \K[0-9]+' output/AI-ULT/{BOOK}/{BOOK}-{CH}.usfm | tail -1)
```

## Phase 2: Parallel Generation

Launch four **Task subagents** in parallel (`subagent_type: general-purpose`).
Each agent gets a prompt telling it to invoke the skill and providing all
file paths. Each runs in its own context window.

| Agent | Skill to invoke | Model | Key inputs | Output |
|-------|----------------|-------|-----------|--------|
| Chapter Intro | `/chapter-intro {BOOK} {CHAPTER}` | sonnet | ULT, UST, issues from Phase 1 | Inserts intro row into `output/issues/{BOOK}/{BOOK}-{CH}.tsv` |
| TQ Writer | `/tq-writer` | sonnet | ULT, UST | `output/tq/{BOOK}/{BOOK}-{CHAPTER}.tsv` |
| ULT Alignment | `/ULT-alignment` | sonnet | `output/AI-ULT/{BOOK}/{BOOK}-{CH}.usfm` + Hebrew source | `output/AI-ULT/{BOOK}/{BOOK}-{CH}-aligned.usfm` |
| UST Alignment | `/UST-alignment` | sonnet | `output/AI-UST/{BOOK}/{BOOK}-{CH}.usfm` + Hebrew source + `output/AI-UST/hints/{BOOK}/{BOOK}-{CH}.json` | `output/AI-UST/{BOOK}/{BOOK}-{CH}-aligned.usfm` |

**Each agent prompt should include:**
- Book, chapter, and padded chapter values
- Paths to all input files
- Expected output path
- Instruction to invoke the skill via the Skill tool and follow its SKILL.md

Run the chapter-intro agent without `run_in_background` so the orchestrator
knows when it completes. The other three can run in the background if desired.

## Between Phase 2 and 3: Validate Brackets

After ULT-alignment completes, run the bracket validator to catch words
incorrectly marked as implied when they actually translate a Hebrew prefix:

```bash
python3 .claude/skills/utilities/scripts/validate_ult_brackets.py \
  output/AI-ULT/{BOOK}/{BOOK}-{CH}-aligned.usfm
```

If issues are found, fix the aligned USFM before proceeding to tn-writer.
Typical fix: remove curly braces from words like `{in}` that align to a
prefixed Strong's number (e.g. `b:H6951` where `b` = "in").

## Phase 3: TN Writer

After **chapter-intro**, **ULT-alignment**, and **UST-alignment** all complete,
launch the tn-writer **Task subagent**. The tn-writer needs: the intro row in
the issues TSV, the aligned ULT for local quote conversion (avoids empty Quote
columns from remote API mismatch), and the aligned UST for AT verification.
Do not wait for tq-writer.

The tn-writer's `prepare_notes.py` accepts `--aligned-usfm` to extract Hebrew
quotes directly from the aligned ULT instead of roundtripping through
`lang_convert.js`. This eliminates QUOTE_NOT_FOUND errors caused by differences
between our AI-generated ULT and the published Door43 master.

| Agent | Skill to invoke | Model | Key inputs | Output |
|-------|----------------|-------|-----------|--------|
| TN Writer | `/tn-writer` | **opus** | `output/issues/{BOOK}/{BOOK}-{CH}.tsv` (with intro), `/tmp/claude/ult_plain.usfm`, `/tmp/claude/ust_plain.usfm`, `output/AI-ULT/{BOOK}/{BOOK}-{CH}-aligned.usfm` | `output/notes/{BOOK}/{BOOK}-{CH}.tsv` |

Wait for this agent plus any remaining Phase 2 agents to complete before
proceeding.

## Phase 4: Repo Insert (Push to Master)

After all agents complete, insert each content type into Door43 repos.
Launch four **Task subagents** in parallel (`model: "haiku"` -- pure git operations, no reasoning needed).

All repos are under the **unfoldingWord** organization on Door43. Never push
to a personal fork.

| Content | Source | Repo | Branch | Insert script |
|---------|--------|------|--------|---------------|
| ULT (aligned) | `output/AI-ULT/{BOOK}/{BOOK}-{CH}-aligned.usfm` | unfoldingWord/en_ult | `AI-{BOOK}-{CH}` (staging) -> master | `insert_usfm_verses.py` |
| UST (aligned) | `output/AI-UST/{BOOK}/{BOOK}-{CH}-aligned.usfm` | unfoldingWord/en_ust | `AI-{BOOK}-{CH}` (staging) -> master | `insert_usfm_verses.py` |
| TN | `output/notes/{BOOK}/{BOOK}-{CH}.tsv` | unfoldingWord/en_tn | `AI-{BOOK}-{CH}` (staging) -> master | `insert_tn_rows.py` |
| TQ | `output/tq/{BOOK}/{BOOK}-{CHAPTER}.tsv` | unfoldingWord/en_tq | `AI-{BOOK}-{CH}` (staging) -> master | `insert_tn_rows.py` |

### Git procedure for each repo (strict order)

1. **Ensure remote points to unfoldingWord** -- verify the origin URL contains
   `git.door43.org/unfoldingWord/{repo}`. If it points to a fork, fix it:
   ```bash
   git remote set-url origin "https://${DOOR43_USERNAME}:${DOOR43_TOKEN}@git.door43.org/unfoldingWord/{repo}.git"
   ```
2. **Fetch** -- `git fetch origin`
3. **Create staging branch from origin/master** -- always branch from
   `origin/master`. Delete any stale local branch with the same name first.
   ```bash
   git checkout --detach 2>/dev/null
   git branch -D "$BRANCH" 2>/dev/null || true
   git checkout -b "$BRANCH" origin/master
   ```
4. **Insert** -- run the appropriate script with `--backup`
   - USFM: `--chapter {CHAPTER} --verses {FIRST}-{LAST_VERSE}`
   - TSV: no verse filter needed (script matches by reference)
5. **Verify** -- log `git diff --stat` output
6. **Commit** -- `git add {file} && git commit -m "AI {content_type} for {BOOK} {CHAPTER}"`
7. **Merge to master and push**:
   ```bash
   git checkout master
   git merge origin/master --ff-only
   git merge "$BRANCH" --no-edit
   git push origin master
   git branch -D "$BRANCH"
   ```
8. **If push fails** (remote advanced): `git pull origin master --no-edit` then retry push once
9. **If merge conflict or second push fails**: stop and report error to admin

### Repo-insert commands reference

```bash
REPOS="$DOOR43_REPOS_PATH"

# ULT
python3 .claude/skills/repo-insert/scripts/insert_usfm_verses.py \
  --book-file "$REPOS/en_ult/{BOOK_NUM}-{BOOK}.usfm" \
  --source-file output/AI-ULT/{BOOK}/{BOOK}-{CH}-aligned.usfm \
  --chapter {CHAPTER} --verses {FIRST}-{LAST_VERSE} --backup

# UST
python3 .claude/skills/repo-insert/scripts/insert_usfm_verses.py \
  --book-file "$REPOS/en_ust/{BOOK_NUM}-{BOOK}.usfm" \
  --source-file output/AI-UST/{BOOK}/{BOOK}-{CH}-aligned.usfm \
  --chapter {CHAPTER} --verses {FIRST}-{LAST_VERSE} --backup

# TN
python3 .claude/skills/repo-insert/scripts/insert_tn_rows.py \
  --book-file "$REPOS/en_tn/tn_{BOOK}.tsv" \
  --source-file output/notes/{BOOK}/{BOOK}-{CH}.tsv --backup

# TQ
python3 .claude/skills/repo-insert/scripts/insert_tn_rows.py \
  --book-file "$REPOS/en_tq/tq_{BOOK}.tsv" \
  --source-file output/tq/{BOOK}/{BOOK}-{CHAPTER}.tsv --backup
```

Book numbers for filenames (from `fetch_door43.py` BOOK_NUMBERS mapping):
PSA = `19-PSA.usfm`, GEN = `01-GEN.usfm`, etc.

## Output Summary

| Content | Local path | Repo | Pushed to |
|---------|-----------|------|-----------|
| ULT (aligned) | `output/AI-ULT/{BOOK}/{BOOK}-{CH}-aligned.usfm` | en_ult | master |
| UST (aligned) | `output/AI-UST/{BOOK}/{BOOK}-{CH}-aligned.usfm` | en_ust | master |
| TN | `output/notes/{BOOK}/{BOOK}-{CH}.tsv` | en_tn | master |
| TQ | `output/tq/{BOOK}/{BOOK}-{CHAPTER}.tsv` | en_tq | master |
| Issues | `output/issues/{BOOK}/{BOOK}-{CH}.tsv` | -- | working file only |
| ULT (unaligned) | `output/AI-ULT/{BOOK}/{BOOK}-{CH}.usfm` | -- | not inserted |
| UST (unaligned) | `output/AI-UST/{BOOK}/{BOOK}-{CH}.usfm` | -- | not inserted |

## Error Handling

If any phase fails:
1. Stop the pipeline and report which phases completed vs failed
2. All completed outputs remain in `output/` for inspection
3. Repo insertions only happen after all generation phases succeed
4. If a push to master fails after one retry, stop and report to admin

## Unattended Operation

This pipeline runs without user interaction:
- Repo-insert skips dry-run confirmation prompts
- Git diffs are logged but do not require approval
- Each phase validates its outputs before proceeding
