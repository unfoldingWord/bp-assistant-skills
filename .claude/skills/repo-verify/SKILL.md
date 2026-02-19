---
name: repo-verify
description: Verify that a repo-insert push landed on Door43 by comparing local and remote content. Use when asked to verify a push or confirm content is on Door43.
allowed-tools: Bash, Read
---

# Repo Verify

Verify that content from repo-insert actually landed on master on Door43. This
checks that the staging branch was merged, not just that it was pushed.

## When to Use

- After `repo-insert` completes, to confirm the PR was merged to master
- When a user reports that content isn't showing up
- As a sanity check before telling a user their content is ready

## Parameters

| Parameter | Example | Notes |
|-----------|---------|-------|
| Repo | `en_tn`, `en_ult`, `en_ust` | Door43 repo name |
| Book | `PSA` | Book abbreviation |
| Chapter | `122` | Chapter number |
| Content type | `tn`, `ult`, `ust` | What was inserted |
| Staging branch | `AI-PSA-122` | Branch name used by repo-insert |

## Workflow

### Step 1: Check Staging Branch Status

The staging branch should be **gone** after a successful merge (gitea_pr.py
deletes it). If it still exists, the merge likely failed.

```bash
# Load credentials
source <(grep -v '^#' .env | sed 's/^/export /')

REPO="en_tn"
BRANCH="AI-PSA-122"
AUTH_URL="https://${DOOR43_USERNAME}:${DOOR43_TOKEN}@git.door43.org/unfoldingWord/${REPO}.git"

# Check if staging branch still exists on remote
BRANCH_REF=$(git ls-remote --heads "$AUTH_URL" "$BRANCH" 2>/dev/null)
if [ -n "$BRANCH_REF" ]; then
  echo "WARNING: Staging branch '$BRANCH' still exists on remote -- merge may not have happened"
else
  echo "OK: Staging branch '$BRANCH' was deleted (expected after successful merge)"
fi
```

### Step 2: Verify Content on Master

Fetch origin/master and check that the expected content is present.

For TN:
```bash
cd "$DOOR43_REPOS_PATH/$REPO"
git fetch origin master
# Check that master has rows for the chapter
git show origin/master:tn_PSA.tsv | grep -c "^122:"
# Should return a non-zero count
```

For ULT/UST:
```bash
cd "$DOOR43_REPOS_PATH/$REPO"
git fetch origin master
# Check that master has the chapter content
git show origin/master:19-PSA.usfm | grep -c "\\\\c 122"
```

### Step 3: Verify Commit Exists on Master

Check that the AI commit message appears in master's history:

```bash
cd "$DOOR43_REPOS_PATH/$REPO"
git fetch origin master
git log origin/master --oneline -10 | grep -i "PSA 122"
```

If the commit is NOT in master's log but the staging branch still exists,
the merge failed. Report this as an error.

### Step 4: Report

- If staging branch is gone AND content is on master: "Verified: PSA {CH} {content_type} merged to master on {repo}"
- If staging branch still exists: "FAILED: Staging branch {branch} not merged. Run gitea_pr.py --merge to fix."
- If content missing from master: "FAILED: Content not found on master for PSA {CH}"
