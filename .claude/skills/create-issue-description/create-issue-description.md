# Skill: Create Translation Issue Skill

## Purpose
Create a comprehensive identification skill for a translation issue (figs-metaphor, figs-idiom, etc.) by systematically gathering information from all authoritative sources.

## When to Use
- User says "create skill for [issue]" or "next issue"
- User wants to document how to identify a specific translation issue type

## Skill Naming Convention

**IMPORTANT**: Skills must be named using the exact hyphenated label from `data\translation-issues.csv`:
```
.claude\skills\issue-identification\[exact-issue-label].md
```

Examples:
- `figs-metaphor` -> `.claude\skills\issue-identification\figs-metaphor.md`
- `figs-123person` -> `.claude\skills\issue-identification\figs-123person.md`
- `grammar-connect-logic-result` -> `.claude\skills\issue-identification\grammar-connect-logic-result.md`

## Process Overview

### Step 1: Identify the Issue
Check `data\translation-issues.csv` for the target issue. If user says "next", find the first issue without a `last_updated` date.
If asked to do multiple issues at once, work through the whole process individually for each requested while keeping the others in mind as potentially related and make distinctions between them if needed.

### Step 2: Gather Source Materials

#### 2a. Translation Academy Article
Find and read the TA article for this issue:

Location: `data\ta-flat\[issue-name].md`
Example: `data\ta-flat\figs-metaphor.md`
Extract:
- Definition
- Description of the figure/issue
- Examples from the Bible
- Translation strategies

#### 2b. Human-Identified Examples (COMPREHENSIVE REVIEW)
Search the published translation notes for real examples from multiple genres (OT narrative, poetry, prophets, gospels, epistles). Find examples in EACH genre and each Testament if possible:

Location: `data/published-tns/`

**IMPORTANT: TSV lines are very long. Use this multi-step approach to avoid token limits:**

**Step 1: Get counts by file** (understand distribution)
```
Grep tool with:
  pattern: "[0-9]:[0-9].*translate/[issue-name]"
  path: "data/published-tns"
  output_mode: "count"
```

**Step 2: Sample from files that have examples** (10-20 examples per file)
```
Grep tool with:
  pattern: "[0-9]:[0-9].*translate/[issue-name]"
  path: "data/published-tns/tn_[BOOK].tsv"
  output_mode: "content"
  head_limit: 15
```

Note: The pattern combines two filters:
- `[0-9]:[0-9]` requires a verse reference in column 1 (excludes `:intro` rows)
- `translate/[issue-name]` matches the SupportReference column format
Intro rows are huge and often mention issue types in their text - this pattern excludes them.

Use the counts from Step 1 to pick files. Aim for genre diversity:
- Pick 2-3 OT books and 2-3 NT books from those with examples
- Prioritize files with more examples (better sample)
- Try to cover different genres (narrative, poetry, prophecy, gospels, epistles) based on what's available

**Analyze examples for:**
- Common patterns and phrasings
- Categories/subtypes of the issue
- How annotators distinguish from similar issues
- Specific vocabulary that triggers this issue

#### 2c. Issues Resolved (AUTHORITATIVE DECISIONS)
The Issues Resolved document is cached daily in `data\issues_resolved.txt`. The script checks the first line for a date stamp and only re-fetches if it's a new day.

```bash
python .claude\skills\issue-identification\scripts\fetch_issues_resolved.py
```

This will:
- Return cached content if already fetched today (from `data\issues_resolved.txt`)
- Fetch fresh content and save if not fetched today
- Use `--force` flag to override daily cache: `python .claude\skills\issue-identification\scripts\fetch_issues_resolved.py --force`

Search the content for:
- Explicit decisions about this issue type
- Distinctions from similar issue types
- Edge cases and how they were resolved
- Any updates or corrections to previous decisions

**Issues Resolved is the final authority** - if it contradicts other sources, Issues Resolved wins.

#### 2d. TN Templates
The templates spreadsheet is cached daily in `data\templates.csv`:
```bash
python .claude\skills\utilities\scripts\fetch_templates.py
```

Use `--force` to re-fetch: `python .claude\skills\utilities\scripts\fetch_templates.py --force`

Search for all template variants for this issue:
- Generic template
- Specialized subtypes
- Related templates that might overlap

### Step 3: Synthesize and Write Skill

Create skill file at: `.claude\skills\issue-identification\[exact-issue-label].md`

The filename MUST match the issue label exactly as it appears in `data\translation-issues.csv`.

Structure:
1. **Purpose** - What this skill helps identify
2. **Definition** - From TA article
3. **Confirmed Classifications** - From Issues Resolved
4. **NOT This Issue** - What to use instead (with reasons)
5. **Categories/Subtypes** - From examples analysis
6. **Recognition Process** - Decision tree for identification
7. **Template Types Available** - From templates spreadsheet
8. **Authoritative Sources** - Links to tools

IMPORTANT: Before writing, review and trim the fat. These will be loaded into context so minimize token use and don't repeat things unneccesarily.
Do not mention or reference the note templates in the output.

Update sections Available Issue Types and Recognition Flow in `.claude\skills\issue-identification\SKILL.md` with new skill one-liners.

### Step 4: Update Tracking
Update `data\translation-issues.csv` with today's date:
```
[issue-name],YYYY-MM-DD
```

## "Next Issue" Command

When user says "next" or "go to next one":
1. Read translation-issues.csv
2. Find first row where last_updated is empty
3. Start the process for that issue
4. Report which issue you're working on

## Quality Checklist

Before completing a skill, verify:
- [ ] TA article reviewed
- [ ] 200+ examples examined from published notes (or all available if fewer)
- [ ] Multiple genres represented in examples
- [ ] Issues Resolved searched for decisions (uses daily cache)
- [ ] Distinctions from similar issues documented
- [ ] Templates identified
- [ ] Skill filename matches issue label exactly
- [ ] CSV updated with date

## Example Commands

```
"Create skill for figs-idiom"
"Next issue"
"Go to the next one"
"Create skill for figs-metonymy"
```
