---
name: ULT-gen

description: Transform Hebrew USFM into unfoldingWord Literal Text (ULT) - a highly literal translation that preserves the form and structure of the original Hebrew while producing clear English.

allowed-tools: Read, Grep, Glob, Bash
---

## 7-Step Workflow

### Step 1: Parse Hebrew Input

Read Hebrew USFM from `data/hebrew_bible/*.usfm`. Extract verse text from `\w` tags with morphology (lemma, strong, x-morph).

For complex passages, use the alignment parser to see how Hebrew was previously translated:

```bash
node .claude/skills/utilities/scripts/usfm/parse_usfm.js \
  data/published_ult/34-NAM.usfm \
  --chapter 1 --output-json /tmp/alignments.json
```

Output shows Hebrew->English mappings:
```json
{
  "ref": "NAM 1:2",
  "source": {"word": "...", "lemma": "...", "strong": "H3068"},
  "english": "Yahweh"
}
```

### Step 2: Analyze Clause Structure

Identify:
- Verb stem/form (wayyiqtol, infinitive construct, participle, etc.)
- Subject, object, modifiers
- Construct chains
- Discourse markers (waw-consecutive, hinneh, etc.)

Query alignment JSON for how specific Hebrew patterns were rendered in published ULT.

### Step 3: Generate Draft Translation

Apply rules in this order:

#### A. Discourse Markers

| Hebrew Pattern | ULT Rendering |
|----------------|---------------|
| wayyiqtol of hayah + time expression | "Now it happened..." |
| waw + wayyiqtol (narrative sequence) | "And/Then/So" + past tense |
| hinneh | "Behold" |
| ki (causal) | "for/because" |
| ki (emphatic/asseverative) | "surely/indeed" |
| pen | "lest" |
| im...im | "whether...or" |
| gam...gam | "both...and" |
| lo...welo | "neither...nor" |

#### B. Key Vocabulary - Runtime Lookups

**Divine Names:**
- יהוה (YHWH) = "Yahweh" (never "LORD" or "the LORD")
- אֲדֹנָי (Adonai) = "Lord"
- אֵל / אֱלֹהִים (El/Elohim) = "God"

**Do NOT guess vocabulary translations. Always search authoritative sources:**

1. **First**: Check `data/issues_resolved.txt` for authoritative decisions
   ```bash
   grep -i "chesed\|חֶסֶד" data/issues_resolved.txt
   ```

2. **Second**: Check glossaries in `data/glossary/`
   - `hebrew_ot_glossary.csv` - main vocabulary with ULT/UST glosses
   - `psalms_reference.csv` - Psalms-specific terms
   - `sacrifice_terminology.csv` - sacrificial vocabulary
   - `biblical_measurements.csv` - measurements and units
   - `biblical_phrases.csv` - common constructions

3. **Third**: Search published ULT for parallel usage
   ```bash
   grep -r "covenant loyalty" data/published_ult_english/
   ```

#### C. Hebrew Idioms - Preserve Literally

ULT keeps Hebrew idioms in their literal form. Do not substitute English equivalents:

| Hebrew Idiom | Literal ULT | NOT |
|--------------|-------------|-----|
| אֶרֶךְ אַפַּיִם (erek appayim) | "long of nostrils" | "slow to anger" |
| לִפְנֵי (liphnei) | "to the face of" | "before" |
| בְּעֵינֵי (be'enei) | "in the eyes of" | "in the sight of" |
| בְּיַד (beyad) | "by the hand of" | "through" |
| מִפִּי (mippi) | "from the mouth of" | "from" |
| עַל־לֵב (al-lev) | "on the heart" | "in mind" |
| קְשֵׁה עֹרֶף (qesheh oref) | "hard of neck" | "stubborn" |
| חֲזַק לֵב (chazaq lev) | "strong of heart" | "courageous" |

Body-part idioms especially must stay literal - this is where Hebrew differs most from English and where translation notes will explain the meaning.

#### D. Verb Forms

| Hebrew Form | ULT Rendering |
|-------------|---------------|
| Wayyiqtol | Past tense with connector ("And he went") |
| Qatal (perfect) | Past or present perfect depending on context |
| Yiqtol (imperfect) | Future, habitual, or modal |
| Infinitive construct | "to [verb]" |
| Infinitive absolute | Show reduplication: "acquitting he will not acquit" (not "certainly") |
| Participle | Present tense; NO brackets for be-verb |
| Imperative | Command form |
| Jussive/Cohortative | "Let him/me..." or subjunctive |

### Step 4: Supply Words {in brackets}

Brackets mark words added for English grammar not present in Hebrew.

**USE brackets for:**
- Copulas when Hebrew has none: "Your God {is} my God"
- Implied verbs: "she had been {living} there"
- Genitive absolute constructions: "{while} they {were} eating"
- Implied subjects when needed for clarity: "{it was} good"

**DO NOT use brackets for:**
- Participles with be-verbs: "Yahweh is giving" (not "Yahweh {is} giving")
- Words within semantic range of Hebrew: "hill country" (not "hill {country}")
- Articles: "the man" (not "{the} man")

### Step 5: Apply Style Rules

Reference `reference/gl_guidelines.md` for detailed style guidance. Key points:

**Formality:**
- No contractions ("do not" not "don't")
- Use "whom" not "who" as object
- Subjunctive mood ("if he were" not "if he was")
- Formal register throughout

**Numbers:**
- 1-10: Spell out ("one", "five")
- 11+: Use numerals ("11", "150")
- Ranges: En-dash ("30-40 people")

**Punctuation:**
- Oxford comma ("red, white, and blue")
- American spelling ("color" not "colour")
- Single space between sentences
- Quotation marks at start/end of speech only

**Capitalization:**
- God pronouns: lowercase except sentence start
- Titles: capitalize ("Son of Man", "King David")
- "Scripture" capitalized for Bible; lowercase for passages

**Word Order:**
- Preserve Hebrew order where possible while maintaining grammatical English
- Wayyiqtol chains should show sequence

### Step 6: Format as USFM

```usfm
\id [BOOK] - unfoldingWord Literal Text
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
- `\q1` - first level poetry
- `\q2` - second level (indented)
- `\qa` - acrostic heading
- `\d` - superscription (Psalms)

**Section breaks:**
- `\ts\*` - chunk/section divider

### Step 7: Export to File

Save the completed ULT to `output/AI-ULT/` with the naming convention:

```
output/AI-ULT/[BOOK]-[CHAPTER].usfm
```

Examples:
- `output/AI-ULT/NAM-01.usfm` - Nahum chapter 1
- `output/AI-ULT/PSA-023.usfm` - Psalm 23
- `output/AI-ULT/GEN-01.usfm` - Genesis chapter 1

Use three-letter book codes and two-digit chapter numbers (zero-padded).

---

## Scripts Reference

### Parse aligned USFM to JSON
```bash
node .claude/skills/utilities/scripts/usfm/parse_usfm.js \
  data/published_ult/[BOOK].usfm \
  --chapter [N] \
  --output-json /tmp/alignments.json
```

### Quick vocabulary lookup
```bash
# Check authoritative decisions first
grep -i "[hebrew term]\|[english term]" data/issues_resolved.txt

# Then check glossary
grep "[term]" data/glossary/hebrew_ot_glossary.csv

# Find parallel usage in published ULT
grep -r "[phrase]" data/published_ult_english/
```

### Extract plain USFM from aligned
```bash
node .claude/skills/utilities/scripts/usfm/parse_usfm.js \
  data/published_ult/[BOOK].usfm \
  --plain-only > /tmp/plain.usfm
```

---

## Quality Checklist

Before finalizing ULT output, verify:

- [ ] Wayyiqtol verbs have appropriate connectors (And/Then/So)
- [ ] Hebrew idioms preserved literally (e.g., "long of nostrils" not "slow to anger")
- [ ] Prepositions kept literal (e.g., "to the face of" not "before")
- [ ] Infinitive absolute shown as reduplication (not adverbs like "certainly")
- [ ] {brackets} used correctly - only for grammar words not in Hebrew
- [ ] No contractions anywhere
- [ ] Hebrew word order preserved where grammatically possible
- [ ] USFM markers properly formatted
- [ ] Poetry uses \q1/\q2 appropriately
- [ ] Key vocabulary matches Issues Resolved decisions
- [ ] Numbers formatted correctly (1-10 spelled out)
- [ ] Formal register maintained throughout
- [ ] No split infinitives

---

## Data Sources (Runtime Lookups)

**Always check these at runtime - do not rely on memory:**

| Source | Path | Purpose |
|--------|------|---------|
| Issues Resolved | `data/issues_resolved.txt` | FINAL AUTHORITY - content team decisions |
| Hebrew Glossary | `data/glossary/hebrew_ot_glossary.csv` | Standard ULT/UST glosses |
| Psalms Reference | `data/glossary/psalms_reference.csv` | Psalms-specific vocabulary |
| Sacrifice Terms | `data/glossary/sacrifice_terminology.csv` | Sacrificial vocabulary |
| Measurements | `data/glossary/biblical_measurements.csv` | Units and measures |
| Phrases | `data/glossary/biblical_phrases.csv` | Common constructions |
| Published ULT | `data/published_ult_english/*.usfm` | Parallel patterns |
| Style Guide | `reference/gl_guidelines.md` | Detailed style rules |

---

## Related Skills

- [Pipeline Overview](../pipeline-overview/SKILL.md) - Where this fits in the workflow
- [Hebrew Reference](../hebrew-reference/SKILL.md) - Hebrew language patterns
- [Issue Identification](../issue-identification/SKILL.md) - Finding translation issues
