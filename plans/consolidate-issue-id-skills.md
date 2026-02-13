# Consolidate deep-issue-id into issue-identification

**Priority: Secondary to making 2-agent team the primary mode.** We'll likely trim more fat during that change, so consolidation should happen after.

## Problem

deep-issue-id duplicates content from issue-identification that the analysts already receive (they spawn with `subagent_type: "issue-identification"`).

## Word-for-word duplicates to remove from deep-issue-id

- Output format firewall (lines ~258-287) -- identical rules
- Grammar independence rule (challenger section) -- same as final review pass
- Abstract noun detection command -- same as Step 4
- Confused pairs in challenger criteria -- subset of the Commonly Confused table

## Near-duplicates

- Fetch/parse/compare setup (same scripts, different tmp paths)
- Passive voice instructions (same "see figs-activepassive.md" guidance)

## What's actually unique to deep-issue-id (keep)

- Team orchestration (TeamCreate, waves, shutdown, patience rules)
- Agent domain assignments + cross-reading protocol
- Challenger role (challenge/defend/ruling cycle)
- Merge procedure
- Verse range chunking
- Lite vs full mode structure

## Target structure

deep-issue-id becomes a thin orchestration wrapper:
1. "Run setup per issue-identification steps 1-4 using $TMP" (not duplicated commands)
2. Team setup + wave orchestration (unique content)
3. References issue-identification for output format, quality checks, etc.

## Also consider during this work

- Make --lite (2-agent) the default, require --full for 4-agent
- PSA 87 data shows 2-agent produces equivalent quality (30 vs 29 issues)
- 4-subagent-without-team was worst (42 noisy issues) -- drop that option
- The initial-pipeline skill has similar duplication to audit
