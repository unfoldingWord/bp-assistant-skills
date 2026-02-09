---
name: UST-gen

description: Transform T4T (Translation for Translators) into unfoldingWord Simplified Text (UST) - a meaning-based translation that clearly communicates the meaning of the original text in natural English.

allowed-tools: Read, Grep, Glob, Bash
---

## Important: T4T-Based Workflow

The UST creation process starts with the **T4T (Translation for Translators)** as the base text. The goal is to **modify T4T as little as possible** while ensuring it is:
1. **True to the Hebrew** (final authority on meaning)
2. **Consistent with the ULT** (same meaning, different form)
3. **Compliant with unfoldingWord standards** (style, vocabulary, formatting)

**Do NOT start from scratch.** Read the T4T first, verify it against Hebrew/ULT, then make targeted adjustments.

**Note on published UST:** The UST currently on Door43, if not from our recently published approved work, was adapted from T4T long ago by underskilled volunteers and should largely be ignored as a reference. Use T4T as your primary starting point.

---

## Key Principle: Differentiate from ULT

The UST must be **noticeably different** from the ULT. If the only difference is removing "And" at the start, you haven't done enough.

**The UST should:**
- Use **simpler, more common words** than the ULT
- **Explain meaning** rather than preserve form


**Test:** Read the ULT and UST side by side. If they sound nearly identical, rewrite the UST.

| ULT | Bad UST (too similar) | Good UST (differentiated) |
|-----|----------------------|---------------------------|
| "He gave over their cattle to the hail" | "He gave over their cattle to the hail" | "He let the hail kill their cattle" |
| "and their livestock to the bolts of lightning" | "and their livestock to the bolts of lightning" | "and he let lightning strike their livestock" |
| "They tested God in their heart" | "They tested God in their heart" | "They challenged God to see if he would help them" |
| "by asking for food for their craving" | "by asking for food for their craving" | "by demanding the food they wanted" |

### Simpler Vocabulary

Prefer common words over formal/literary ones:

| ULT/Formal | UST/Simple |
|------------|------------|
| livestock | animals / herds |
| craving | desire / want |
| iniquity | sin / evil |
| transgressions | sins |
| rebuke | correct / scold |
| wrath | anger |
| affliction | suffering / trouble |
| insolent | proud / arrogant |
| abhor | hate / reject |
| slumber | sleep |
| give over to | let X destroy / hand over to |

### Collapsing Parallelism

Hebrew poetry often says the same thing twice with different words (synonymous parallelism). In UST, **collapse true parallelism into one statement** when both lines express the same meaning.

| ULT (parallel lines) | UST (collapsed) |
|---------------------|-----------------|
| "He gave over their cattle to the hail / and their livestock to the bolts of lightning" | "He sent a terrible thunderstorm with hail to kill all their cattle" |
| "They did not keep the covenant of God / and they refused to walk in his law" | "They refused to obey God's covenant and law" |
| "Yahweh knows the way of the righteous / but the way of the wicked will perish" | Keep both - this is **antithetic** parallelism (contrast), not synonymous |

**Judgment call:** If the second line adds new information or contrasts with the first, keep both lines. If it just restates the first line with different words, collapse them.

---

## 7-Step Workflow

### Step 1: Read T4T Base

Read the T4T from `data/t4t/*.usfm`. This is your starting point.

```bash
# Fetch T4T if not present
python3 .claude/skills/utilities/scripts/fetch_t4t.py --books PSA 1KI
```

T4T uses special markers that serve two purposes:
1. **Guide your UST rendering** - they identify translation issues in the text
2. **Must be removed** - the markers themselves don't appear in final UST

| Marker | Meaning | UST Implication |
|--------|---------|-----------------|
| `\add...\add*` | Implicit information | Usually weave into prose; rarely bracket |
| `[IDI]` | Idiom | Render the meaning, not literal form |
| `[DOU]` | Doublet (repetition for emphasis) | May simplify or keep both terms |
| `[SYN]` | Synecdoche (part for whole) | Express the intended referent |
| `[RHQ]` | Rhetorical question | Keep as question or convert to statement |
| `[EUP]` | Euphemism | Use clear language |
| `[MTY]` | Metonymy (association) | Express what is actually meant |

These markers are valuable pre-identified translation issues - use them to inform your rendering choices before removing them from the final text.

### Step 2: Verify Against Hebrew and ULT

Check that T4T accurately represents the Hebrew meaning:

1. **Read Hebrew source** from `data/hebrew_bible/*.usfm` - this is the final authority
2. **Read corresponding ULT** - shows the literal form for comparison
3. **Note any discrepancies** between T4T and Hebrew/ULT

Key relationship:
- Hebrew = **final authority** on meaning
- ULT = **what the Hebrew says** (form)
- T4T/UST = **what the Hebrew means** (meaning)

If T4T diverges from Hebrew meaning, correct it. If T4T and ULT express the same meaning differently, that's expected - they serve different purposes.

### Step 2.5: Check Identified Translation Issues

Before generating UST, check for any pre-identified translation issues:

1. Look for issue files at `output/issues/[BOOK]-[CHAPTER].tsv`
2. If found, read the identified issues - these flag constructions needing attention:
   - **figs-activepassive**: MUST convert to active voice in UST
   - **figs-abstractnouns**: Consider verbal/clausal forms
   - **figs-nominaladj**: Unpack nominalized adjectives
   - **figs-metaphor/figs-simile**: Express the meaning
   - **figs-idiom**: Explain rather than preserve
   - **figs-rquestion**: Consider if rhetorical function is clear

3. Use identified issues to guide your transformation decisions in Step 4

### Step 3: Identify Changes Needed

Compare T4T to unfoldingWord standards. Flag areas that need adjustment:

1. **Check Issues Resolved** for authoritative decisions
   ```bash
   grep -i "UST" data/issues_resolved.txt | grep -i "[term or topic]"
   ```

2. **Remove T4T notation markers** - [IDI], [DOU], [SYN], [RHQ], [EUP], [MTY]

3. **Handle `\add...\add*` markers** - weave into prose; rarely bracket (see Step 4A)

4. **Check for unfoldingWord-specific requirements:**
   - Divine names: Must use "Yahweh" (not "the LORD")
   - Proper names: Same as ULT (no modern equivalents)
   - Active voice for psalm superscriptions
   - No initial conjunctions ("And", "But")

### Step 4: Make Minimal Modifications

Apply only necessary changes. The T4T is already a good meaning-based translation.

#### A. Handle T4T Markers

| T4T | UST |
|-----|-----|
| `\add text \add*` | Evaluate: most become unbracketed natural prose |
| `[IDI]`, `[DOU]`, etc. | Remove entirely |
| `[RHQ]` | Remove (keep the rhetorical question) |

**T4T `\add...\add*` markers:** These mark where T4T added clarifying information. In UST, most of this content should be woven into natural prose WITHOUT brackets. Only use {brackets} when the added content is:
1. Truly absent from the Hebrew (not just restructured)
2. Essential for comprehension (not just helpful)
3. Would seem "added" to a careful reader

See `reference/ust_patterns.md` Section 8 for detailed guidance.

#### B. Divine Names (if needed)

T4T may use "the LORD" or other renderings. Update to:
- יהוה = "Yahweh"
- אֲדֹנָי = "Lord"
- אֵל / אֱלֹהִים = "God"
- "angel of Yahweh" = "an angel representing Yahweh"

#### C. Check Vocabulary Against Issues Resolved

```bash
# Check for specific term decisions
grep -i "UST" data/issues_resolved.txt | grep -i "[term]"

# Check UST Strong's index for published precedent
python3 .claude/skills/utilities/scripts/build_ust_index.py --lookup H2617

# Check glossaries
grep "[term]" data/glossary/hebrew_ot_glossary.csv
```

When a vocabulary decision requires checking published precedent (UST index, glossaries, or issues_resolved), record it in `data/quick-ref/ust_decisions.csv` for future reference. Only record non-trivial decisions -- common words that map obviously don't need tracking.

```bash
# Check if decision already recorded
grep "H2617" data/quick-ref/ust_decisions.csv 2>/dev/null

# Append new decision (creates file with header if needed)
echo "H2617,chesed,faithful love,PSA,dominant UST rendering 67%,,$(date +%Y-%m-%d)" >> data/quick-ref/ust_decisions.csv
```

#### D. Active Voice

Every passive construction must be converted to active voice.

Detection pattern: auxiliary (be/is/are/was/were/been/being) + past participle

| ULT/T4T (passive) | UST (active) |
|-------------------|--------------|
| "they will be killed" | "they will die" / "someone will kill them" |
| "will be eaten by jackals" | "jackals will eat" |
| "A psalm written by David" | "David wrote this song" |
| "it was told to Solomon" | "Someone told Solomon" |

**If you cannot identify the agent**, use:
- Generic agent: "Someone told...", "People will..."
- Intransitive alternative: "they will die" instead of "they will be killed"
- God as agent (divine passive): "God will judge them"

#### E. Abstract Nouns to Verbal Forms

When identified issues flag **figs-abstractnouns**, convert the abstract noun to a verbal or clausal form:

| Abstract (ULT/T4T) | Verbal (UST) |
|--------------------|--------------|
| "the salvation of Yahweh" | "how Yahweh saves" |
| "his righteousness" | "how righteous he is" |
| "the fear of Yahweh" | "to deeply respect Yahweh" |
| "covenant faithfulness" | "You are always kind to me, as you promised" |
| "his power and glory" | "how powerful and glorious you are" |

Ask: What action or quality does this noun represent? Express it as a verb or clause.

#### F. Nominalized Adjectives

When identified issues flag **figs-nominaladj**, unpack the nominalized adjective into its full meaning:

| Nominalized (ULT/T4T) | Unpacked (UST) |
|-----------------------|----------------|
| "the wicked" | "wicked people" / "people who do evil" |
| "the righteous" | "righteous people" / "people who do what is right" |
| "the dead" | "dead people" / "people who have died" |
| "the poor" | "poor people" / "people who are poor" |

The UST should make clear who or what is being described.

#### G. Psalm Superscriptions

(See Active Voice above for passive → active conversion)

#### H. Initial Conjunctions

If T4T starts sentences with "And" or "But", replace:
- "And" → "So" / "Then" / remove
- "But" → "However" / remove

### Step 5: Verify Against Standards

Cross-check with:
- `reference/ust_patterns.md` - transformation patterns
- `../ULT-gen/reference/gl_guidelines.md` - shared style rules

**{Brackets} - Use Sparingly:**
- Most clarifying information should be woven into natural prose without brackets
- Only bracket content that is truly unexpressed in the source AND essential for comprehension
- Length limit: Should not be as long as a regular sentence
- When in doubt, write naturally without brackets

### Step 6: Format as USFM

Ensure proper USFM formatting:

```usfm
\id [BOOK] - unfoldingWord Simplified Text
\usfm 3.0
\h [Book Name]
\toc1 [Full Book Name]
\toc2 [Abbreviated Name]
\toc3 [Short Code]
\mt [Main Title]

\c [chapter]
\p
\v [verse] [text]

\ts\*
\q1 [poetry line 1]
\q2 [poetry line 2 - indented]
```

**Poetry markers:**
- `\q1` - first colon of a verse
- `\q2` - second/third colon (parallel lines)
- `\d` - superscription (Psalms)
- `\qs ... \qs*` - Selah

### Step 7: Export to File

Save to `output/AI-UST/` with naming convention:

```
output/AI-UST/[BOOK]-[CHAPTER].usfm
```

### Step 7.5: Write Alignment Hints

After writing the UST USFM, write a hints JSON that records which Hebrew words you rendered in each English phrase. As you generated each phrase, you knew which Hebrew concepts you were rendering -- capture that mapping now.

Output path: `output/AI-UST/hints/<BOOK>-<CH>.json`

Format:
```json
[
  {
    "reference": "PSA 1:1",
    "hints": [
      {"english": "The person who will have a truly good life", "hebrew_indices": [0, 1]},
      {"english": "is the person who", "hebrew_indices": [2]},
      {"english": "does not do what evil people tell him to do,", "hebrew_indices": [3, 4, 5, 6]},
      {"english": "{It seems like}", "hebrew_indices": [], "implied": true}
    ]
  }
]
```

Rules:
- One entry per verse
- `english` = phrase from the UST, matching `english_text` word-for-word
- `hebrew_indices` = which Hebrew word positions (0-based) contributed meaning to that phrase
- Add `"implied": true` on entries with bracketed content (`hebrew_indices: []`)
- Phrases should cover all English words (complete coverage)
- Granularity: phrase-level, not word-level. Group by the meaning units you were thinking in.
- This is a rough draft for the aligner, not a finished alignment. Don't overthink it.

### Step 8: Convert to Curly Quotes

Run the curly quotes script to convert straight quotes to curly quotes:

```bash
python3 .claude/skills/utilities/scripts/curly_quotes.py \
  output/AI-UST/[BOOK]-[CHAPTER].usfm --in-place
```

This converts:
- Straight double quotes `"..."` to curly `"..."`
- Straight single quotes/apostrophes `'...'` to curly `'...'`

---

## Scripts Reference

### Fetch T4T (primary source)
```bash
# Fetch T4T books
python3 .claude/skills/utilities/scripts/fetch_t4t.py --books PSA 1KI

# List available books
python3 .claude/skills/utilities/scripts/fetch_t4t.py --list
```

### Vocabulary lookup
```bash
# 1. Check authoritative UST decisions
grep -i "UST" data/issues_resolved.txt | grep -i "[term]"

# 2. Check prior UST vocabulary decisions
grep "H2617" data/quick-ref/ust_decisions.csv 2>/dev/null

# 3. Check UST Strong's index for published UST precedent
python3 .claude/skills/utilities/scripts/build_ust_index.py --lookup H2617

# 4. Compare ULT vs UST renderings for the same word
python3 .claude/skills/utilities/scripts/build_ust_index.py --compare H2617

# 5. Check glossaries (UST_GLOSS column)
grep "[term]" data/glossary/hebrew_ot_glossary.csv

# 6. Compare T4T to ULT for same verse
grep "1:1" data/t4t/11-1KI.usfm
grep "1:1" data/published_ult_english/11-1KI.usfm
```

### UST Strong's Index
```bash
# Build/refresh UST index (daily staleness check)
python3 .claude/skills/utilities/scripts/build_ust_index.py

# Look up published UST renderings for a Strong's number
python3 .claude/skills/utilities/scripts/build_ust_index.py --lookup H2617

# Compare ULT (literal) vs UST (meaning-based) renderings
python3 .claude/skills/utilities/scripts/build_ust_index.py --compare H2617

# Index statistics
python3 .claude/skills/utilities/scripts/build_ust_index.py --stats
```

### Parse aligned USFM (for Hebrew verification)
```bash
node .claude/skills/utilities/scripts/usfm/parse_usfm.js \
  data/published_ult/[BOOK].usfm \
  --chapter [N] \
  --output-json /tmp/alignments.json
```

---

## Quality Checklist

Before finalizing UST output, verify:

**T4T Conversion:**
- [ ] T4T notation markers removed ([IDI], [DOU], [SYN], [RHQ], [EUP], [MTY])
- [ ] `\add...\add*` content woven into natural prose (rarely bracketed)
- [ ] Changes are minimal - T4T preserved where it meets standards

**unfoldingWord Standards:**
- [ ] Divine names correct (Yahweh, not LORD)
- [ ] Same proper names as ULT (no modern equivalents)
- [ ] No sentences starting with "And" or "But"
- [ ] **No passive voice** (search for: is/are/was/were/been/being + past participle)
- [ ] **Abstract nouns converted** to verbal/clausal forms where flagged
- [ ] **Nominalized adjectives unpacked** (not just "the dead" but "dead people" or similar)
- [ ] Key vocabulary matches Issues Resolved decisions

**Style:**
- [ ] Natural English word order
- [ ] Clear, common vocabulary
- [ ] {brackets} used sparingly - only for truly unexpressed, essential content
- [ ] Most clarifications woven into natural prose without brackets
- [ ] USFM markers properly formatted
- [ ] Poetry uses \q1/\q2 appropriately
- [ ] "peoples" kept as "peoples"
- [ ] Selah retained as "Selah"

---

## Data Sources (Runtime Lookups)

**Always check these at runtime - do not rely on memory:**

| Source | Path | Purpose |
|--------|------|---------|
| **T4T** | `data/t4t/*.usfm` | PRIMARY SOURCE for UST |
| Issues Resolved | `data/issues_resolved.txt` | FINAL AUTHORITY - UST decisions |
| Hebrew Glossary | `data/glossary/hebrew_ot_glossary.csv` | UST_GLOSS column |
| Psalms Reference | `data/glossary/psalms_reference.csv` | UST_GLOSS column |
| Published ULT | `data/published_ult_english/*.usfm` | Meaning verification |
| UST Strong's Index | `data/cache/ust_index.json` | Published UST renderings by Strong's number |
| UST Decisions | `data/quick-ref/ust_decisions.csv` | Prior UST vocabulary decisions |
| UST Patterns | `reference/ust_patterns.md` | Transformation rules |
| Style Guide | `../ULT-gen/reference/gl_guidelines.md` | Shared style rules |

**Note:** `data/published_ust/` contains older UST that may not meet current standards. Use T4T as your base, not published UST. The UST Strong's index is still useful for seeing how published UST renders specific Hebrew words -- treat it as precedent to consider, not authority to follow.

---

## Related Skills

- [Pipeline Overview](../pipeline-overview/SKILL.md) - Where this fits in the workflow
- [ULT-gen](../ULT-gen/SKILL.md) - Literal translation (form-based)
- [Issue Identification](../issue-identification/SKILL.md) - Finding translation issues
- [Hebrew Reference](../hebrew-reference/SKILL.md) - Hebrew language patterns
