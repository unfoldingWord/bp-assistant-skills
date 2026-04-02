---
name: repo-insert
description: Insert generated ULT, UST, TN, or TQ content into Door43 repo clones, commit, and create pull requests. Use when asked to push to Door43, insert into repos, or deliver content to the remote.
allowed-tools: Read, Grep, Glob, Bash, Write, Edit
---

# Repo Insert

Insert AI-generated content (ULT, UST, or TN) into local clones of git.door43.org repos, commit on a temporary staging branch, and merge to master via PR.

All mechanical work (clone, insert, validate, commit, push, PR create, PR merge) is handled by `door43-push-cli.js`, a CLI wrapper around `door43Push()`. This skill adds intelligence on top: parameter gathering, dry-run preview, and error recovery.

## Organization Rule

All repos belong to the **unfoldingWord** organization on Door43. Never push to a
personal fork. The CLI enforces this by verifying the remote URL.

## Configuration

Uses `.env` in the project root (already in `.gitignore`). On the OCI server, the file lives at `config/.env` instead -- check there as a fallback if the project-root `.env` is missing.

```
DOOR43_TOKEN=<gitea-api-token>
DOOR43_USERNAME=benjamin-test
DOOR43_REPOS_PATH=/path/to/your/door43/repos
```

The token variable may be named `GITEA_TOKEN` rather than `DOOR43_TOKEN` depending on the environment. The scripts accept either name.

## Parameters

| Parameter | Example | Notes |
|-----------|---------|-------|
| Content type | `ult`, `ust`, `tn` | User specifies |
| Book | `PSA` | Standard abbreviation |
| Chapter | `30` or `33-34` | Single chapter or range |
| Verse range | `119:100-104` | Chapter:start-end |
| Username | `benjamin-test` | For commit message attribution |
| Source file | `output/AI-ULT/PSA/PSA-119-100-104-aligned.usfm` | Locate in `output/` |

### Derived Values

- **Repo**: `en_ult` / `en_ust` / `en_tn` (from content type)
- **Staging branch**: `AI-{BOOK}-{CH}` for single chapter (e.g. `AI-PSA-030`, `AI-ISA-33`), `AI-{BOOK}-{CH1}-{CH2}` for range (e.g. `AI-PSA-030-031`). PSA uses 3-digit padding, all other books use 2-digit.
- **Filename in repo**: `{BOOK_NUMBER}-{BOOK}.usfm` for ULT/UST, `tn_{BOOK}.tsv` for TN
  - Book numbers from `fetch_door43.py` BOOK_NUMBERS mapping (e.g., PSA -> `19-PSA.usfm`)

## Workflow

### Step 1: Gather Parameters

Determine from the user or context:
1. Content type (ult/ust/tn/tq)
2. Book and chapter (or range)
3. Source file path (check `output/` directories)
4. Door43 username (for user branch derivation and commit attribution)

Load `.env` for `DOOR43_USERNAME`:
```bash
eval $(grep -v '^#' .env | xargs -d '\n' printf 'export %s\n')
echo "User: $DOOR43_USERNAME"
```

Derive staging branch name:
```bash
# PSA uses 3-digit padding, other books use 2-digit
BRANCH="AI-PSA-030"  # or AI-ISA-33
```

### Step 2: Dry-Run Preview (interactive use only)

For interactive (non-pipeline) use, show the user what will change before pushing. Pass `--dry-run` to the `door43-push-cli.js` command (Step 3) to preview without committing. The CLI will print the diff but not push.

Wait for user confirmation before proceeding. Skip this step in unattended/pipeline mode.

### Step 3: Run door43-push-cli.js

Execute the CLI wrapper which handles clone/fetch, insertion, validation (TN), commit, push, PR create, and PR merge:

```bash
node /app/src/door43-push-cli.js \
  --type tn \
  --book PSA \
  --chapter 30 \
  --username "$DOOR43_USERNAME" \
  --branch AI-PSA-030 \
  --source output/notes/PSA/PSA-030.tsv
```

For ULT/UST, add `--verses` if not the full chapter:
```bash
node /app/src/door43-push-cli.js \
  --type ult \
  --book PSA \
  --chapter 30 \
  --username "$DOOR43_USERNAME" \
  --branch AI-PSA-030 \
  --source output/AI-ULT/PSA/PSA-030-aligned.usfm \
  --verses 1-22
```

**Path note**: Inside the Docker container, use `/app/src/door43-push-cli.js`. On the host (ad-hoc Claude sessions), use `/srv/bot/app/src/door43-push-cli.js`.

The CLI outputs JSON to stdout:
```json
{"success": true, "details": "PR #123 merged AI-PSA-030 into master on en_tn", "prNumber": 123, "duration": "4.2"}
```

Exit codes: 0 = success, 1 = push failed (details in JSON), 2 = bad args.

### Step 4: Handle Result

**Success**: Report the PR number and target branch to the user.

**Validation failure** (details contain "Door43 CI validation failed"):
1. Read the error details (line numbers, rule names, messages)
2. Fix the source file (e.g., bracket pairing, AT label format)
3. Re-run the CLI with the fixed source

**No changes detected**: Not an error -- content already matches the target branch. Report and move on.

**Git/push/API errors** (auth, conflict, timeout): Report to user -- these need human intervention.

## Scripts Reference

### door43-push-cli.js
CLI wrapper around `door43Push()`. Handles clone, insert, validate, commit, push, PR create/merge in one command.

```
node /app/src/door43-push-cli.js \
  --type <tn|ult|ust> --book <BOOK> --chapter <N> \
  --username <name> --branch <branch> --source <path> \
  [--verses <range>]
```

- Outputs JSON to stdout, logs to stderr
- Exit 0 = success, 1 = failure, 2 = bad args
- Internally calls `door43Push()` from `door43-push.js`

### insert_usfm_verses (internal)
Used internally by `door43-push-cli.js`. Surgically replaces a verse range in a book-level USFM file.

- Strips source headers (`\id`, `\usfm`, `\ide`, `\h`, `\toc*`, `\mt`, `\c`), uses only verse content
- Finds verse boundaries by `\v N` markers within the target chapter
- Handles poetry markers on same line as `\v` (e.g., `\q1 \v 100`)
- Handles one-word-per-line aligned USFM format
- Preserves `\ts\*` / `\s5` / `\b` markers outside the replacement range
- Verifies verse marker count is unchanged after insertion
- Preserves original file line endings

### insert_tn_rows (internal)
Used internally by `door43-push-cli.js`. Verse-aware chapter replacement for TN rows in a book-level TSV file.

- Default mode: detects which verses are in the source file, removes only those verses from the book file, preserves rows for verses not covered by the source
- `--per-reference`: legacy mode that matches rows by exact reference string
- `--skip-intro`: preserve existing intro row even if source has one
- `--references`: filters to specific references (only with `--per-reference`)
- Sort order within each chapter: `:intro` < `:front` < `:1` < `:2` < ... (see Note Ordering below)

### gitea_pr (manual fallback)
Use `mcp__workspace-tools__gitea_pr` with `repo`, `head`, `base`, `title`, and `merge=true`. Used only when the CLI is unavailable.

## Note Ordering (TN)

For any given chapter, notes follow this reference order:

```
<chapter>:intro    (chapter introduction -- may be auto-generated in the future)
<chapter>:front    (superscription / pre-verse-1 content)
<chapter>:1
<chapter>:2
...
```

Within each verse, notes are ordered by position in the ULT (first to last),
with longer phrases before shorter nested phrases. The `insert_tn_rows.py`
script and `assemble_notes.py` both enforce this ordering.

## Safety

- Always dry-run first in interactive mode (show the user what will change)
- Backup files created automatically by the CLI (`--backup` passed to insertion scripts)
- Rollback: `git checkout -- <file>` in the repo directory if something goes wrong
- Never force-push

## Troubleshooting

- **Push rejected (non-fast-forward)**: The remote branch has new commits. The CLI handles fetch/reset but if this persists, check for concurrent pushes.
- **Authentication error (403)**: The Door43 token may be expired or missing. Check `.env` for `DOOR43_TOKEN` and verify it has push access to the target organization.
- **Validation failure**: Read the error details from the CLI JSON output, fix the source file, and retry.
- **CLI not found**: Inside Docker use `/app/src/door43-push-cli.js`, on the host use `/srv/bot/app/src/door43-push-cli.js`.

## Manual Fallback

If the CLI is unavailable, the full manual git procedure is documented in the git
history of this file. The key steps are: clone/fetch, create staging branch from
master, run insertion script, validate (TN), commit, push, create PR via
`gitea_pr.py --merge`, verify merge.

## Book Number Reference

Used for mapping book abbreviations to filenames (from `fetch_door43.py`):

| Book | Number | Filename |
|------|--------|----------|
| GEN | 01 | 01-GEN.usfm |
| PSA | 19 | 19-PSA.usfm |
| MAT | 41 | 41-MAT.usfm |
| REV | 67 | 67-REV.usfm |

For TN files: `tn_{BOOK}.tsv` (e.g., `tn_PSA.tsv`)

Full mapping available in `.claude/skills/utilities/scripts/fetch_door43.py`.
