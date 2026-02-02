# Skill Best Practices (Claude Code)

Notes from Anthropic documentation research (Feb 2026).

## File Size

- **Keep SKILL.md under 500 lines** (practical efficiency, not technical limit)
- Ideal: 200-300 lines for core workflow
- Larger skills work but create poor context efficiency

## Loading Behavior

- **Skill descriptions** load at session start (Claude uses to decide when to invoke)
- **Full skill content** only loads when invoked
- Use `disable-model-invocation: true` to keep descriptions out of context until manually invoked

## Data Strategy

### Embed in SKILL.md:
- Core instructions and workflows
- Frequent reference patterns (10-20 items max)
- Default behaviors

### Reference in supporting files (loaded on-demand):
- Large reference material
- API specifications
- Example collections
- Detailed implementations

### Fetch at runtime (for volatile data):
- Use `!`command`` syntax to run shell commands before Claude sees skill
- Example: `!`python scripts/fetch_latest.py``
- Example: `!`grep "term" data/issues_resolved.txt``

## Recommended Structure

```
.claude/skills/my-skill/
  SKILL.md           # Core workflow (200-300 lines)
  reference/
    detailed-docs.md # Large reference (loads on-demand)
    examples/        # Example files (loads when needed)
  scripts/
    fetch_data.py    # Runtime data fetching
```

## Key Principles

1. **Context window fills up fast** - performance degrades as it fills
2. **Subagents get separate context** - use for research-heavy tasks
3. **Run `/context`** to see what's consuming space
4. **Prefer runtime lookups** for frequently-changing data
5. **Skills can include multiple files** - keeps SKILL.md focused

## Skill File Reference Syntax

In SKILL.md, reference supporting files:
```markdown
## Reference Materials
- For complete definitions, see [reference.md](reference.md)
- For examples, see [examples/](examples/)
```

Claude will load these on-demand when needed.

## Dynamic Context Injection

For truly volatile data, use command execution:
```yaml
---
name: my-skill
---

## Current Data
- Latest issues: !`grep "ULT" data/issues_resolved.txt | head -20`

## Your task
[instructions...]
```

This runs the command **before** Claude sees the skill content.
