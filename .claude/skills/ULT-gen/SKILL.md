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

**Collective/Generic nouns:**
- אֱנוֹשׁ (enosh) = "man" (singular, generic) - not "men"
- אָדָם (adam) = "man/Adam" depending on context

**Do NOT guess vocabulary translations. You MUST run the lookup scripts below for every non-trivial word. Tokens are cheap, mistakes are expensive. If you skip lookups, the output will diverge from human ULT.**

1. **First**: Check `data/issues_resolved.txt` for authoritative decisions
   ```bash
   grep -i "chesed\|חֶסֶד" data/issues_resolved.txt
   ```

2. **Second**: Search published ULT for how this exact word was rendered

   Use Proskomma to find every occurrence of a Strong's number:
   ```bash
   # Find all renderings of a Hebrew word by Strong's number
   node .claude/skills/utilities/scripts/proskomma/query_word.js H4869 --format table
   ```

   Or grep the aligned USFM for the Strong's number:
   ```bash
   grep -r "strong=\"H4869\"" data/published_ult/*.usfm | head -20
   ```

   Then extract how it was translated in context:
   ```bash
   # Parse a sample verse to see the English rendering
   node .claude/skills/utilities/scripts/usfm/parse_usfm.js \
     data/published_ult/19-PSA.usfm --verse "PSA 9:9" --output-json /tmp/sample.json
   ```

3. **Third**: Check project glossary for editorial overrides
   ```bash
   grep -i "[term]" data/glossary/project_glossary.md
   ```
   Only add to project glossary when human review revealed a needed change from existing published patterns.

4. **Fourth**: Check other glossaries in `data/glossary/`
   - `hebrew_ot_glossary.csv` - main vocabulary with ULT/UST glosses
   - `psalms_reference.csv` - Psalms-specific terms
   - `sacrifice_terminology.csv` - sacrificial vocabulary
   - `biblical_measurements.csv` - measurements and units
   - `biblical_phrases.csv` - common constructions

**Search multiple times if needed.** For any word that appears more than once in a chapter, verify consistency by checking 3-5 published occurrences before settling on a rendering.

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

#### D. Literalness Patterns

Consult `reference/literalness_patterns.md` for these patterns:
- **Hiphil causatives**: Use "made [verb]" ("made see" not "showed")
- **Construct chains**: Keep "X of Y" ("city of fortification")
- **Verbal idioms**: Preserve noun ("do valor" not "do valiantly")

#### E. Verb Forms

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

**Preserve verb form distinctions in parallel structures:**
When a participle and perfect appear in parallel, do not conform them:
- "the one putting our soul among the living, and he does not allow our foot to slip" (participle + perfect)
- NOT: "placing...and not giving" (both as participles)

#### Cohortative Recognition

Hebrew cohortatives (1cs/1cp with ה- ending or lengthened form) express desire or resolve. Render as "Let me/us...":
- אֶשְׁמֹרָה -> "Let me wait" (not "I will watch")
- אֲזַמֵּרָה -> "Let me make music" (not "I will make music")

#### Participle Handling

Participles should use "-ing" forms to preserve their verbal noun quality:
- הַמִּתְקוֹמְמַי -> "the ones rising up against me" (not "who rise up")
- מֹשֵׁל -> "is ruling" (not "rules")
- שֹׁמֵעַ -> "Who is hearing?" (not "Who hears?")

**Substantive participles:**
- לִירֵאֶיךָ -> "to the ones fearing you" (not "to those who fear you")

Use "the ones [verb]-ing" for participles functioning as nouns.

**However**, prefer noun-like forms when available:
- יִרְאֵי שְׁמֶךָ -> "the fearers of your name" (not "the ones fearing your name")

Per psalms_reference.csv: Nominal adjectives like "the righteous," "the wicked," "the poor" do NOT need {ones}. Only add {ones} for participles when truly needed for grammar.

#### F. Psalm Superscriptions

| Hebrew | ULT Rendering |
|--------|---------------|
| לַמְנַצֵּחַ | "For the chief musician" (not "music director") |
| עַל־נְגִינַת | "On a stringed instrument" (singular) |
| לְדָוִד | "Of David" |
| מִזְמוֹר | "A psalm" |
| מַשְׂכִּיל | "A maskil" |
| מִכְתָּם | "A miktam" |
| שִׁיר | "A song" |

Separate superscription elements with periods, not commas:
- "For the chief musician. On a stringed instrument. Of David."

#### G. Comparatives with מִן

| Hebrew Pattern | ULT | NOT |
|----------------|-----|-----|
| יָרוּם מִמֶּנִּי | "higher than I" | "high away from me" |
| גָּדוֹל מִמֶּנִּי | "greater than I" | "great from me" |
| X + מִן comparative | "X-er than Y" | "X away from Y" |

#### H. Context-Dependent Verbs

| Hebrew | Context | ULT | NOT |
|--------|---------|-----|-----|
| יָשַׁב | permanent dwelling | "dwell" | "sit" |
| יָשַׁב | temporary/literal | "sit" | - |
| נָצַר | watch over/protect | "preserve" | "guard" |
| שָׁלַם (Piel) | vows/debts | "pay" | "fulfill" |
| שָׁמַע + לְ | listen to | "listen to" | "hear" |

#### I. Connector Words

| Hebrew | ULT |
|--------|-----|
| כֵּן (adverbial) | "Thus" (not "So") |

#### J. Emphatic Doubling

Preserve Hebrew doubling without adding words:
- יוֹם יוֹם -> "day, day" (not "day {by} day")

### Step 4: Supply Words {in brackets}

Brackets mark words added for English grammar not present in Hebrew.

**USE brackets for:**
- Copulas when Hebrew has none: "Your God {is} my God"
- Implied verbs: "she had been {living} there"
- Genitive absolute constructions: "{while} they {were} eating"
- Implied subjects when needed for clarity: "{it was} good"
- Implied prepositions with verbs: "sing {about} your strength" (when Hebrew has no prep)
- Implied prepositions in negation: "not {for} my transgression"
- Purpose clause markers: "that they {may} not {be}"
- Implied objects: "{to} any treacherous workers"

**Pattern**: When "my [noun]" in Hebrew becomes "of [noun] to me" for literalness:
- צַר־לִי -> "trouble to me" (not "my distress")

**DO NOT use brackets for:**
- Participles with be-verbs: "Yahweh is giving" (not "Yahweh {is} giving")
- Words within semantic range of Hebrew: "hill country" (not "hill {country}")
- Articles: "the man" (not "{the} man")
- Definite articles when Hebrew has them (even implied in construct): "the enemy" not "{the} enemy"
- "the king" when מֶלֶךְ has article or is definite by context

### Step 5: Apply Style Rules

Reference `reference/gl_guidelines.md` for detailed style guidance. Key points:

**Formality:**
- No contractions ("do not" not "don't")
- Use "whom" not "who" as object
- Subjunctive mood ("if he were" not "if he was")
- Formal register throughout

**Numbers:**
- 1-10: Spell out ("one", "five")
- 11+: Use numerals with commas ("12,000")
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
- Use English standard SVO order; do not woodenly follow Hebrew word order
- Prepositional phrases fronted in Hebrew (temporal, locative, source, indirect object, etc.) should go in their natural English position unless the fronting serves a clear discourse function (focus, contrast, topic shift)
- Wayyiqtol chains should show sequence

**Emphatic Pronouns:**
When Hebrew repeats a pronoun for emphasis, preserve it:
- וַאֲנִי אָשִׁיר -> "But I, I will sing"
- הֵמָּה יְנִיעוּן -> "They, they wander"
- וְהוּא יָבוּס -> "he, he will trample" (comma separates emphatic pronoun)

**Vocative Position:**
Hebrew vocatives at clause end should stay there:
- מָגִנֵּנוּ אֲדֹנָי -> "Lord our shield" (not "our shield, Lord")

**Preposition Precision:**

| Hebrew | Context | ULT | Not |
|--------|---------|-----|-----|
| מִן + שָׂגַב | separation | "away from" | "from" |
| עַל | governing | "over" | "on" |
| לְ + infinitive | purpose | "to [verb]" | - |

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
- `\q1` - first colon of a verse (the "A" line)
- `\q2` - second/third colon of a verse (the "B" or "C" line in parallel structure)
- `\qa` - acrostic heading
- `\d` - superscription (Psalms)
- `\qs Selah \qs*` - Selah marker on its own line after the verse's poetry lines (note the space after "Selah" before `\qs*`)

**Poetry indentation pattern:**
Hebrew poetry uses parallelism. Use `\q1` for the first line of each verse, then `\q2` for continuation lines:

```usfm
\q1 \v 3 Because your covenant faithfulness {is} better than life,
\q2 my lips will praise you.
```

For tricola (three-part verses), use `\q1` + `\q2` + `\q2`:

```usfm
\q1 \v 11 But the king will rejoice in God;
\q2 everyone who swears by him will exult,
\q2 for the mouth of the speakers of lies will be shut.
```

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

### Step 8: Convert to Curly Quotes

Run the curly quotes script to convert straight quotes to curly quotes:

```bash
python3 .claude/skills/utilities/scripts/curly_quotes.py \
  output/AI-ULT/[BOOK]-[CHAPTER].usfm --in-place
```

This converts:
- Straight double quotes `"..."` to curly `"..."`
- Straight single quotes/apostrophes `'...'` to curly `'...'`

---

## Scripts Reference

### Parse aligned USFM to JSON
```bash
node .claude/skills/utilities/scripts/usfm/parse_usfm.js \
  data/published_ult/[BOOK].usfm \
  --chapter [N] \
  --output-json /tmp/alignments.json
```

### Vocabulary lookup (search aggressively)
```bash
# 1. Check authoritative decisions
grep -i "[hebrew term]\|[english term]" data/issues_resolved.txt

# 2. Find all occurrences of a Hebrew word by Strong's number
node .claude/skills/utilities/scripts/proskomma/query_word.js H4869 --format table

# 3. Or grep aligned USFM for Strong's number
grep -r "strong=\"H4869\"" data/published_ult/*.usfm | head -20

# 4. Parse specific verse to see full alignment
node .claude/skills/utilities/scripts/usfm/parse_usfm.js \
  data/published_ult/19-PSA.usfm --verse "PSA 18:2" --output-json /tmp/sample.json

# 5. Search plain English text for phrases
grep -r "stronghold" data/published_ult_english/*.usfm | head -10

# 6. Check project glossary for editorial overrides
grep -i "[term]" data/glossary/project_glossary.md

# 7. Check standard glossaries
grep "[term]" data/glossary/hebrew_ot_glossary.csv
```

### Verify consistency before output
For key terms appearing multiple times, check 3-5 published occurrences:
```bash
# Find all verses with a term
grep -r "strong=\"H2617\"" data/published_ult/*.usfm | wc -l  # count occurrences
grep -r "strong=\"H2617\"" data/published_ult/*.usfm | shuf | head -5  # random sample
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
- [ ] USFM markers properly formatted
- [ ] Poetry uses \q1/\q2 appropriately
- [ ] Key vocabulary matches Issues Resolved decisions
- [ ] Numbers formatted correctly (1-10 spelled out)
- [ ] Formal register maintained throughout
- [ ] No split infinitives
- [ ] Cohortatives rendered as "Let me/us..."
- [ ] Participles use "-ing" forms consistently
- [ ] Emphatic pronouns preserved ("I, I will...")
- [ ] Vocative word order preserved
- [ ] Project glossary checked for editorial decisions
- [ ] Prepositions marked with brackets when implied
- [ ] Literalness patterns applied (see reference/literalness_patterns.md)
- [ ] Substantive participles use noun-like form when available ("fearers" not "the ones fearing")
- [ ] Large numbers use numerals with commas (12,000)
- [ ] Vocabulary scripts were run for key terms
- [ ] Psalm superscriptions use "chief musician" and periods between elements
- [ ] Comparatives with מִן use "-er than" form ("higher than I")
- [ ] Selah uses `\qs Selah \qs*` format on its own line (space after Selah before closing tag)
- [ ] Emphatic doubling preserved without adding words ("day, day" not "day {by} day")

---

## Data Sources (Runtime Lookups)

**Always check these at runtime - do not rely on memory:**

| Source | Path | Purpose |
|--------|------|---------|
| Issues Resolved | `data/issues_resolved.txt` | FINAL AUTHORITY - content team decisions |
| Project Glossary | `data/glossary/project_glossary.md` | Editorial decisions from human review |
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
