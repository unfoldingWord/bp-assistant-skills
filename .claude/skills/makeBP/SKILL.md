---
name: makeBP
description: End-to-end Book Package for a chapter. Orchestrates ULT, issues, UST, chapter intro, TN, TQ, alignments, and repo insertion with maximum parallelization.
---

# Make Book Package

Generate a complete Book Package for a single chapter and push to Door43.

## Arguments

`/makeBP <book> <chapter> <username>`

| Argument | Example | Description |
|----------|---------|-------------|
| book | psa | Book abbreviation (3-letter) |
| chapter | 149 | Chapter number |
| username | deferredreward | Door43 username for branch naming |

## Setup

Normalize parameters:
- `BOOK` = uppercase 3-letter code (PSA)
- `CHAPTER` = plain number (149)
- `CH` = zero-padded for filenames (3 digits for PSA: `149`, 2 digits for other books: `03`)
- `USERNAME` = as provided

Load environment:
```bash
eval $(grep -v '^#' .env | xargs -d '\n' printf 'export %s\n')
```

## Dependency Graph

```
Phase 1: /initial-pipeline ──→ ULT + issues + UST
              │
Phase 2: ─────┼──→ /chapter-intro ──────┐
(parallel)    ├──→ /tq-writer            │
              ├──→ /ULT-alignment        │
              └──→ /UST-alignment        │
                                         ↓
Phase 3: ──────────→ /tn-writer (needs intro row)
              │
Phase 4: ─────┴──→ /repo-insert (all content, parallel)
```

Phases 2 and 3 overlap: tq-writer and alignments keep running while tn-writer
starts after chapter-intro finishes.

## Phase 1: Initial Pipeline

Invoke `/initial-pipeline {BOOK} {CHAPTER}`.

This runs the 6-wave team internally (ULT draft, adversarial issue-id,
challenge/defend, merge, ULT revision, verification, UST generation).

**Outputs:**
- `output/AI-ULT/{BOOK}-{CH}.usfm` -- revised ULT
- `output/AI-UST/{BOOK}-{CH}.usfm` -- UST
- `output/issues/{BOOK}-{CH}.tsv` -- verified issues

## Between Phases: Prepare Plain Text

Create plain-text ULT/UST for tn-writer and tq-writer:

```bash
node .claude/skills/utilities/scripts/usfm/parse_usfm.js \
  output/AI-ULT/{BOOK}-{CH}.usfm --plain-only > /tmp/claude/ult_plain.usfm
node .claude/skills/utilities/scripts/usfm/parse_usfm.js \
  output/AI-UST/{BOOK}-{CH}.usfm --plain-only > /tmp/claude/ust_plain.usfm
```

Determine verse count for repo-insert later:
```bash
LAST_VERSE=$(grep -oP '\\v \K[0-9]+' output/AI-ULT/{BOOK}-{CH}.usfm | tail -1)
```

## Phase 2: Parallel Generation

Launch four agents in parallel using the Task tool (`subagent_type: general-purpose`).
Each agent invokes its skill and follows that skill's full workflow.

| Agent | Skill to invoke | Key inputs | Output |
|-------|----------------|-----------|--------|
| Chapter Intro | `/chapter-intro {BOOK} {CHAPTER}` | ULT, UST, issues from Phase 1 | Inserts intro row into `output/issues/{BOOK}-{CH}.tsv` |
| TQ Writer | `/tq-writer` | ULT, UST | `output/tq/{BOOK}-{CHAPTER}.tsv` |
| ULT Alignment | `/ULT-alignment` | `output/AI-ULT/{BOOK}-{CH}.usfm` + Hebrew source | `output/AI-ULT/{BOOK}-{CH}-aligned.usfm` |
| UST Alignment | `/UST-alignment` | `output/AI-UST/{BOOK}-{CH}.usfm` + Hebrew source | `output/AI-UST/{BOOK}-{CH}-aligned.usfm` |

**Agent prompts should include:**
- Book, chapter, and padded chapter values
- Paths to all input files
- Expected output path
- Instruction to invoke the skill and follow its SKILL.md

## Phase 3: TN Writer

After the **chapter-intro agent** completes (intro row must exist in issues TSV),
launch the tn-writer agent. Do not wait for tq-writer or alignments.

| Agent | Skill to invoke | Key inputs | Output |
|-------|----------------|-----------|--------|
| TN Writer | `/tn-writer` | `output/issues/{BOOK}-{CH}.tsv` (with intro), `/tmp/claude/ult_plain.usfm`, `/tmp/claude/ust_plain.usfm` | `output/notes/{BOOK}-{CH}.tsv` |

## Phase 4: Repo Insert

After all agents complete, insert each content type into Door43 repos.
These can run in parallel (each touches a different repo directory).

| Content | Source | Repo | Branch | Insert script |
|---------|--------|------|--------|---------------|
| ULT (aligned) | `output/AI-ULT/{BOOK}-{CH}-aligned.usfm` | en_ult | `auto-{user}-{BOOK}` | `insert_usfm_verses.py` |
| UST (aligned) | `output/AI-UST/{BOOK}-{CH}-aligned.usfm` | en_ust | `auto-{user}-{BOOK}` | `insert_usfm_verses.py` |
| TN | `output/notes/{BOOK}-{CH}.tsv` | en_tn | `{user}-tc-create-1` | `insert_tn_rows.py` |
| TQ | `output/tq/{BOOK}-{CHAPTER}.tsv` | en_tq | `auto-{user}-{BOOK}` | `insert_tn_rows.py` |

For each content type, follow the repo-insert skill workflow:

1. **Setup repo** -- clone if needed, checkout branch (create from master or
   reset to remote), merge `origin/master`
2. **Insert** -- run the appropriate script with `--backup`
   - USFM: `--chapter {CHAPTER} --verses 1-{LAST_VERSE}`
   - TSV: no verse filter needed (script matches by reference)
3. **Verify** -- log `git diff` output
4. **Commit** -- `AI {content_type} for {BOOK} {CHAPTER}`
5. **Push** -- `git push origin {BRANCH}`

### Repo-insert commands reference

```bash
REPOS="$DOOR43_REPOS_PATH"

# ULT
python3 .claude/skills/repo-insert/scripts/insert_usfm_verses.py \
  --book-file "$REPOS/en_ult/{BOOK_NUM}-{BOOK}.usfm" \
  --source-file output/AI-ULT/{BOOK}-{CH}-aligned.usfm \
  --chapter {CHAPTER} --verses 1-{LAST_VERSE} --backup

# UST
python3 .claude/skills/repo-insert/scripts/insert_usfm_verses.py \
  --book-file "$REPOS/en_ust/{BOOK_NUM}-{BOOK}.usfm" \
  --source-file output/AI-UST/{BOOK}-{CH}-aligned.usfm \
  --chapter {CHAPTER} --verses 1-{LAST_VERSE} --backup

# TN
python3 .claude/skills/repo-insert/scripts/insert_tn_rows.py \
  --book-file "$REPOS/en_tn/tn_{BOOK}.tsv" \
  --source-file output/notes/{BOOK}-{CH}.tsv --backup

# TQ
python3 .claude/skills/repo-insert/scripts/insert_tn_rows.py \
  --book-file "$REPOS/en_tq/tq_{BOOK}.tsv" \
  --source-file output/tq/{BOOK}-{CHAPTER}.tsv --backup
```

Book numbers for filenames (from `fetch_door43.py` BOOK_NUMBERS mapping):
PSA = `19-PSA.usfm`, GEN = `01-GEN.usfm`, etc.

## Output Summary

| Content | Local path | Repo | Branch |
|---------|-----------|------|--------|
| ULT (aligned) | `output/AI-ULT/{BOOK}-{CH}-aligned.usfm` | en_ult | `auto-{user}-{BOOK}` |
| UST (aligned) | `output/AI-UST/{BOOK}-{CH}-aligned.usfm` | en_ust | `auto-{user}-{BOOK}` |
| TN | `output/notes/{BOOK}-{CH}.tsv` | en_tn | `{user}-tc-create-1` |
| TQ | `output/tq/{BOOK}-{CHAPTER}.tsv` | en_tq | `auto-{user}-{BOOK}` |
| Issues | `output/issues/{BOOK}-{CH}.tsv` | -- | working file only |
| ULT (unaligned) | `output/AI-ULT/{BOOK}-{CH}.usfm` | -- | not inserted |
| UST (unaligned) | `output/AI-UST/{BOOK}-{CH}.usfm` | -- | not inserted |

## Error Handling

If any phase fails:
1. Stop the pipeline and report which phases completed vs failed
2. All completed outputs remain in `output/` for inspection
3. Repo insertions only happen after all generation phases succeed
4. Any partially-pushed repos can be rolled back with `git checkout -- <file>`

## Unattended Operation

This pipeline runs without user interaction:
- Repo-insert skips dry-run confirmation prompts
- Git diffs are logged but do not require approval
- Each phase validates its outputs before proceeding
