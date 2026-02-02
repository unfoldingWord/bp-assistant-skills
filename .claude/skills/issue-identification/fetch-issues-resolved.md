# Skill: Fetch Issues Resolved

## Purpose
Fetch the "Issues Resolved" Google Doc containing authoritative decisions about translation notes, figures of speech classifications, and content guidelines.

## When to Use
- When you need to verify how a specific figure of speech should be classified (metaphor vs idiom vs metonymy, etc.)
- When checking decisions about specific Hebrew/Greek terms or expressions
- When verifying content team decisions about translation note formatting or approaches
- The Issues Resolved document is the **final authority** on any disputed decision

## Usage

### Fetch with daily caching (recommended):
```bash
python .claude\skills\issue-identification\scripts\fetch_issues_resolved.py
```

### Force re-fetch even if cached today:
```bash
python .claude\skills\issue-identification\scripts\fetch_issues_resolved.py --force
```

### Fetch with custom output path:
```bash
python .claude\skills\issue-identification\scripts\fetch_issues_resolved.py -o output_file.txt
```

### Default document ID:
`1C0C7Qsm78fM0tuLyVZEAs-IWtClNo9nqbsAZkAFeFio`

## Output
Plain text export of the Google Doc saved to `data\issues_resolved.txt`. Most recent decisions are at the top, organized by date.

## Key Content Areas
The document contains decisions about:
- Figure of speech classifications (figs-metaphor, figs-idiom, figs-metonymy, etc.)
- Hebrew/Greek term translations
- ULT/UST conventions
- Note formatting standards
- Template usage guidelines

## Example Workflow
1. Run the fetch script to get latest decisions
2. Search the output for the relevant term or figure type
3. Apply the documented decision to your work
