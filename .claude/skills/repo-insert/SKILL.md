---
name: repo-insert
description: Insert generated ULT, UST, TN, or TQ content into Door43 repo clones, commit, and create pull requests. Use when asked to push to Door43, insert into repos, or deliver content to the remote.
allowed-tools: Read, Grep, Glob, Bash, Write, Edit
---

# Repo Insert

Insert AI-generated content (ULT, UST, or TN) into local clones of git.door43.org repos, commit on a temporary staging branch, merge to master, and push.

## Organization Rule

All repos belong to the **unfoldingWord** organization on Door43. Never push to a
personal fork. Always verify the remote URL contains `git.door43.org/unfoldingWord/`
before any git operation. Use a temporary AI-named branch for staging, then merge
to master and push.

## Configuration

Uses `.env` in the project root (already in `.gitignore`). On the OCI server, the file lives at `config/.env` instead -- check there as a fallback if the project-root `.env` is missing.

```
DOOR43_TOKEN=<gitea-api-token>
DOOR43_USERNAME=benjamin-test
DOOR43_REPOS_PATH=/path/to/your/door43/repos
```

The token variable may be named `GITEA_TOKEN` rather than `DOOR43_TOKEN` depending on the environment. The scripts accept either name.

- **Git operations** (clone, push, pull): HTTPS with token (`https://${DOOR43_USERNAME}:${DOOR43_TOKEN}@git.door43.org/unfoldingWord/{repo}.git`)

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
1. Content type (ult/ust/tn)
2. Book and chapter (or range)
3. Source file path (check `output/` directories)

Load `.env` for `DOOR43_REPOS_PATH` and `DOOR43_USERNAME`:
```bash
# Source .env values
eval $(grep -v '^#' .env | xargs -d '\n' printf 'export %s\n')
echo "Repos: $DOOR43_REPOS_PATH, User: $DOOR43_USERNAME"
```

### Step 2: Setup Repo

```bash
REPOS_PATH="$DOOR43_REPOS_PATH"
REPO="en_ult"  # en_ult, en_ust, or en_tn
HTTPS_URL="https://${DOOR43_USERNAME}:${DOOR43_TOKEN}@git.door43.org/unfoldingWord/${REPO}.git"

# Clone if needed (use HTTPS with token -- works in sandboxed environments)
if [ ! -d "$REPOS_PATH/$REPO" ]; then
  git clone "$HTTPS_URL" "$REPOS_PATH/$REPO"
fi

cd "$REPOS_PATH/$REPO"
```

**Verify remote points to unfoldingWord.** If the origin URL points to a personal
fork instead of unfoldingWord, fix it before proceeding:

```bash
cd "$REPOS_PATH/$REPO"

# Verify remote -- must be unfoldingWord org, not a personal fork
ORIGIN_URL=$(git remote get-url origin)
if [[ "$ORIGIN_URL" != *"git.door43.org/unfoldingWord/"* ]]; then
  echo "WARNING: Remote points to $ORIGIN_URL -- fixing to unfoldingWord"
  git remote set-url origin "$HTTPS_URL"
fi
```

**Sync local with remote before anything else.** The local branch must exactly
match the remote before inserting. Stale local state causes merge conflicts and
misplaced rows.

```bash
# Check for uncommitted changes -- abort if dirty
if ! git diff --quiet || ! git diff --cached --quiet; then
  echo "ERROR: Repo has uncommitted changes. Resolve before proceeding."
  git status
  # Stop and ask the user how to handle this
fi

# Fetch latest from remote
git fetch origin
```

**Create the staging branch from origin/master.** Always start fresh from
origin/master. Never resume a remote branch.

```bash
BRANCH="AI-PSA-030"  # Derived from book + chapter(s)

# Detach HEAD first so we can safely delete the local branch if it exists
git checkout --detach 2>/dev/null
git branch -D "$BRANCH" 2>/dev/null || true

# Create fresh from origin/master every time
git checkout -b "$BRANCH" origin/master
```

### Step 3: Show Existing Content

Before replacing anything, show the user what currently exists at the target location so they can confirm.

For USFM (ULT/UST):
```bash
# Show current verses in the file
python3 .claude/skills/repo-insert/scripts/insert_usfm_verses.py \
  --book-file "$REPOS_PATH/$REPO/19-PSA.usfm" \
  --source-file output/AI-ULT/PSA/PSA-119-100-104-aligned.usfm \
  --chapter 119 --verses 100-104 --dry-run
```

For TN:
```bash
python3 .claude/skills/repo-insert/scripts/insert_tn_rows.py \
  --book-file "$REPOS_PATH/$REPO/tn_PSA.tsv" \
  --source-file output/notes/PSA/PSA-058.tsv \
  --chapter 58 \
  --dry-run
```

Wait for user confirmation before proceeding.

### Step 4: Execute Insertion

Run with `--backup` to create a safety copy:

For USFM:
```bash
python3 .claude/skills/repo-insert/scripts/insert_usfm_verses.py \
  --book-file "$REPOS_PATH/$REPO/19-PSA.usfm" \
  --source-file output/AI-ULT/PSA/PSA-119-100-104-aligned.usfm \
  --chapter 119 --verses 100-104 --backup
```

For TN:
```bash
python3 .claude/skills/repo-insert/scripts/insert_tn_rows.py \
  --book-file "$REPOS_PATH/$REPO/tn_PSA.tsv" \
  --source-file output/notes/PSA/PSA-058.tsv \
  --chapter 58 \
  --backup
```

### Step 5: Door43 CI Validation (TN only)

For TN inserts, run the Door43 CI validation on the modified book-level TSV
before committing. These are the same checks that run in Door43's CI pipeline
on PR merge -- catching failures here avoids pushing content that will be
rejected.

```bash
python3 .claude/skills/tn-quality-check/scripts/validate_tn_tsv.py \
    "$REPOS_PATH/$REPO/tn_PSA.tsv" \
    --json /tmp/claude/door43_validation.json
```

If this reports errors, fix them before proceeding. If errors cannot be fixed,
roll back with `git checkout -- <file>` and report the failure.

### Step 6: Verify

Show the git diff so the user can review the actual changes:
```bash
cd "$REPOS_PATH/$REPO"
git diff
```

Check:
- Correct verses/rows changed
- Adjacent content untouched
- No stray formatting issues

### Step 7: Commit, Push Branch, Create PR, and Merge

Commit on the staging branch, push it, then create and merge a PR via the API.
Master is a protected branch on Door43 -- direct pushes to master are rejected.
You must use `gitea_pr.py --merge` to land changes on master.

All four operations (commit, push, PR create, PR merge) must complete. The task
is not done until `gitea_pr.py` prints "PR #NNNN merged."

```bash
cd "$REPOS_PATH/$REPO"

# 1. Commit on the staging branch
git add 19-PSA.usfm  # or tn_PSA.tsv
git commit -m "AI ULT for PSA 30 (attribution: benjamin-test)"

# 2. Verify the changes
git diff HEAD~1 --stat

# 3. Push the staging branch
git push origin "$BRANCH"

# 4. Create PR, merge it, and delete the staging branch (all in one call)
python3 .claude/skills/repo-insert/scripts/gitea_pr.py \
  --repo "$REPO" --head "$BRANCH" --base master \
  --title "AI TN for PSA 30 [benjamin-test]" \
  --merge
# Expected output: "PR #NNNN created" then "PR #NNNN merged." then "Branch ... deleted."
# If you do not see "merged" in the output, the insert FAILED -- report the error.
```

If the PR already exists (API 409), the script reuses it and still merges.

If the merge fails or there is a conflict: **stop immediately** and report the
error to the admin. Include the repo name, book, chapter, and error output.

## Scripts Reference

### insert_usfm_verses.py
Surgically replaces a verse range in a book-level USFM file.

```
python3 .claude/skills/repo-insert/scripts/insert_usfm_verses.py \
  --book-file <path-to-book.usfm> \
  --source-file <path-to-source.usfm> \
  --chapter <N> --verses <start-end> \
  [--dry-run] [--backup]
```

- Strips source headers (`\id`, `\usfm`, `\ide`, `\h`, `\toc*`, `\mt`, `\c`), uses only verse content
- Finds verse boundaries by `\v N` markers within the target chapter
- Handles poetry markers on same line as `\v` (e.g., `\q1 \v 100`)
- Handles one-word-per-line aligned USFM format
- Preserves `\ts\*` / `\s5` / `\b` markers outside the replacement range
- Verifies verse marker count is unchanged after insertion
- Preserves original file line endings

### insert_tn_rows.py
Verse-aware chapter replacement for TN rows in a book-level TSV file.

```
python3 .claude/skills/repo-insert/scripts/insert_tn_rows.py \
  --book-file <path-to-tn.tsv> \
  --source-file <path-to-source.tsv> \
  --chapter <chapter-number> \
  [--skip-intro] [--per-reference] \
  [--references 58:2,58:3] \
  [--dry-run] [--backup]
```

- Default mode: detects which verses are in the source file, removes only those verses from the book file, preserves rows for verses not covered by the source
- `--per-reference`: legacy mode that matches rows by exact reference string
- `--skip-intro`: preserve existing intro row even if source has one
- `--references`: filters to specific references (only with `--per-reference`)
- Sort order within each chapter: `:intro` < `:front` < `:1` < `:2` < ... (see Note Ordering below)

### gitea_pr.py
Creates a PR via the Gitea API and optionally merges it. This is the primary
mechanism for landing changes on master (protected branch, no direct push).

```
python3 .claude/skills/repo-insert/scripts/gitea_pr.py \
  --repo <repo-name> --head <source-branch> --base <target-branch> \
  --title "PR title" --merge
```

- `--merge`: creates PR, merges it, and deletes the staging branch
- Reads token from `.env` files first (project root, then config/.env),
  falls back to env vars. Logs which token source is used.
- Prints the PR URL, merge status, and branch deletion on success
- Exits non-zero on failure

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

- Always dry-run first, show the user what will change
- Always show `git diff` after insertion
- Backup files created automatically with `--backup`
- Rollback: `git checkout -- <file>` if something goes wrong
- Never force-push

## Troubleshooting

- **Push rejected (non-fast-forward)**: The remote branch has new commits. Pull with `git pull --rebase` before retrying. If conflicts arise, resolve them manually and re-push.
- **Merge conflict**: The target branch diverged from your working branch. Fetch latest, rebase onto the target, resolve conflicts, and force-push your feature branch (never force-push master/main).
- **Authentication error (403)**: The Door43 token may be expired or missing. Check `.env` for `DOOR43_TOKEN` and verify it has push access to the target organization.
- **Wrong remote (personal fork)**: Verify `git remote -v` shows the unfoldingWord org URL, not a personal fork. Use `git remote set-url origin <correct-url>` to fix.

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
