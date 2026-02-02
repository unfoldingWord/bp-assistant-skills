Check your environment. You are probably in windows. You may be in WSL.
Don't use emojis, it breaks windows terminal.

## Primary Tasks
You are either being asked to:
1) Assist with creation of unfoldingWord Book Package items including the unfoldingWord Literal Text, unfoldingword Simplified Text, translation notes, or possibly translation questions. You will have skills for each of these, the top level skills may lead you to other skills.
2) Develop or improve the skills markdown files for task 1.

- Take a light hand to skill edits. Avoid all caps, or 'critical' type language. If an issue is underrepresented we want to nudge not shove.

## Project Structure

### Skills (in `.claude/skills/`)
- `pipeline-overview/` - Orchestration and workflow guidance
- `ULT-gen/` - ULT creation (placeholder)
- `simplified-transform/` - UST creation (placeholder)
- `issue-identification/` - Identifying translation issues (figs-metaphor, figs-idiom, etc.)
- `note-writing/` - Writing translation notes (placeholder)
- `hebrew-reference/` - Hebrew language reference (placeholder)
- `create-issue-description/` - Create new issue identification skills

### Data (in `data/`)
- `translation-issues.csv` - List of all translation issues; `last_updated` column tracks skill completion
- `issues_resolved.txt` - Cached Issues Resolved document (auto-fetched daily)
- `templates.csv` - Cached TN Templates (auto-fetched daily)

### External Resources
- `data/ta-flat/` - Translation Academy articles (source definitions)
- `data/published-tns/` - Human-identified examples in TSV format

### Tracking
- When completing a skill, update `data/translation-issues.csv` with today's date (YYYY-MM-DD)
- "Next issue" or "go to next one" means find first issue without a date and create that skill

### Authoritative Sources (in order of authority)
1. **Issues Resolved** (FINAL AUTHORITY) - Content team decisions
   - Fetch: `python .claude/skills/issue-identification/scripts/fetch_issues_resolved.py` (cached daily in `data/issues_resolved.txt`)
   - If Issues Resolved contradicts other sources, Issues Resolved wins
2. **Processed Translation Notes** - Human-identified examples
3. **TN Templates** - Official note templates
   - Fetch: `python .claude/skills/utilities/scripts/fetch_templates.py` (cached daily in `data/templates.csv`)
4. **Translation Academy** - Definitions and explanations

### Creating Skills
See `.claude/skills/create-issue-description/create-issue-description.md` for the full process. Key requirements:
- Examine 200+ examples from processed notes (if available)
- Check Issues Resolved for authoritative decisions
- Document what IS and what IS NOT this issue type
- Update tracking CSV when complete
