---
name: repo-insert
description: Insert generated ULT, UST, or TN content into Door43 repo clones, commit, and optionally create PRs.
allowed-tools: Read, Grep, Glob, Bash, Write, Edit
---

# Repo Insert

Insert AI-generated content (ULT, UST, or TN) into local clones of git.door43.org repos, commit, push, and optionally create pull requests.

## Configuration

Uses `.env` in the project root (already in `.gitignore`):

```
DOOR43_TOKEN=<gitea-api-token>       # Only needed for PR creation
DOOR43_USERNAME=deferredreward
DOOR43_REPOS_PATH=/mnt/c/Users/benja/Documents/GitHub
```

- **Git operations** (clone, push, pull): SSH URLs (`git@git.door43.org:unfoldingWord/{repo}.git`) -- SSH keys already configured
- **PR creation**: Needs a Gitea API token (see `reference/gitea-api.md`)

## Parameters

| Parameter | Example | Notes |
|-----------|---------|-------|
| Content type | `ult`, `ust`, `tn` | User specifies |
| Book | `PSA` | Standard abbreviation |
| Verse range | `119:100-104` | Chapter:start-end |
| Username | `deferredreward` | From user or `.env` |
| Source file | `output/AI-ULT/PSA-119-100-104-aligned.usfm` | Locate in `output/` |
| Create PR? | yes/no | User specifies |
| PR base branch | working branch or master | User chooses when PR requested |

### Derived Values

- **Repo**: `en_ult` / `en_ust` / `en_tn` (from content type)
- **Working branch**: ULT/UST = `auto-{username}-{BOOK}`, TN = `{username}-tc-create-1`
- **Filename in repo**: `{BOOK_NUMBER}-{BOOK}.usfm` for ULT/UST, `tn_{BOOK}.tsv` for TN
  - Book numbers from `fetch_door43.py` BOOK_NUMBERS mapping (e.g., PSA -> `19-PSA.usfm`)
- **PR branch** (when basing on master): Auto-derived like `psa-119-100-104`, or user-specified

## Workflow

### Step 1: Gather Parameters

Determine from the user or context:
1. Content type (ult/ust/tn)
2. Book and verse range
3. Source file path (check `output/` directories)
4. Whether to create a PR

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

**Sync local with remote before anything else.** The local branch must exactly match the remote before inserting. Stale local state causes merge conflicts and misplaced rows. Do not merge master into the working branch -- the goal is an exact replica of the remote branch state.

```bash
cd "$REPOS_PATH/$REPO"

# Check for uncommitted changes -- abort if dirty
if ! git diff --quiet || ! git diff --cached --quiet; then
  echo "ERROR: Repo has uncommitted changes. Resolve before proceeding."
  git status
  # Stop and ask the user how to handle this
fi

# Fetch the working branch from remote
git fetch "$HTTPS_URL" "$BRANCH" || true  # may not exist yet
```

Checkout the working branch, ensuring it matches remote exactly:
```bash
BRANCH="auto-deferredreward-PSA"  # or {username}-tc-create-1 for TN

# Fetch and create/reset local branch to match remote exactly
if git fetch "$HTTPS_URL" "$BRANCH" 2>/dev/null; then
  git fetch "$HTTPS_URL" "$BRANCH:$BRANCH" 2>/dev/null || true
  git checkout "$BRANCH"
  git reset --hard FETCH_HEAD
else
  # Branch doesn't exist on remote -- fetch master and create from it
  git fetch "$HTTPS_URL" master
  git checkout -b "$BRANCH" FETCH_HEAD
fi
```

### Step 3: Show Existing Content

Before replacing anything, show the user what currently exists at the target location so they can confirm.

For USFM (ULT/UST):
```bash
# Show current verses in the file
python3 .claude/skills/repo-insert/scripts/insert_usfm_verses.py \
  --book-file "$REPOS_PATH/$REPO/19-PSA.usfm" \
  --source-file output/AI-ULT/PSA-119-100-104-aligned.usfm \
  --chapter 119 --verses 100-104 --dry-run
```

For TN:
```bash
python3 .claude/skills/repo-insert/scripts/insert_tn_rows.py \
  --book-file "$REPOS_PATH/$REPO/tn_PSA.tsv" \
  --source-file output/notes/PSA-058.tsv \
  --dry-run
```

Wait for user confirmation before proceeding.

### Step 4: Execute Insertion

Run with `--backup` to create a safety copy:

For USFM:
```bash
python3 .claude/skills/repo-insert/scripts/insert_usfm_verses.py \
  --book-file "$REPOS_PATH/$REPO/19-PSA.usfm" \
  --source-file output/AI-ULT/PSA-119-100-104-aligned.usfm \
  --chapter 119 --verses 100-104 --backup
```

For TN:
```bash
python3 .claude/skills/repo-insert/scripts/insert_tn_rows.py \
  --book-file "$REPOS_PATH/$REPO/tn_PSA.tsv" \
  --source-file output/notes/PSA-058.tsv \
  --backup
```

### Step 5: Verify

Show the git diff so the user can review the actual changes:
```bash
cd "$REPOS_PATH/$REPO"
git diff
```

Check:
- Correct verses/rows changed
- Adjacent content untouched
- No stray formatting issues

### Step 6: Commit and Push

```bash
cd "$REPOS_PATH/$REPO"
git add 19-PSA.usfm  # or tn_PSA.tsv
git commit -m "Insert AI ULT for PSA 119:100-104"
git push "$HTTPS_URL" "$BRANCH"
```

### Step 7: Optional PR Creation

If the user wants a PR:

**If basing on the working branch** (the common case): the content was already pushed to the working branch in step 6. The user works on that branch directly -- no PR needed for this case unless they want to merge the working branch into master.

**If basing on master** (or any other branch): create a named branch from the current position and PR it:

```bash
PR_BRANCH="psa-119-100-104"  # auto-derived or user-specified
git checkout -b "$PR_BRANCH"
git push origin "$PR_BRANCH"

python3 .claude/skills/repo-insert/scripts/gitea_pr.py \
  --repo "$REPO" \
  --head "$PR_BRANCH" \
  --base master \
  --title "PSA 119:100-104 AI ULT"
```

The script prints the PR URL on success.

If the user doesn't have a `DOOR43_TOKEN`, direct them to create one at `https://git.door43.org/user/settings/applications` and add it to `.env`.

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
Surgically replaces TN rows by reference in a book-level TSV file.

```
python3 .claude/skills/repo-insert/scripts/insert_tn_rows.py \
  --book-file <path-to-tn.tsv> \
  --source-file <path-to-source.tsv> \
  [--references 58:2,58:3] \
  [--dry-run] [--backup]
```

- Matches rows by exact reference string (column 0)
- Replaces existing rows or inserts at correct sort position
- Sort order within each chapter: `:intro` < `:front` < `:1` < `:2` < ... (see Note Ordering below)
- `--references` filters to specific references from the source file

### gitea_pr.py
Creates a pull request via the Gitea API.

```
python3 .claude/skills/repo-insert/scripts/gitea_pr.py \
  --repo <repo-name> --head <source-branch> --base <target-branch> \
  --title "PR title"
```

- Reads `DOOR43_TOKEN` from `.env` or environment
- Prints the PR URL on success

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
