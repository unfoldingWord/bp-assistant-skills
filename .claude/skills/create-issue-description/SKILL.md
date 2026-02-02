---
name: create-issue-description
description: Creates or updates a translation issue description file and the issue-identification SKILL.
allowed-tools: Read, Grep, Glob, Bash
---

# Utilities

## Purpose
Supporting tools and skills for resource fetching, skill creation, and other utility functions.

## Available Utilities

| Utility | Description |
|---------|-------------|
| [create-issue-description.md](create-issue-description.md) | Create a new translation issue identification skill |
| [fetch-templates.md](fetch-templates.md) | Fetch TN Templates spreadsheet |

## Scripts

Located in `scripts\`:

| Script | Purpose | Usage |
|--------|---------|-------|
| `fetch_templates.py` | Fetch TN Templates from Google Sheets | `python .claude\skills\utilities\scripts\fetch_templates.py` |

## Related Scripts

The Issues Resolved fetch script is located with the issue-identification skill:
- `.claude\skills\issue-identification\scripts\fetch_issues_resolved.py`

## Common Commands

### Refresh all cached resources
```bash
python .claude\skills\issue-identification\scripts\fetch_issues_resolved.py --force
python .claude\skills\utilities\scripts\fetch_templates.py --force
```

### Check cached resource dates
The first line of each cached file shows the fetch date:
- `data\issues_resolved.txt`
- `data\templates.csv`

## Creating New Skills

To create a new issue identification skill:

1. Run `create-issue-description.md` workflow
2. Skill will be created at `.claude\skills\issue-identification\[issue-name].md`
3. Update `data\translation-issues.csv` with completion date
