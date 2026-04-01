---
name: ULT-gen

description: Transform Hebrew USFM into unfoldingWord Literal Text (ULT), preserving the form and structure of the original Hebrew. Use when asked to translate Hebrew to ULT, generate literal text, or create ULT for a chapter.

allowed-tools: Read, Grep, Glob, mcp__workspace-tools__*
---

## MCP-First Execution

Run this skill with workspace MCP tools in restricted environments. Prefer:
- `mcp__workspace-tools__fetch_hebrew_bible`, `mcp__workspace-tools__fetch_ult`
- `mcp__workspace-tools__build_strongs_index`
- `mcp__workspace-tools__curly_quotes`
Use `Read`/`Grep` for file inspection and avoid shell/python command snippets.

## 7-Step Workflow

### Step 1: Parse Hebrew Input

Read Hebrew USFM from `data/hebrew_bible/*.usfm`. Extract verse text from `\w` tags with morphology (lemma, strong, x-morph).

For complex passages, use MCP workspace tools to fetch and inspect prior published renderings, then read the relevant USFM/alignment artifacts with `Read`.

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

1. **First**: Check `data/issues_resolved.txt` for authoritative decisions using `Grep`.

2. **Second**: Check quick-ref decisions using `Grep` on `data/quick-ref/ult_decisions.csv`.
   The file has a `Source` column: `human` entries (editor corrections, issues_resolved) are near-authoritative — treat them like issues_resolved. `AI` entries are precedent — use them unless context clearly warrants deviation.

3. **Third**: Look up the Strong's index for aggregated rendering data with `mcp__workspace-tools__build_strongs_index` (`lookup: "H4869"`).
   This returns all renderings with occurrence counts and sample refs from published ULT, without scanning 43MB of USFM. Use the dominant rendering unless context requires otherwise.

4. **Fourth**: Check project glossary for editorial overrides with `Grep` on `data/glossary/project_glossary.md`.
   Only add to project glossary when human review revealed a needed change from existing published patterns.

5. **Fifth**: Check other glossaries in `data/glossary/`
   - `hebrew_ot_glossary.csv` - main vocabulary with ULT/UST glosses
   - `psalms_reference.csv` - Psalms-specific terms
   - `sacrifice_terminology.csv` - sacrificial vocabulary
   - `biblical_measurements.csv` - measurements and units
   - `biblical_phrases.csv` - common constructions

6. **After resolving**: For words that required 2+ sources or had multiple possible renderings, record the decision with `mcp__workspace-tools__append_quickref` so future runs resolve faster:
   - `file`: `ult_decisions`
   - `strong`: the Strong's number (e.g. `H4869`)
   - `hebrew`: the Hebrew word
   - `rendering`: the English rendering chosen
   - `context`: brief context (e.g. `dominant rendering 85% of 20 occ`)
   - `notes`: rationale if non-obvious
   - `source`: `AI` (default) or `human` if recording an editor decision
   The tool deduplicates by Strong number and returns the existing entry if one is already recorded.

**Fallback**: If the index doesn't have an entry (e.g., unpublished books), search published files with `Grep` and inspect specific verses with `Read`.

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
Default to agent-noun forms when English has them:
- יִרְאֵי שְׁמֶךָ -> "the fearers of your name"
- יֹשְׁבֵי -> "the dwellers of"
- שֹׁרְרַי -> "my watchers" / "my enemies"

Use "the ones [verb]-ing" or "those [verb]-ing" only as a fallback when no natural English agent noun exists. Do not systematically expand agent nouns to full phrases -- editors will adjust case-by-case when context requires it (e.g., "callers" or "lovers" may need expansion to avoid wrong meaning).

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

**Superscription verse anchoring:**
Do not assume all psalm headings belong in `\d` before verse 1. Anchor placement to the Hebrew chapter structure:

1. **If Hebrew `\v 1` contains both superscription and body text** (e.g., Psalms 120-134 "song of ascents" + body), the superscription is part of verse 1. Output as:
   ```
   \d
   \v 1 A song of ascents
   \q1 Remember, Yahweh, for David,
   \q2 all of his afflictions,
   ```
   `\d` is an empty paragraph-style marker (tells renderers to style what follows as a superscription). `\v 1` contains just the superscription text. `\q1` starts the poetry body, still part of verse 1. Do NOT put text on the `\d` line, do NOT put `\d` after `\v 1`, and do NOT omit `\d`.

2. **If Hebrew has superscription words only in `\v 1`** (no body text until `\v 2`), with verse-offset markers (`\va`) showing English versification is shifted (Hebrew v2 = English v1), keep the superscription on `\d` with its text and start body at English `\v 1`:
   ```
   \d For the chief musician. A psalm. Of David.
   \v 1 [body text from Hebrew v2]
   ```

Quick check at chapter start:
- Read the first 5-10 lines after `\c N` in Hebrew.
- If `\v 1` has both superscription words AND body text: use format 1 (empty `\d`, superscription in `\v 1`).
- If `\v 1` has only superscription words and body starts at `\v 2`: use format 2 (`\d` with text, body at English `\v 1`).

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
- **Active verbs with no explicit subject where English passive would be the natural rendering**: supply the implied subject in brackets to preserve active voice. Use a contextually appropriate noun — `{people}`, `{enemies}`, `{he}`, etc. E.g., `{people} forgot` (Qal of שָׁכַח, LAM 2:6) rather than "is forgotten"; `let {him} be filled` → `let {him} fill {people}` if the Hebrew supports it. When the implied subject is genuinely unclear, passive with a note is acceptable, but bracket the subject wherever context makes it identifiable.

**Pattern**: When "my [noun]" in Hebrew becomes "of [noun] to me" for literalness:
- צַר־לִי -> "trouble to me" (not "my distress")

**Prefer fewer implied words**: When Hebrew uses a preposition + infinitive construct (e.g., min + infinitive), render it with the Hebrew preposition rather than restructuring into an English purpose/result clause with added implied words. Preserve Hebrew word order when the meaning is clear in English.

**DO NOT use brackets for:**
- **Participles with be-verbs are NEVER bracketed**: "Yahweh is giving" (not "Yahweh {is} giving"), "he was walking" (not "he {was} walking"), "they are dwelling" (not "they {are} dwelling"). The auxiliary verb is required English grammar for participle constructions.
- Words within semantic range of Hebrew: "hill country" (not "hill {country}")
- **Articles are NEVER bracketed**: "the head" (not "{the} head"), "the land" (not "{the} land"). The definite article never needs brackets regardless of whether Hebrew has an explicit article.

### Prophetic Speech Formulas

The phrase נְאֻם יְהוָה (neum Yahweh, "the declaration of Yahweh") and its expanded form נְאֻם יְהוָה צְבָאוֹת ("the declaration of Yahweh of Armies") appear as parenthetical attributions within prophetic speech. Format them with em-dashes and no supplied {is}:

- Correct: `"And I will rise up against them"—the declaration of Yahweh of Armies—"and I will cut off..."`
- Wrong: `"And I will rise up against them," {is} the declaration of Yahweh of Armies, "and I will cut off..."`

Rules:
- Use em-dashes (—) on both sides when the attribution interrupts quoted speech
- Use a single em-dash when it ends a quoted section: `"...the broom of destruction"—the declaration of Yahweh of Armies.`
- Do not add {is} -- the Hebrew has no copula here and the phrase is a parenthetical attribution, not a predicate
- Do not add commas around the phrase; the em-dashes serve as the delimiter

### Step 5: Apply Style Rules

Apply all shared style rules from `../reference/gl_guidelines.md` (formality, numbers, punctuation, capitalization, spelling). ULT-specific rules below:

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

\q1 [poetry line 1]
\q2 [poetry line 2 - indented]

\f + \fq quoted text \ft explanation\f*
```

**Poetry markers:**
- `\q1` - first colon of a verse (the "A" line)
- `\q2` - second/third colon of a verse (the "B" or "C" line in parallel structure)
- `\qa` - acrostic heading
- `\d` - superscription (Psalms, only when Hebrew treats it as standalone heading)
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

### Step 7: Export to File

Save the completed ULT to `output/AI-ULT/` with the naming convention:

```
output/AI-ULT/[BOOK]/[BOOK]-[CHAPTER].usfm
```

Examples:
- `output/AI-ULT/NAM/NAM-01.usfm` - Nahum chapter 1
- `output/AI-ULT/PSA/PSA-023.usfm` - Psalm 23
- `output/AI-ULT/GEN/GEN-01.usfm` - Genesis chapter 1

Use three-letter book codes and two-digit chapter numbers (zero-padded).

### Step 8: Convert to Curly Quotes

Run `mcp__workspace-tools__curly_quotes` with `inPlace: true` for `output/AI-ULT/[BOOK]/[BOOK]-[CHAPTER].usfm`.

This converts:
- Straight double quotes `"..."` to curly `"..."`
- Straight single quotes/apostrophes `'...'` to curly `'...'`

---

## Tools Reference

All lookups use MCP tools or built-in `Read`/`Grep` (no Bash needed).

| Task | Tool | Example |
|------|------|---------|
| Strong's lookup | `mcp__workspace-tools__build_strongs_index` | `lookup: "H4869"` |
| Hebrew source | `mcp__workspace-tools__fetch_hebrew_bible` | `books: ["LAM"]` |
| Published ULT | `mcp__workspace-tools__fetch_ult` | `books: ["LAM"]` |
| Glossary files | `mcp__workspace-tools__fetch_glossary` | (fetches all 5 CSVs) |
| Authoritative decisions | `Grep` on `data/issues_resolved.txt` | pattern: `"H4869"` |
| Prior ULT decisions | `Grep` on `data/quick-ref/ult_decisions.csv` | pattern: `"H4869"` |
| Project glossary | `Grep` on `data/glossary/project_glossary.md` | pattern: `"term"` |
| Standard glossaries | `Grep` on `data/glossary/*.csv` | pattern: `"term"` |
| Published ULT text | `Grep` on `data/published_ult_english/*.usfm` | pattern: `"stronghold"` |
| Aligned USFM parse | `mcp__workspace-tools__create_aligned_usfm` | (for alignment data) |
| Plain USFM extract | `mcp__workspace-tools__extract_ult_english` | (strips alignment markup) |
| Curly quotes | `mcp__workspace-tools__curly_quotes` | (post-processing) |
| Record decision | `mcp__workspace-tools__append_quickref` | `file: "ult_decisions", strong: "H4869"` |

### Verify consistency before output
For key terms appearing multiple times, use `Grep` on `data/published_ult/*.usfm` with the Strong's number pattern (e.g. `strong="H2617"`) to check 3-5 published occurrences.

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
- [ ] Substantive participles default to agent-noun form ("fearers"); expansion is editor discretion
- [ ] Large numbers use numerals with commas (12,000)
- [ ] Vocabulary scripts were run for key terms
- [ ] Psalm superscriptions use "chief musician" and periods between elements
- [ ] Superscription placement matches Hebrew anchoring (`\v 1`-embedded vs standalone `\d`)
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
| Quick-Ref Decisions | `data/quick-ref/ult_decisions.csv` | Prior ULT-gen vocabulary decisions |
| Strong's Index | `data/cache/strongs_index.json` | Aggregated Strong's -> rendering map |
| Published ULT | `data/published_ult_english/*.usfm` | Parallel patterns |
| Style Guide | `../reference/gl_guidelines.md` | Detailed style rules |

---

## Related Skills

- [Pipeline Overview](../pipeline-overview/SKILL.md) - Where this fits in the workflow
- [Hebrew Reference](../hebrew-reference/SKILL.md) - Hebrew language patterns
- [Issue Identification](../issue-identification/SKILL.md) - Finding translation issues
