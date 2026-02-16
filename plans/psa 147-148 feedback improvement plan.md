# Fix PSA 147-149 Issues: Skill Improvements + Verse Corrections

## Context

Review of AI-generated PSA 147-149 output revealed ~50 issues across ULT, UST, TNs, alignment, and TQs. The user's priority is **skill/prompt improvements** to prevent recurrence, not just one-off fixes. The user warns against over-correction ("being really nitpicky... don't over correct") and wants a light hand on edits. Feedback covers 147:1-148:14 (149 not reviewed in the file).

**Highlighting concept** (from screenshots): In translationCore, a TN's Hebrew quote field maps to aligned Hebrew, which highlights the corresponding ULT/UST text in yellow. Broken quotes (wrong Hebrew, missing direct object marker) break highlighting and make notes unusable.

---

## Phase 1: Skill Improvements (15-20 light-touch edits across ~8 files)

### 1A. ULT-gen SKILL.md

| Edit | What | Where (approx line) |
|------|------|---------------------|
| Merge adjacent brackets | Add rule: `{it} {is}` -> `{it is}` | After line 264, end of Step 4 |
| Clarify copula bracketing | Amend line 247: copula bracket only when no verb AND no participle | Line 247 |
| Strengthen Yoda-speak | Add "read aloud" check to Step 5 Word Order section | After line 273 |
| Cross-verse sentences | Add guidance on sentences spanning verse breaks | Before Step 5, new subsection in Step 3 |

### 1B. UST-gen SKILL.md

| Edit | What | Where |
|------|------|-------|
| Reinforce T4T baseline | Add checkpoint: "re-read T4T before each verse, modifications should be traceable to T4T phrasing" | Step 4 opening |
| Synonym differentiation | Add: compare key words against ULT, find synonyms where both use same word | After vocabulary table |
| Figurative speech handling | Add: UST must unpack metaphors/idioms into plain meaning, not preserve literal image | Step 2.5 issue integration |

### 1C. TN-writer SKILL.md

| Edit | What | Where |
|------|------|-------|
| ID format rule | Document `[a-z][a-z0-9]{3}` requirement explicitly | Step 2a |
| No antithetical parallelism notes | Add: only synonymous parallelism gets notes | Step 6 |
| AT fit reminder | Add: check the word immediately before gl_quote; AT must fit seamlessly | Step 6 |
| Note suppression | Add: semantic notes (idiom, metaphor) can suppress less informative structural notes (possession) for same phrase | Step 6 |
| Hebrew quote `&` connector | Document the `&` syntax for discontinuous Hebrew quotes when DO marker is unaligned | Step 2c |
| Highlighting check | Add to final review: verify Hebrew quotes produce correct highlighting | Step 10 |

### 1D. TN-writer note-style-guide.md

| Edit | What | Where |
|------|------|-------|
| Bold exactness | Reinforce: verify word appears verbatim in ULT before bolding | After line 21 |
| Psalms author reference | Add: never use "the writer" in Psalms; use attributed author or "the psalmist" | After line 77 |

### 1E. ULT-alignment alignment_rules.md

| Edit | What | Where |
|------|------|-------|
| DO marker consistency | Add: handle every direct object marker the same way throughout a chapter | After DO marker section |
| "Name of" pattern | Add: align "name" (shem) with the noun, not the governing verb | New subsection in Word Type Rules |

### 1F. UST-alignment ust_alignment_rules.md

| Edit | What | Where |
|------|------|-------|
| "Name" with proper noun | Add: when UST omits "name", align "Yahweh" with the Hebrew proper noun, not the verb | Names section |

### 1G. figs-possession.md (issue-identification)

| Edit | What | Where |
|------|------|-------|
| Suppression by semantic notes | Add: when idiom/metaphor covers same phrase, suppress possession note | After existing suppression rules |

### Critical Files
- `.claude/skills/ULT-gen/SKILL.md` (lines 242-274)
- `.claude/skills/UST-gen/SKILL.md` (lines 9-18, 114-127, vocabulary table area)
- `.claude/skills/tn-writer/SKILL.md` (Steps 2a, 2c, 6, 10)
- `.claude/skills/tn-writer/reference/note-style-guide.md` (lines 21, 74-79)
- `.claude/skills/ULT-alignment/reference/alignment_rules.md` (DO marker section, Word Type Rules)
- `.claude/skills/UST-alignment/reference/ust_alignment_rules.md` (Names section)
- `.claude/skills/issue-identification/figs-possession.md` (suppression section)

---

## Phase 1.5: Review PSA 149 Output (same session as Phase 1)

Review PSA 149 output files against the same patterns found in 147-148. Look for:
- Bracket issues (`{is}` on copulas, adjacent brackets not merged)
- UST divergence from T4T
- AT fit problems, bold exactness, ID format
- Alignment issues (DO markers, name-with-Yahweh)
- Missing/incorrect notes (antithetical parallelism notes, apostrophe/personification)

Add any findings to the feedback file or note them for skill improvement validation.

---

## (Future) Phase 2: Re-run PSA 147-148 with Improved Skills

After skill edits, re-run `/makeBP` or `/initial-pipeline` for PSA 147 and 148. Compare output against the feedback file to measure how many issues are resolved by skill improvements alone.

Focus areas for comparison:
- Bracket merging and copula handling
- Yoda-speak in 147:10
- T4T adherence in UST
- Antithetical parallelism filtering (147:6)
- ID format (all start with [a-z])
- AT fit across all notes

---

## Phase 3: Manual Verse-Specific Corrections

After re-run, check remaining issues verse-by-verse against the feedback file. Key items that skill improvements alone won't fully resolve:

**ULT fixes**: 147:1 stanza break, 147:10 word order, 147:14-15 multi-verse sentence, 147:19 ketiv/qere singular "word", 148:1 alignment, 148:14 stanza break

**TN fixes**: 147:1 combine notes 04f8+1763, 147:3 reclassify 2c3b to figure of speech, 147:9 suppress possession note, 147:10 dedup 855f/87d4, 147:12 fix 98bd quote field, 147:13 reclassify ad82, 147:18 "psalmist" fix + remove old notes, 147:20 improve contrast AT + add "see how" note + abstract noun note, 148:4 add apostrophe notes, 148:5 fix fh50 quote + rewrite o7d2, 148:7 expand litany range to 7-12, 148:8 add chiasm note, 148:9 fix o2mx quote + add apostrophe, 148:10 combine merism notes + add apostrophe, 148:13 fix vzip DO marker + add passive note

**Alignment fixes**: 147:3 "the" with "broken of", 147:7 flip sing/thank in UST, 147:11 unsplit merged Hebrew words, 147:15 UST second stanza, 147:18 UST "gives", 148:1 DO marker + "from"/"heavens" split, 148:5 name with Yahweh, 148:11 "all" alignment, 148:13 name with Yahweh

---

## Phase 4: Research -- Alienable vs Inalienable Possession

Spin off a subagent to research this linguistic concept (user request from 147:10 feedback). Many languages (Russian, Oceanic, African families) distinguish body-part possession from acquired-object possession grammatically.

Add a new section to `figs-possession.md` covering:
- What alienable/inalienable distinction means
- Biblical examples (body parts = inalienable, objects = alienable)
- Why it matters for translation notes

---

## Phase 5: Process Improvement -- Verification Agent

The user identified a truth/completeness problem: AI sometimes claims tasks are done when they aren't (e.g., "TNs already inserted" when they weren't).

Add a post-process verification checklist concept to the pipeline overview skill:
- Completeness: confirm each expected output file exists with content
- Instruction adherence: re-read skill requirements and verify each was met
- Spot-check: read 3-5 random verses against skill rules
- Repo state: if insertion was done, verify files are committed

---

## Execution Scope (this session)

**Phase 1 + 1.5 only.** Make the skill edits, then review PSA 149 output. Phases 2-5 are documented for future sessions.

## Verification (this session)

- Read each edited skill file after editing; confirm edits are light-touch, no CRITICAL/ALL CAPS language
- Confirm no existing skill behavior was accidentally removed or contradicted
- PSA 149 review: document findings, note any additional skill gaps discovered
