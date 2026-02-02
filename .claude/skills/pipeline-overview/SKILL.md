# Pipeline Overview

## Purpose
This skill provides an overview of the unfoldingWord Book Package creation pipeline and guides you to the appropriate specialized skill for each stage.

## The Four-Stage Pipeline

### Stage 1: Literal Transform (ULT)
Transform source text into unfoldingWord Literal Text - a highly literal translation that preserves the form and structure of the original languages.

**Skill**: `.claude\skills\literal-transform\SKILL.md`
**Status**: To be developed

### Stage 2: Simplified Transform (UST)
Transform source text into unfoldingWord Simplified Text - a meaning-based translation that makes implicit information explicit and restructures for clarity.

**Skill**: `.claude\skills\simplified-transform\SKILL.md`
**Status**: To be developed

### Stage 3: Issue Identification
Analyze biblical text to identify translation issues that require notes - figures of speech, cultural concepts, grammatical patterns, etc.

**Skill**: `.claude\skills\issue-identification\SKILL.md`
**Status**: Active (6 issue types documented)

### Stage 4: Note Writing
Generate translation notes based on identified issues using the appropriate templates.

**Skill**: `.claude\skills\note-writing\SKILL.md`
**Status**: To be developed

## When to Use Each Stage

| Task | Stage | Skill Location |
|------|-------|----------------|
| Creating ULT text | 1 | literal-transform\ |
| Creating UST text | 2 | simplified-transform\ |
| Finding what needs notes | 3 | issue-identification\ |
| Writing the actual notes | 4 | note-writing\ |

## Supporting Skills

### Hebrew Reference
Reference material for Hebrew language patterns and vocabulary.

**Skill**: `.claude\skills\hebrew-reference\SKILL.md`
**Status**: To be developed

### Utilities
Tools for fetching resources, creating new issue skills, and other supporting functions.

**Skill**: `.claude\skills\utilities\SKILL.md`
**Status**: Active

## Common Workflows

### "Create translation notes for [passage]"
1. Use **issue-identification** to find translation issues
2. Use **note-writing** to generate notes for each issue

### "Create skill for [issue type]"
1. Use **utilities\create-issue-skill.md** to create a new identification skill

### "What figure of speech is this?"
1. Use the appropriate skill in **issue-identification\** (e.g., figs-metaphor.md, figs-idiom.md)

## Authoritative Sources

All skills draw from these sources (in order of authority):
1. **Issues Resolved** - Content team decisions (final authority)
2. **TN Templates** - Official note templates
3. **Processed Translation Notes** - Human-identified examples
4. **Translation Academy** - Definitions and explanations
