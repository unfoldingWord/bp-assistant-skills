# Postmortem: Lost Files Recovery - February 5, 2026

## Summary

Multiple skill files and scripts were lost from the cSkillBP repository. Files were created during Claude Code sessions but were never committed to git. They were recovered from Claude Code session history stored in `~/.claude/projects/`.

## What Was Lost

### Complete Skills (entire directories missing)
- `.claude/skills/ULT-alignment/` - Word-level alignment between Hebrew and English
- `.claude/skills/UST-gen/` - Simplified Text generation skill

### Individual Files
- `.claude/skills/ULT-alignment/reference/alignment_rules.md`
- `.claude/skills/UST-gen/reference/ust_patterns.md`
- `.claude/skills/issue-identification/scripts/compare_ult_ust.py`
- `.claude/skills/utilities/scripts/fetch_all_ust.py`
- `.claude/skills/utilities/scripts/fetch_t4t.py`
- `.claude/skills/utilities/scripts/filter_psalms.py`
- `.claude/skills/utilities/scripts/usfm/create_aligned_usfm.js`

## Root Cause

### The Trigger: Branch Reset

From the git reflog:
```
2075ad5 refs/heads/main@{2}: branch: Reset to issue-id-subagent-conversion
```

The `main` branch was reset to match `issue-id-subagent-conversion`. This itself shouldn't cause file loss if everything was committed.

### The Actual Problem: Uncommitted Work

The files were created in Claude Code sessions but **never committed to git**. This created a dangerous situation:

1. Files existed on disk (working directory)
2. Files were NOT in any git commit
3. Git operations (reset, checkout, etc.) do not protect untracked files
4. At some point, the working directory was cleaned or overwritten

### Why Files Weren't Committed

Looking at the session history, files were written during sessions but:
- No explicit commit was requested
- The session ended without committing
- Work continued in new sessions, assuming files existed
- Nobody noticed they weren't in git until much later

## Timeline Reconstruction

| Date | Event |
|------|-------|
| Feb 2 | Initial commit with basic skills |
| Feb 3 | ULT-alignment skill created in session (not committed) |
| Feb 3 | UST-gen skill created in session (not committed) |
| Feb 3 | Various utility scripts written (not committed) |
| Feb 4 | create_aligned_usfm.js written (not committed) |
| Feb 5 | Branch reset executed |
| Feb 5 | Discovery: files missing, .gitignore corrupted |

## Recovery Method

Claude Code stores full session transcripts in `~/.claude/projects/<project-path>/`:
- Each session is a `.jsonl` file containing all tool calls
- Write tool calls include the full file content
- By parsing these files, we recovered the original content

```bash
# Search for files that were written
grep -l "file_path.*alignment" ~/.claude/projects/*/*.jsonl
```

## Prevention Strategies

### 1. Commit Early, Commit Often

**Rule**: If Claude writes a file you want to keep, commit it immediately.

```bash
# After any significant file creation
git add <new-file>
git commit -m "Add <description>"
```

**Why it matters**: Git only protects committed files. Untracked files can be lost at any time.

### 2. Check Git Status Before Ending Sessions

**Habit**: Before ending any session, run:
```bash
git status
```

Look for untracked files (red, not staged). If you see new files that should be kept, commit them.

### 3. Use .gitignore Carefully

Your `.gitignore` was missing entries that caused data folders to be untracked. Keep `.gitignore` version controlled and review changes to it.

**Dangerous pattern**: Adding broad ignores like `data/` without realizing it hides important files.

### 4. Periodic "What's Not Tracked?" Audits

Run periodically:
```bash
git status --porcelain | grep "^??"
```

This shows all untracked files. Review them - should any be committed?

### 5. Consider a Pre-Session Hook

Claude Code supports hooks. Consider a `SessionEnd` hook that warns about untracked files:

```json
{
  "hooks": {
    "SessionEnd": [{
      "type": "command",
      "command": "git status --porcelain | grep '^??' && echo 'WARNING: Untracked files exist!'"
    }]
  }
}
```

### 6. Backup Session Transcripts

The session transcripts in `~/.claude/` saved this situation. Consider:
- Not excluding `~/.claude/projects/` from backups
- Periodic manual backup of session history
- Knowing this recovery method exists

## Git Safety Principles

### What Git Protects
- Committed files (in any branch)
- Staged files (added but not committed)
- Stashed changes

### What Git Does NOT Protect
- Untracked files (never added)
- Ignored files (matched by .gitignore)
- Working directory changes that aren't staged

### Dangerous Git Operations (for uncommitted work)
- `git reset --hard` - Discards all uncommitted changes
- `git checkout .` - Reverts working directory
- `git clean -f` - Deletes untracked files
- `git stash` then forgetting to `git stash pop`
- Branch switching when files would be overwritten

## Quick Reference: Safe Workflow

```
1. Claude creates files
     |
     v
2. Review what was created
   $ git status
     |
     v
3. Stage important files
   $ git add <files>
     |
     v
4. Commit with message
   $ git commit -m "description"
     |
     v
5. THEN do branch operations
   (checkout, reset, merge, etc.)
```

## Lessons Learned

1. **Session work != Saved work** - Files created in a session are not automatically permanent
2. **Git is not a backup** - Git only protects what's committed
3. **Session history is valuable** - Claude Code's session storage can recover lost work
4. **Branch operations are risky** - Always ensure clean git status before branch operations
5. **Verify before assuming** - Don't assume files exist; verify with `ls` or `git status`

## Files Recovered in This Incident

All files were successfully recovered from session history:
- 2 complete skills (ULT-alignment, UST-gen)
- 7 individual files (scripts and reference docs)
- ~50KB of content total

## Future Improvements

Consider adding to CLAUDE.md:
```markdown
## Git Discipline
- Commit any new files immediately after creation
- Run `git status` before ending sessions
- Never do branch operations with untracked files you want to keep
```
