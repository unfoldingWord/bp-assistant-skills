---
name: repo-verify
description: Verify that a repo-insert push actually landed on the Door43 remote. Checks branch existence and file content via git ls-remote and shallow clone.
allowed-tools: Bash, Read
---

# Repo Verify

Verify that a push to a Door43 repository branch actually succeeded. Use this after repo-insert when you need to confirm content landed on the remote.

## When to Use

- After `repo-insert` completes and you want to confirm the push worked
- When a user reports that content isn't showing up on their branch
- As a sanity check before telling a user their content is ready

## Parameters

| Parameter | Example | Notes |
|-----------|---------|-------|
| Repo | `en_tn`, `en_ult`, `en_ust` | Door43 repo name |
| Branch | `auto-deferredreward-PSA` | Branch to check |
| File path | `19-PSA.usfm` | File within the repo to verify (optional) |

## Workflow

### Step 1: Check Branch Exists

```bash
# Load credentials
source <(grep -v '^#' .env | sed 's/^/export /')

REPO="en_ult"
BRANCH="auto-deferredreward-PSA"
AUTH_URL="https://${DOOR43_USERNAME}:${DOOR43_TOKEN}@git.door43.org/unfoldingWord/${REPO}.git"

# Verify branch exists on remote
git ls-remote --heads "$AUTH_URL" "$BRANCH"
```

If no output, the branch doesn't exist — the push failed.

### Step 2: Verify File Content (Optional)

If you need to verify specific file content:

```bash
# Shallow clone the branch
TMPDIR=$(mktemp -d /tmp/claude/repo-verify-XXXXXX)
git clone --depth 1 --branch "$BRANCH" "$AUTH_URL" "$TMPDIR"

# Check the file exists and compare
ls -la "$TMPDIR/19-PSA.usfm"

# Compare against local source
diff "$TMPDIR/19-PSA.usfm" output/AI-ULT/PSA/PSA-119-aligned.usfm

# Cleanup
rm -rf "$TMPDIR"
```

### Step 3: Report

- If branch exists and files match: "Verified: content is on `{branch}` in {repo}"
- If branch missing: "Push failed: branch `{branch}` not found on {repo}"
- If files differ: "Content mismatch on `{branch}` — the push may have partially failed"
