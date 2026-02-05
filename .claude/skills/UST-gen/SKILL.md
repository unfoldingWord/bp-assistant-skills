---
name: UST-gen

description: Transform Hebrew USFM into unfoldingWord Simplified Text (UST) - a meaning-based translation that clearly communicates the meaning of the original text in natural English.

allowed-tools: Read, Grep, Glob, Bash
---

## 7-Step Workflow

### Step 1: Parse Hebrew Input

Read Hebrew USFM from `data/hebrew_bible/*.usfm`. Extract verse text from `\w` tags with morphology (lemma, strong, x-morph).

For context, also read the corresponding ULT to understand how the passage was rendered literally:

```bash
# Parse ULT alignment to see Hebrew->English mappings
node .claude/skills/utilities/scripts/usfm/parse_usfm.js \
  data/published_ult/11-1KI.usfm \
  --chapter 1 --output-json /tmp/alignments.json
```

### Step 2: Read ULT Reference

Read the corresponding ULT passage. The UST should express the **same meaning** as the ULT but in natural, clear English.

Key relationship:
- ULT shows **what the Hebrew says** (form)
- UST shows **what the Hebrew means** (meaning)

### Step 3: Identify Transformation Needs

Scan for elements that need UST transformation:
- Hebrew idioms (body parts, emotions, etc.)
- Metaphors and figures of speech
- Abstract nouns that could be verbal
- Passive constructions
- Initial conjunctions ("And...")
- Formal/archaic expressions
- Implicit information that helps clarity

Consult `reference/ust_patterns.md` for transformation guidance.

### Step 4: Generate Meaning-Based Draft

Apply transformations in this order:

#### A. No Initial Conjunctions

UST sentences should NOT start with "And," "But," or similar conjunctions.

| ULT | UST |
|-----|-----|
| "And his servants said" | "So his officials said" / "His officials said" |
| "And they sought" | "They searched" |
| "But he did not call" | "However, he did not invite" |

Use logical connectors when needed: "So", "However", "Therefore", "Then", "Meanwhile"

#### B. Active Voice

Convert passive to active voice whenever possible.

| ULT (passive) | UST (active) |
|---------------|--------------|
| "A psalm written by David when..." | "David wrote this song when..." |
| "it was told to Solomon" | "Someone told Solomon" |

#### C. Idiom Explanations

Express the **meaning** of Hebrew idioms, not the literal form.

| Hebrew Idiom | ULT | UST |
|--------------|-----|-----|
| אֶרֶךְ אַפַּיִם | "long of nostrils" | "does not quickly become angry" |
| בֹּא בַּיָּמִים | "come into days" | "very old" |
| לִפְנֵי | "to the face of" | "with" / "in the presence of" |
| יָדַע + person | "knew her" | "have sexual relations with her" |

See `reference/ust_patterns.md` for complete idiom list.

#### D. Key Vocabulary - Runtime Lookups

**Do NOT guess vocabulary translations. Run the lookup scripts for key terms.**

1. **First**: Check `data/issues_resolved.txt` for authoritative UST decisions
   ```bash
   grep -i "UST" data/issues_resolved.txt | grep -i "[term]"
   ```

2. **Second**: Check glossaries for UST_GLOSS column
   ```bash
   grep "[term]" data/glossary/hebrew_ot_glossary.csv
   ```

3. **Third**: Search published UST for how terms were rendered
   ```bash
   grep -r "[term]" data/published_ust/*.usfm | head -10
   ```

#### E. Title and Address Terms

| ULT | UST |
|-----|-----|
| "my lord the king" | "Your Majesty" |
| "the sons of Israel" | "Israelites" |
| "the sons of Ammon" | "the Ammonites" |
| "sons of [person]" | "descendants of [person]" |
| "the servant of Yahweh" (appositive) | "Yahweh's servant" |

#### F. Divine Names

Same as ULT:
- יהוה (YHWH) = "Yahweh"
- אֲדֹנָי (Adonai) = "Lord"
- אֵל / אֱלֹהִים = "God"

But for "angel of Yahweh" use: "an angel representing Yahweh"

#### G. Special Terms

| Hebrew | UST Rendering |
|--------|---------------|
| אַשְׁרֵי | "What a good life..." |
| סֶלָה | "Selah" (keep same) |
| שׁוֹפָר | "horn" (first instance: "ram's-horn trumpet") |
| מִדְבָּר | "desolate area" / "dry place" / "uninhabited region" |
| תּוֹרָה | "instruction" |

### Step 5: Add Implicit Information

Use {brackets} to add background or implicit information that helps clarity.

**When to add:**
- Location clarification: "{the village of} Elkosh"
- Category identification: "{the city of} Nineveh"
- Contextual bridges: "{The king gave them permission,} so they searched"
- Meaning clarification: "he will certainly punish {those who have done evil things}"

**Length limits:**
- Should not be as long as a regular sentence
- Can be a short complete sentence if reworking would be longer

**Do NOT use brackets for:**
- Grammar words (that's ULT's use of brackets)
- Information that's already clear from context

### Step 6: Format as USFM

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

\f + \fq quoted text \ft explanation\f*
```

**Poetry markers:**
- `\q1` - first colon of a verse (the "A" line)
- `\q2` - second/third colon (parallel lines)
- `\qa` - acrostic heading
- `\d` - superscription (Psalms)
- `\qs ... \qs*` - Selah

### Step 7: Export to File

Save the completed UST to `output/AI-UST/` with the naming convention:

```
output/AI-UST/[BOOK]-[CHAPTER].usfm
```

Examples:
- `output/AI-UST/NAM-01.usfm` - Nahum chapter 1
- `output/AI-UST/PSA-023.usfm` - Psalm 23
- `output/AI-UST/1KI-01.usfm` - 1 Kings chapter 1

Use three-letter book codes and two-digit chapter numbers (zero-padded).

---

## Scripts Reference

### Vocabulary lookup
```bash
# 1. Check authoritative UST decisions
grep -i "UST" data/issues_resolved.txt | grep -i "[term]"

# 2. Check glossaries (UST_GLOSS column)
grep "[term]" data/glossary/hebrew_ot_glossary.csv

# 3. Search published UST for patterns
grep -r "[term]" data/published_ust/*.usfm | head -10

# 4. Compare ULT to UST for same verse
grep "1:1" data/published_ult_english/11-1KI.usfm
grep "1:1" data/published_ust/11-1KI.usfm
```

### Fetch UST data
```bash
# Fetch all published UST books
python3 .claude/skills/utilities/scripts/fetch_all_ust.py

# Fetch specific books
python3 .claude/skills/utilities/scripts/fetch_all_ust.py --books NAM PSA 1KI
```

### Parse aligned USFM
```bash
node .claude/skills/utilities/scripts/usfm/parse_usfm.js \
  data/published_ult/[BOOK].usfm \
  --chapter [N] \
  --output-json /tmp/alignments.json
```

---

## Quality Checklist

Before finalizing UST output, verify:

- [ ] No sentences starting with "And" or "But"
- [ ] Active voice used (not passive) where possible
- [ ] Hebrew idioms expressed as meaning, not literal
- [ ] Natural English word order
- [ ] Same proper names as ULT (no modern equivalents)
- [ ] Metaphors and figures explained, not literal
- [ ] Clear, common vocabulary (not formal/archaic)
- [ ] {brackets} used for implicit/background info only
- [ ] USFM markers properly formatted
- [ ] Poetry uses \q1/\q2 appropriately
- [ ] Key vocabulary matches Issues Resolved decisions
- [ ] Psalm superscriptions use active voice
- [ ] "sons of X" transformed appropriately (Israelites, descendants, etc.)
- [ ] Divine names correct (Yahweh, not LORD)
- [ ] Selah retained as "Selah"
- [ ] "peoples" kept as "peoples" (not changed to singular)

---

## Data Sources (Runtime Lookups)

**Always check these at runtime - do not rely on memory:**

| Source | Path | Purpose |
|--------|------|---------|
| Issues Resolved | `data/issues_resolved.txt` | FINAL AUTHORITY - UST decisions |
| Hebrew Glossary | `data/glossary/hebrew_ot_glossary.csv` | UST_GLOSS column |
| Psalms Reference | `data/glossary/psalms_reference.csv` | UST_GLOSS column |
| Sacrifice Terms | `data/glossary/sacrifice_terminology.csv` | UST_GLOSS column |
| Biblical Phrases | `data/glossary/biblical_phrases.csv` | UST_GLOSS column |
| Published UST | `data/published_ust/*.usfm` | Parallel patterns |
| Published ULT | `data/published_ult_english/*.usfm` | Reference for meaning |
| UST Patterns | `reference/ust_patterns.md` | Transformation rules |
| Style Guide | `../ULT-gen/reference/gl_guidelines.md` | Shared style rules |

---

## Related Skills

- [Pipeline Overview](../pipeline-overview/SKILL.md) - Where this fits in the workflow
- [ULT-gen](../ULT-gen/SKILL.md) - Literal translation (form-based)
- [Issue Identification](../issue-identification/SKILL.md) - Finding translation issues
- [Hebrew Reference](../hebrew-reference/SKILL.md) - Hebrew language patterns
