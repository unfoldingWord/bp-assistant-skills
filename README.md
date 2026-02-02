# Pure Skills BP Assistant

AI-assisted creation of unfoldingWord Book Package (BP) items including translation notes, ULT, and UST.

## Purpose

This project provides Claude Code skills for:
- Creating unfoldingWord Literal Text (ULT)
- Creating unfoldingWord Simplified Text (UST)
- Identifying translation issues in biblical text
- Generating translation notes

## Pipeline Stages

The book package creation process follows four stages:

| Stage | Description | Skill Location | Status |
|-------|-------------|----------------|--------|
| 1. Literal Transform | Create ULT from source | `.claude/skills/ULT-gen/` | Placeholder |
| 2. Simplified Transform | Create UST from source | `.claude/skills/simplified-transform/` | Placeholder |
| 3. Issue Identification | Find what needs notes | `.claude/skills/issue-identification/` | Active |
| 4. Note Writing | Generate translation notes | `.claude/skills/note-writing/` | Placeholder |

## Using the Skills

Start with the pipeline overview:
```
.claude/skills/pipeline-overview/SKILL.md
```

For issue identification, each issue type has its own skill file:
- `figs-metaphor.md` - Metaphors
- `figs-idiom.md` - Idioms
- `figs-123person.md` - Person shifts
- `figs-explicit.md` - Making implicit explicit
- `figs-explicitinfo.md` - Making explicit implicit
- `figs-extrainfo.md` - Preserving intentional ambiguity

## Creating New Issue Skills

To add a new translation issue type:
```
.claude/skills/utilities/create-issue-skill.md
```

Track progress in `data/translation-issues.csv`.

## Authoritative Sources

Skills draw from these sources (in priority order):
1. **Issues Resolved** - Content team decisions (final authority)
2. **TN Templates** - Official note templates
3. **Processed Translation Notes** - Human-identified examples
4. **Translation Academy** - Definitions and explanations

## Roadmap

- [ ] Literal-transform skill development
- [ ] Simplified-transform skill development
- [ ] Hebrew-reference skill development
- [ ] Note-writing skill development

