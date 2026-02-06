# Pipeline Overview

## Purpose
This skill provides an overview of the unfoldingWord Book Package creation pipeline and guides you to the appropriate specialized skill for each stage.

## The Five-Stage Pipeline

### Stage 1: Literal Transform (ULT)
Transform source text into unfoldingWord Literal Text - a highly literal translation that preserves the form and structure of the original languages.

**Skill**: `.claude/skills/ULT-gen/SKILL.md`
**Status**: Active

### Stage 1b: ULT Alignment
Create word-level alignments between Hebrew source and English ULT. AI produces a simple index-based mapping JSON that a script converts to aligned USFM.

**Skill**: `.claude/skills/ULT-alignment/SKILL.md`
**Status**: Active

### Stage 2: Issue Identification
Analyze biblical text to identify translation issues that require notes - figures of speech, cultural concepts, grammatical patterns, etc.

**Agent**: `.claude/agents/issue-identification.md`
**Invoke**: Use the Task tool with `subagent_type: issue-identification`
**Status**: Active (93 issue types documented)

### Stage 3: Simplified Transform (UST)
Transform source text into unfoldingWord Simplified Text - a meaning-based translation that makes implicit information explicit and restructures for clarity.

**Skill**: `.claude/skills/UST-gen/SKILL.md`
**Status**: Active

### Stage 4: Note Writing
Generate translation notes from identified issues. A preparation script handles deterministic work (template matching, language conversion, ID generation), then AI generates note text following the style guide.

**Skill**: `.claude/skills/tn-writer/SKILL.md`
**Status**: Active

## When to Use Each Stage

| Task | Stage | Skill Location |
|------|-------|----------------|
| Creating ULT text | 1 | ULT-gen/ |
| Aligning ULT to Hebrew | 1b | ULT-alignment/ |
| Finding what needs notes | 2 | agents/issue-identification (Task tool) |
| Creating UST text | 3 | UST-gen/ |
| Writing the actual notes | 4 | tn-writer/ |

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
