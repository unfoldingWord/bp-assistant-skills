# PSA 119 Post-Chunking Review Strategy

After running deep-issue-id --lite in chunks across PSA 119 (176 verses), review the merged output for chunk-boundary artifacts and cross-stanza consistency.

## Suggested Chunks

| Chunk | Verses | Stanzas |
|-------|--------|---------|
| 1 | 1-40 | Aleph through He (5 stanzas) |
| 2 | 41-80 | Vav through Ayin (5 stanzas) |
| 3 | 81-120 | Kaph through Nun (5 stanzas) |
| 4 | 121-152 | Samekh through Qoph (4 stanzas) |
| 5 | 153-176 | Resh through Tav (3 stanzas) |

## Review Steps

### 1. Coverage Check
Verify every verse 1-176 has at least one issue. Any gaps likely mean something was missed at a chunk boundary. A simple script can check this against the merged TSV.

### 2. Cross-Chunk Consistency
PSA 119 repeats the same patterns stanza to stanza ("your law", "your word", "your statutes", "your commands", "your testimonies", etc.). Grep the merged TSV for recurring phrases and verify they got tagged consistently across chunks. If "your statutes" is figs-metonymy in chunk 1 but missing in chunk 3, that's a problem.

Key recurring patterns to check:
- "your law/word/statutes/commands/testimonies/judgments/precepts/ordinances" -- should be consistent issue types
- Passive constructions on similar verbs across stanzas
- Abstract nouns from the same root appearing in multiple stanzas
- "I/my" pronoun references to the psalmist (should be consistent handling)

### 3. Single Review Agent Pass
Have one agent read the full merged TSV against the full ULT text. Not re-identifying issues, just checking:
- Are tags consistent across stanzas for the same Hebrew patterns?
- Did any chunk boundary cause a verse to be missed?
- Are there duplicates at chunk boundaries (last verse of chunk N, first verse of chunk N+1)?
- Do explanation hints stay consistent for the same phrase patterns?

This is cheap (read-only, one agent) and catches the things chunking introduces.

## Token Strategy
- Session 1 (hour before reset): Run chunks 1-2
- Session 2 (fresh window): Run chunks 3-5, then review pass

## Evidence from PSA 87 A/B/C/D Comparison
- 2-agent lite mode (B: 30 issues) matched 4-agent team (A: 29 issues) in quality
- Team coordination matters less with 2 agents (B vs D nearly identical)
- The challenger round is the key quality gate in both modes
- 4-subagent-without-team (C: 42 issues) was the worst -- noisy, unfiltered
