# PSA 119 Issue Review Strategy

All four chunks of deep-issue-id are complete (371 issues across 164/176 verses). This plan covers reviewing those issues for quality, consistency, and completeness.

## What We're Working With

| Chunk | File | Verses | Issues | Avg/verse |
|-------|------|--------|--------|-----------|
| 1 | PSA-119-v1-40.tsv | 1-40 | 105 | 2.6 |
| 2 | PSA-119-v41-80.tsv | 41-80 | 84 | 2.1 |
| 3 | PSA-119-v81-120.tsv | 81-120 | 69 | 1.7 |
| 4 | PSA-119-v121-176.tsv | 121-176 | 113 | 2.0 |

## Known Problems Already Found

### 1. Structural inconsistencies
- **Book field casing**: Chunks 1-2 use `PSA`, chunks 3-4 use `psa`
- **Missing header**: Chunk 4 has no header row
- **Column count**: Chunk 4 has 7 columns (extra empty tabs), chunks 1-3 have 5

### 2. Twelve missing verses (zero issues)
16, 46, 47, 87, 93, 94, 98, 102, 129, 146, 147, 158

These need investigation -- either they genuinely have no taggable issues (unlikely for PSA 119) or they fell through chunk boundaries or got dropped during the challenger round.

### 3. Density drop in chunk 3
Chunks 1-2 average 2.4 issues/verse. Chunk 3 drops to 1.7. Stanzas Lamed (89-96) and Nun (105-112) are thinnest at 1.5 issues/verse. This could be legitimate (simpler Hebrew in those stanzas) or could indicate the agent was fatiguing/rushing. Needs spot-checking against the ULT text.

## Review Plan

### Phase 1: Structural fixes (mechanical, scriptable)

Fix the three structural problems before any semantic review:

1. Normalize Book field to `PSA` in all files
2. Add header row to chunk 4
3. Fix chunk 4 column count (strip extra empty tabs)
4. Verify all rows parse correctly after fixes

This is a 5-minute script task.

### Phase 2: Missing verse triage (agent + ULT text)

For each of the 12 missing verses, pull the ULT text and determine:
- Does the verse genuinely have no translation issues? (Possible for very simple clauses)
- Or was it dropped? If dropped, identify what issues it should have.

Expected: Most will need at least one issue. PSA 119 is dense enough that genuinely empty verses are rare. Any verse with Torah-synonym vocabulary ("your law", "your statutes", etc.) definitely needs at least a metonymy or abstract noun tag.

Output: Either add the missing issues to the appropriate chunk file, or document why each verse has no issues.

### Phase 3: Cross-stanza consistency audit (the big one)

PSA 119 uses the same vocabulary in nearly every stanza. The same Hebrew pattern should get the same issue type and similar explanation across all 22 stanzas. This is the primary thing chunking can break.

**Patterns to audit** (check that each gets consistent treatment everywhere it appears):

| Pattern | Expected issue type | Notes |
|---------|-------------------|-------|
| "your law/teaching" (torah) | figs-metonymy | Represents God's will |
| "your word" (davar/imra) | figs-metonymy | Represents God's communication |
| "your statutes" (khuqqim) | figs-metonymy | Represents God's requirements |
| "your commands/commandments" | figs-metonymy | Represents God's requirements |
| "your testimonies" | figs-metonymy | Represents God's declarations |
| "your judgments" (mishpatim) | figs-abstractnouns | Abstract noun |
| "your precepts" (piqqudim) | figs-metonymy | Represents God's requirements |
| "your ordinances" | figs-metonymy or abstractnouns | Check which was used |
| "way/path of X" | figs-metaphor | Behavior as journey |
| "with all my heart" | figs-metonymy | Heart = devotion |
| "my soul [verbs]" | figs-synecdoche | Soul = whole person |
| "my eyes [verbs]" | figs-synecdoche or metonymy | Eyes = watching/attention |
| Imperatives to God | figs-imperative | Request, not command |
| Nominalized adjectives (the proud, the wicked) | figs-nominaladj | Adjective as noun |
| Passive constructions | figs-activepassive | Note agent |

Method: Grep for each pattern across all four files. Flag any instance where (a) the same Hebrew pattern gets a different issue type than the majority, or (b) the pattern appears in some stanzas but not others where the ULT text has it.

### Phase 4: Thin-verse spot check

43 verses have only 1 issue. Focus on those in the thinnest stanzas (Lamed, Nun, Qoph) where the density is lowest. Pull the ULT text for each and check whether additional issues were missed.

Not every 1-issue verse is wrong -- some genuinely have one notable pattern. But clusters of 1-issue verses in the same stanza suggest the agent got less thorough.

### Phase 5: Merge and final pass

1. Merge all four chunk files into a single `PSA-119.tsv` with consistent formatting
2. Sort by verse number, then by issue type within each verse
3. One read-through of the merged file to catch:
   - Duplicate rows (same verse + same issue type + same ULT text)
   - Explanation quality (are the hints useful for TN writing, or too terse?)
   - Any issue types that seem wrong (e.g., figs-metaphor tagged on a literal statement)

## Execution approach

Phases 1-2 can run together (one session, mostly mechanical). Phase 3 is the most important and should be methodical -- probably worth running grep-based checks with a script, then having an agent review the flagged inconsistencies. Phases 4-5 are one agent pass over the merged output.

Total: probably 2 focused sessions. The structural fixes and missing verses are quick. The consistency audit is the real work.
