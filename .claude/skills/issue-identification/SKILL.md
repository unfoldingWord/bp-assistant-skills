---
name: issue-identification
description: Find translation issues in ULT/Hebrew/Greek texts. Use when analyzing passages for figures of speech, abstract nouns, or other translation concerns.
allowed-tools: Read, Grep, Glob, Bash
---

# Issue Identification

## Purpose
Identify translation issues in biblical text that require translation notes. This skill focuses on **recognition and classification** - note writing is handled separately.

## Arguments

When invoked with arguments like `2sam 1` or `psa 58 local`:
- First argument: Book abbreviation (2sa, gen, psa, 1jn, etc.)
- Second argument: Chapter number (optional, defaults to all)
- Third argument: Source mode (optional) - `local` or `fetch` (default: `fetch`)
- If no arguments: Expect text to be provided or prompt for book/chapter

**Source modes:**
- `fetch` (default): Grab editor-approved ULT/UST from unfoldingWord master
- `local`: Look for local files in `data/published_ult/` and `data/published_ust/`

Examples:
```
/issue-identification psa 58           # Fetch from master (default)
/issue-identification psa 58 fetch     # Same as above, explicit
/issue-identification psa 58 local     # Use local files
```

Book abbreviations follow standard 3-letter codes or common variants:
- 2sam, 2sa -> 2SA (Second Samuel)
- gen -> GEN
- psa, ps -> PSA
- 1jn -> 1JN

## Workflow

There are two ways to use this skill:
1. **Full workflow** - Fetch aligned USFM, parse with proskomma, run detection with morphology data
2. **Quick workflow** - Just provide English text directly, run detection without source language checks

### Option A: Full Workflow (with aligned USFM)

#### Step 1: Fetch/Locate USFM Text

**Fetch mode (default)** - Get from unfoldingWord master:
```bash
# Fetch ULT
python3 .claude/skills/utilities/scripts/fetch_door43.py <BOOK> > /tmp/book_ult.usfm
# Fetch UST (may not exist for all books - continue if fails)
python3 .claude/skills/utilities/scripts/fetch_door43.py <BOOK> --type ust > /tmp/book_ust.usfm 2>/dev/null || true
```

**Local mode** - Use local files:
```bash
# Copy local files (NN is book number, e.g., 19 for PSA)
cp data/published_ult/<NN>-<BOOK>.usfm /tmp/book_ult.usfm
cp data/published_ust/<NN>-<BOOK>.usfm /tmp/book_ust.usfm 2>/dev/null || true
```

If UST is missing, continue without it (first pass, UST not generated yet).
If ULT is missing, error (need at least ULT to identify issues).

#### Step 2: Parse into Alignment JSON and Plain Text
Extract alignment data and plain text using usfm-js:

```bash
# Parse ULT - get alignments and plain text
node .claude/skills/utilities/scripts/usfm/parse_usfm.js /tmp/book_ult.usfm \
  --chapter <N> \
  --output-json /tmp/alignments.json \
  --output-plain /tmp/ult_plain.usfm

# Parse UST - get plain text only (if UST exists)
node .claude/skills/utilities/scripts/usfm/parse_usfm.js /tmp/book_ust.usfm \
  --plain-only > /tmp/ust_plain.usfm 2>/dev/null || true
```

#### Step 3: Compare ULT/UST (if UST available)
Where UST diverges from ULT (beyond synonym/clarity changes), there may be a translation issue:

```bash
python3 .claude/skills/issue-identification/scripts/compare_ult_ust.py \
  /tmp/ult_plain.usfm /tmp/ust_plain.usfm \
  --chapter <N> --output /tmp/ult_ust_diff.tsv
```

Output shows verses where UST made significant changes, with suggested issue types:
| Pattern | Suggested Issue |
|---------|----------------|
| UST adds clarifying words | figs-explicit |
| UST removes repetition | figs-doublet, figs-parallelism |
| UST restructures clause order | figs-infostructure |
| UST replaces figurative language | figs-metaphor |
| UST unpacks abstract noun | figs-abstractnouns |
| UST changes passive to active | figs-activepassive |
| UST expands/explains phrase | figs-idiom |

Skip this step if UST file doesn't exist.

#### Step 4: Run Automated Detection Scripts
These scripts identify issues that should appear in output.

Every passive construction needs a note. Every abstract noun should be evaluated.

```bash
# Passive voice - every passive needs a note
python3 .claude/skills/issue-identification/scripts/detection/detect_activepassive.py \
  /tmp/alignments.json --format tsv >> /tmp/detected_issues.tsv

# Abstract nouns - evaluate each for note necessity
python3 .claude/skills/issue-identification/scripts/detection/detect_abstract_nouns.py \
  /tmp/alignments.json --format tsv >> /tmp/detected_issues.tsv
```

Merge detected issues into final output.

### Option B: Quick Workflow (plain English text)

When you just have English text (no USFM, no alignments), use `--text` to run detection directly. This skips source language morphology checks but still finds passives and abstract nouns.

```bash
# Passive voice detection on plain English
python3 .claude/skills/issue-identification/scripts/detection/detect_activepassive.py \
  --text "The bread was broken and given to them" --format tsv

# Abstract noun detection on plain English
python3 .claude/skills/issue-identification/scripts/detection/detect_abstract_nouns.py \
  --text "The righteousness of God brings salvation" --format tsv
```

Output uses "text" as the reference since there's no verse structure. Source language fields (morph, lemma) will be empty.

### Step 5: Check Names/Unknowns Against Translation Words

**IMPORTANT**: Before flagging any name or unknown concept for translate-names or translate-unknown, check if it has a tW article. If a tW article exists, generally NO note is needed.

```bash
# Check a single term
python3 .claude/skills/issue-identification/scripts/check_tw_headwords.py "Abimelech"

# Check multiple terms at once
python3 .claude/skills/issue-identification/scripts/check_tw_headwords.py "Yahweh" "bread" "Persia"

# Check terms from stdin (for batch processing)
echo -e "Jordan\nCyrus\nmyrrh" | python3 .claude/skills/issue-identification/scripts/check_tw_headwords.py --stdin
```

The script returns JSON with `matches` (have tW articles) and `no_match` (may need notes):
- **matches in "names" category**: NO translate-names note needed (tW covers it)
- **matches in "kt" or "other" category**: NO translate-unknown note needed (tW covers it)
- **no_match**: Likely needs translate-names or translate-unknown note

**Exception**: If a term with a tW article is used FIGURATIVELY, use the appropriate figurative note (figs-metaphor, figs-metonymy, etc.) instead of translate-names/translate-unknown.

### Step 6: Manual Analysis - Four-Pass Workflow

After running detection scripts, analyze the text systematically using this four-pass approach. This ensures thorough coverage while managing cognitive load.

#### Pass 0: Review ULT/UST Differences (if UST available)
If Step 3 produced `/tmp/ult_ust_diff.tsv`, review it first to prime your attention on verses where UST diverged:

1. Read each row noting the `diff_type` and `suggested_issue`
2. Mark divergent verses for closer inspection in later passes
3. Note patterns - if UST consistently adds words, there may be implicit information throughout

This gives you a head start on where translation issues likely exist.

#### Pass 1: Chapter Overview
Read through the entire chapter to understand the big picture:

- **Structural elements**: Note discourse markers (and it came to pass, behold, therefore), participant introductions, quotation blocks
- **Segment boundaries**: Identify natural paragraph or pericope breaks
- **Unusual constructions**: Flag any phrases that seem distinctive or potentially challenging
- **Genre indicators**: Note poetry sections, dialogue patterns, narrative vs. instruction

For any unusual phrases noticed, do a quick search:
```bash
grep -i "phrase or key words" data/published-tns/tn_*.tsv | head -10
```

#### Pass 2: Segment-Level Grammar Focus
For each paragraph or segment identified in Pass 1:

- **Connectors**: Focus on grammar-connect issues - how do clauses relate? (time, logic, condition)
- **Discourse markers**: Check writing-* markers (newevent, background, participants, endofstory)
- **Quotation structure**: Note quote margins, nested quotes, indirect speech
- **Pronoun chains**: Track who "he/they/you" refer to through the segment

When uncertain about a construction:
```bash
grep -i "key phrase from segment" data/published-tns/tn_*.tsv
```

#### Pass 3: Verse-by-Verse Analysis with Task Checklist

For each verse (or small verse group), systematically check all issue types using the TaskCreate tool.

**Creating the checklist:**
Use TaskCreate to generate one task per issue type from `data/translation-issues.csv` (all ~93 types). Example: "Check figs-metaphor in v.3", "Check figs-simile in v.3", etc.

**Working through the checklist:**
1. Read the verse carefully
2. For each task, consider whether that issue type applies
3. Use TaskUpdate to mark completed with findings: `"figs-metaphor: 'shield' as protection - yes"` or `"figs-metaphor: none"`
4. When uncertain, search published notes before deciding

**Integrating detection script output:**
- Check detection script output first - passives and abstract nouns are pre-identified
- Mark those tasks as completed with the script findings
- For names/unknowns, run `check_tw_headwords.py` before flagging

### Systematic Review Principles

1. **Detection scripts first** - integrate passives and abstract nouns from scripts
2. **tW check for names** - run `check_tw_headwords.py` before flagging translate-names/translate-unknown
3. **Search when uncertain** - check `data/published-tns/` for similar phrases
4. **Consult Issues Resolved** - when classifications conflict, `data/issues_resolved.txt` has final authority
5. **Check implicit info** - would modern readers miss cultural practices, theological concepts, or covenant language?

The goal is coverage: it's easier for reviewers to delete a suggested issue than to identify one from scratch. When in doubt, include it.

### Genre-Specific Checks

**For Psalms/Prayers**: Make an extra pass for:
- **figs-imperative**: Imperatives addressed to God are requests, not commands
- **figs-explicit**: Covenant concepts (hesed, name, way) may need explanation
- **figs-parallelism vs figs-doublet**: If synonymous expressions fall on different poetic lines, classify as parallelism not doublet. For 3-line parallel verses, one parallelism note covers all lines. Quote the full parallel lines, not just key words.
- **figs-ellipsis with parallelism**: Check parallel lines for omitted words, but skip if ULT already supplies them in `{}`.

**For Proverbs**: Check:
- **figs-imperative**: Imperative + result = conditional ("Do X, and Y" = "If X, then Y")

### Grammar-Connect Context Guidelines

When identifying grammar-connect issues, capture sufficient context:

**Too Narrow (Avoid):**
- "for...for" - unclear what relationship is
- "because" alone - missing the clauses

**Appropriate Context:**
- "Please stand over me and kill me, for agony has seized me, for my life is still whole in me"
- "Your blood is on your head, for your mouth answered against you"

Rule: Include enough text that a reader can see the logical relationship being identified.

### Quotations
Make an extra pass looking for quotation marks, quotes-in-quotes, and indirect quotations that should be marked.

## Verification and Quality Checks

After completing issue identification, run these verification steps to catch misclassifications.

### Keyword Triggers

When you encounter these words, ALWAYS check the specific issue listed:

| Keyword | Always Check |
|---------|--------------|
| man, men, brothers, sons, fathers | figs-gendernotations (generic masculine?) |
| like, as, than | figs-simile before figs-metaphor |
| hand, hands, eyes, heart, face | figs-metonymy or figs-synecdoche (body part for action/person?) |
| all, every, never, always | figs-hyperbole (exaggeration for emphasis?) |
| the righteous, the wicked, the poor | figs-nominaladj (adjective as noun?) |

### Commonly Confused Issue Pairs

Before finalizing a tag, check if a related issue fits better:

| If considering... | Also check... | Key distinction |
|-------------------|---------------|-----------------|
| writing-pronouns | figs-gendernotations | Unclear referent vs. generic masculine |
| figs-metaphor | figs-simile | No comparison word vs. explicit "like/as" |
| figs-metonymy | figs-synecdoche | Associated thing vs. part/whole relationship |
| figs-doublet | figs-parallelism | Word-level pair vs. clause-level repetition |
| figs-doublet | figs-hendiadys | Synonyms for emphasis vs. one modifies other |
| figs-idiom | figs-metaphor | Fixed expression vs. live comparison |
| figs-hyperbole | figs-merism | General exaggeration vs. two extremes = whole |
| figs-rquestion | figs-exclamations | Question form vs. exclamation form |
| figs-explicit | figs-ellipsis | Adding background info vs. supplying omitted words |
| grammar-connect-logic-goal | grammar-connect-logic-result | Intended outcome vs. unintended consequence |

### Final Review Pass

After completing all identification, review your output:

1. **Tag verification**: For each issue tagged, can you point to specific criteria in the skill definition it meets? If unsure, re-read the skill file.

2. **Duplicate check**: Did you tag the same phrase twice for issues that are really one? (e.g., tagging both figs-doublet and figs-parallelism for the same word pair)

3. **Missing overlap check**: Are there phrases that genuinely need two tags? (e.g., a simile that also contains an abstract noun - both figs-simile AND figs-abstractnouns may apply)

4. **Keyword sweep**: Scan output for any keyword triggers above that you may have tagged incorrectly.

## Authoritative Sources

### Final Authority: Issues Resolved
Consult `data/issues_resolved.txt` before finalizing issue classifications.
This document contains content team decisions that override other guidance.

```bash
# Search for relevant decisions
cat data/issues_resolved.txt | grep -i "[search term]"
```

### Reference Examples: Published Notes
Search `data/published-tns/` for similar examples before classifying uncertain issues:

```bash
# Search for issue type patterns
grep -i "figs-metonymy" data/published-tns/tn_1SA.tsv | head -20
grep -i "fallen\|sword" data/published-tns/tn_*.tsv
```

## Available Scripts

| Script | Location | Purpose |
|--------|----------|---------|
| fetch_door43.py | utilities/scripts/ | Fetch USFM from Door43 (supports `--type ust` for UST) |
| parse_usfm.js | utilities/scripts/usfm/ | Parse USFM, extract alignments and plain text (usfm-js) |
| compare_ult_ust.py | scripts/ | Compare ULT/UST plain text to identify divergences suggesting issues |
| detect_activepassive.py | scripts/detection/ | Find ALL passive constructions. Use `--text "..."` for plain English |
| detect_abstract_nouns.py | scripts/detection/ | Find abstract nouns (591 word list). Use `--text "..."` for plain English |
| check_tw_headwords.py | scripts/ | Check names/unknowns against tW headwords - filters translate-names/translate-unknown |

### Ambiguity Detection (Cross-Cutting Check)

During verse-by-verse analysis, watch for passages where meaning is genuinely unclear:

**Pronoun Reference Ambiguity** (tag: `writing-pronouns`)
- Multiple possible antecedents for he/she/it/they
- Possessive pronouns with unclear referent
- "This/that" pointing to multiple possibilities

**Lexical Polysemy** (tag: `figs-explicit` or existing figure type)
- Words with established multiple meanings:
  - "world" (kosmos) - earth, people, value system
  - "love" (agape) - God's love, human love, both
  - "know" - cognitive, relational, experiential
- Hebrew words spanning multiple semantic domains

**Idiomatic Uncertainty** (tag: `figs-idiom`)
- Fixed expressions where meaning is disputed among scholars
- Cultural phrases with uncertain referent

**Ellipsis with Multiple Resolutions** (tag: `figs-ellipsis` or `figs-explicit`)
- Missing subjects/objects fillable multiple ways
- Implied information with more than one valid interpretation

**Detection signals:**
- English versions differ significantly on translation
- Commentaries acknowledge uncertainty ("interpreters disagree")
- The natural note format would be "This could mean: (1)... (2)..."

**Explanation field format for TCM notes:**
When flagging ambiguity that requires a "this could mean" note, use `TCM` keyword plus `i:` prefix with numbered options:

Format: `TCM i:(1) [option A] (2) [option B]`

Examples:
```
job	9:35	figs-idiom	I am not so with myself			TCM i:(1) I do not consider myself guilty (2) I am not in my right mind from fear
job	9:3	writing-pronouns	he wished to contend			TCM i:(1) God (2) a person who wanted to contend with God
1jn	4:3	figs-explicit	is not from God			TCM i:(1) sent by God (2) having God as its source
```

The `TCM` trigger tells the note writer to format using "This could mean (1)... or (2)..." structure while still using the issue type's template for context.

**Web search as fallback:**
When internal resources (Issues Resolved, published TNs, Translation Academy) don't clarify a potentially ambiguous passage:
1. Search: `"[book] [chapter]:[verse] interpretation"` or `"[Greek/Hebrew term] meaning"`
2. Look for scholarly disagreement as confirmation of genuine ambiguity
3. If sources differ, include a "this could mean" note with options found

**Fallback tag:** When ambiguity doesn't fit existing categories, use `figs-explicit` with note explaining the interpretive options.

See `reference/ambiguity_patterns.md` for detailed examples from published notes.

## Output Format

After identifying issues, output a tab-separated file to `output/issues/`:

```
output/issues/[BOOK]-[CHAPTER].tsv
```

Examples:
- `output/issues/PSA-063.tsv` - Psalm 63
- `output/issues/GEN-01.tsv` - Genesis 1
- `output/issues/2SA-01.tsv` - 2 Samuel 1

Use three-letter book codes and three-digit chapter numbers (zero-padded).

Format:

```
[book]\t[chapter:verse]\t[supportreference]\t[ULT text]\t\t\t[explanation if needed]
```

| Column | Description |
|--------|-------------|
| book | 3-letter abbreviation (psa, gen, mat, etc.) |
| chapter:verse | Reference (78:17) |
| supportreference | Issue type (figs-metaphor, writing-pronouns, etc.) |
| ULT text | English phrase where issue occurs |
| (empty) | Reserved |
| (empty) | Reserved |
| explanation | Brief note if issue not obvious from text (optional) |

Example:
```
psa	78:17	writing-pronouns	And they added			ancestors/israelites
psa	78:19	figs-rquestion	Is God able			rhetorical - asserting doubt
gen	1:5	figs-infostructure	evening and morning			time phrase order
```

## Available Issue Types

### A. Discourse Structure

#### Narrative Markers
| Issue | Description |
|-------|-------------|
| [writing-newevent](writing-newevent.md) | Phrases introducing new events/episodes |
| [writing-background](writing-background.md) | General background info - setting, character details, explanations |
| [writing-endofstory](writing-endofstory.md) | Concluding info that signals end of story/episode |
| [writing-participants](writing-participants.md) | Introducing new characters or reintroducing old ones in narrative |

#### Quotation Structure
| Issue | Description |
|-------|-------------|
| [figs-quotations](figs-quotations.md) | Converting between direct and indirect quotations |
| [figs-quotemarks](figs-quotemarks.md) | Using quotation marks or punctuation to mark quote boundaries |
| [figs-quotesinquotes](figs-quotesinquotes.md) | Simplifying nested quotations by converting inner levels to indirect |
| [writing-quotations](writing-quotations.md) | Quote margins - "saying," "answered and said," missing speech identifiers |

#### Poetry/Wisdom
| Issue | Description |
|-------|-------------|
| [writing-poetry](writing-poetry.md) | Cognate accusative (verb + noun same root), sound play, poetic structures |
| [writing-proverbs](writing-proverbs.md) | Short sayings teaching general wisdom about life |
| [figs-parables](figs-parables.md) | Short illustrative stories teaching truth (kingdom parables, teaching stories) |

### B. Grammar

#### Voice
| Issue | Description |
|-------|-------------|
| [figs-activepassive](figs-activepassive.md) | ALL passive voice in English (aux + participle), not stative verbs (be ashamed, be afraid) - every instance needs a note |

#### Pronouns & Person
| Issue | Description |
|-------|-------------|
| [figs-123person](figs-123person.md) | Unexpected grammatical person (self/addressee in 3rd person) |
| [figs-you](figs-you.md) | General "you" clarification - who is being addressed (infrequent) |
| [figs-yousingular](figs-yousingular.md) | Clarifying singular/plural forms of "you" (marks PLURAL despite name) |
| [figs-youdual](figs-youdual.md) | Exactly two people being addressed (for languages with dual pronouns) |
| [figs-youcrowd](figs-youcrowd.md) | Singular pronouns addressing a crowd |
| [figs-youformal](figs-youformal.md) | Formal vs informal register when addressing someone (rare) |
| [figs-exclusive](figs-exclusive.md) | Inclusive/exclusive "we/us/our" - does pronoun include the addressee? |
| [figs-rpronouns](figs-rpronouns.md) | Reflexive pronouns - same person is subject and object |
| [writing-pronouns](writing-pronouns.md) | Pronoun clarification - unclear referents, independent pronouns, indefinite "they" |
| [figs-gendernotations](figs-gendernotations.md) | Masculine terms used generically to include women (brothers, sons, man) |

#### Noun Structures
| Issue | Description |
|-------|-------------|
| [figs-abstractnouns](figs-abstractnouns.md) | Abstract nouns (faith, grace, salvation) - detection script available |
| [figs-nominaladj](figs-nominaladj.md) | Adjectives used as nouns (the righteous, the poor, many) |
| [figs-genericnoun](figs-genericnoun.md) | Singular nouns referring to categories/types in general (the ant, the righteous one) |
| [grammar-collectivenouns](grammar-collectivenouns.md) | Singular nouns referring to groups (Israel, flock, their heart) |
| [figs-possession](figs-possession.md) | Possessive forms expressing relationships other than ownership |

#### Negation
| Issue | Description |
|-------|-------------|
| [figs-doublenegatives](figs-doublenegatives.md) | Two negative words in clause - grammatical negatives or negated antonyms |
| [figs-litotes](figs-litotes.md) | Understatement using double negative for EMPHATIC positive meaning |

### C. Clause Relations

#### Temporal
| Issue | Description |
|-------|-------------|
| [grammar-connect-time-background](grammar-connect-time-background.md) | Ongoing clause as time frame for main event (while, when + ongoing) |
| [grammar-connect-time-sequential](grammar-connect-time-sequential.md) | Sequential events (A then B) - connector may need clarification |
| [grammar-connect-time-simultaneous](grammar-connect-time-simultaneous.md) | Simultaneous events (A and B at same time) - connector may need clarification |
| [figs-events](figs-events.md) | Events narrated out of chronological order - reordering needed |

#### Logical
| Issue | Description |
|-------|-------------|
| [grammar-connect-logic-goal](grammar-connect-logic-goal.md) | Purpose/goal relationships - agent intends the outcome |
| [grammar-connect-logic-result](grammar-connect-logic-result.md) | Reason/result relationships - cause-effect without intention |
| [grammar-connect-logic-contrast](grammar-connect-logic-contrast.md) | Contrast relationships - unexpected or opposing elements |
| [grammar-connect-exceptions](grammar-connect-exceptions.md) | Exception clauses - "except," "unless," exclusionary statements |

#### Conditional
| Issue | Description |
|-------|-------------|
| [figs-hypo](figs-hypo.md) | Imaginary/unreal situations (contrary-to-fact, wishes, impossible scenarios) |
| [grammar-connect-condition-hypothetical](grammar-connect-condition-hypothetical.md) | Simple conditions needing "if/then" clarification or reordering |
| [grammar-connect-condition-contrary](grammar-connect-condition-contrary.md) | Contrary-to-fact conditions - known to be false |
| [grammar-connect-condition-fact](grammar-connect-condition-fact.md) | Factual conditions - known to be true |

#### Connectors
| Issue | Description |
|-------|-------------|
| [grammar-connect-words-phrases](grammar-connect-words-phrases.md) | General connecting words (And, Now, But, For) with non-standard function or structural role |

### D. Figures of Speech

#### Explicit Comparison
| Issue | Description |
|-------|-------------|
| [figs-simile](figs-simile.md) | Explicit comparison using "like," "as," "than" |

#### Implicit Comparison
| Issue | Description |
|-------|-------------|
| [figs-metaphor](figs-metaphor.md) | Topic spoken of as if it were a different thing (no comparison words) |
| [figs-metonymy](figs-metonymy.md) | Item called by name of something associated with it |
| [figs-synecdoche](figs-synecdoche.md) | Part represents whole, or whole represents part |
| [figs-personification](figs-personification.md) | Non-living/abstract things performing actions of living beings |

#### Emphasis/Intensification
| Issue | Description |
|-------|-------------|
| [figs-hyperbole](figs-hyperbole.md) | Exaggeration or generalization for emphasis (all, every, never) |
| [figs-doublet](figs-doublet.md) | Two synonymous words/phrases for emphasis (word-level, not clauses) |
| [figs-hendiadys](figs-hendiadys.md) | Two different words where one modifies the other ("kingdom and glory" = glorious kingdom) |
| [figs-parallelism](figs-parallelism.md) | Synonymous clauses repeating same idea for emphasis (poetry) |
| [figs-litany](figs-litany.md) | Series of 3+ similar statements showing comprehensiveness (prophetic) |
| [figs-reduplication](figs-reduplication.md) | Repeated words/forms for emphasis (infinitive absolute, word doubling) |
| [figs-merism](figs-merism.md) | Two extremes/components representing the whole |

#### Fixed Expressions
| Issue | Description |
|-------|-------------|
| [figs-idiom](figs-idiom.md) | Fixed expression with non-compositional meaning |
| [figs-euphemism](figs-euphemism.md) | Polite way of referring to unpleasant/embarrassing topics |
| [writing-oathformula](writing-oathformula.md) | Oath formulas - swearing by Yahweh, conditional oaths, sacred guarantees |
| [writing-symlanguage](writing-symlanguage.md) | Symbolic images representing other things (visions, apocalyptic) |
| [translate-symaction](translate-symaction.md) | Physical actions with cultural/religious meaning |

#### Irony/Indirection
| Issue | Description |
|-------|-------------|
| [figs-irony](figs-irony.md) | Speaker means the opposite of literal words |
| [figs-rquestion](figs-rquestion.md) | Questions used for emphasis, rebuke, emotion - not seeking info |

### E. Speech Acts

#### Commands
| Issue | Description |
|-------|-------------|
| [figs-imperative](figs-imperative.md) | Second-person imperatives used as requests, conditions, or other non-command purposes |
| [figs-imperative3p](figs-imperative3p.md) | Third-person imperatives ("Let there be," "Let no one") - many languages lack this form |
| [figs-declarative](figs-declarative.md) | Statements used for commands, instructions, requests, or performatives |

#### Exclamations/Address
| Issue | Description |
|-------|-------------|
| [figs-exclamations](figs-exclamations.md) | Words/sentences showing strong feeling (Oh, Alas, How, Behold) |
| [figs-apostrophe](figs-apostrophe.md) | Speaker addresses someone/something that cannot hear (cities, objects, absent people) |
| [figs-aside](figs-aside.md) | Speaker pauses to address self/God/reader about current audience |

### F. Information Management

#### Explicitness
| Issue | Description |
|-------|-------------|
| [figs-explicit](figs-explicit.md) | Implicit information to make explicit |
| [figs-explicitinfo](figs-explicitinfo.md) | Redundant information to make implicit |
| [figs-extrainfo](figs-extrainfo.md) | Intentionally vague - keep implicit |
| [figs-ellipsis](figs-ellipsis.md) | Words omitted that reader must supply from context (often co-occurs with parallelism in poetry) |
| [figs-infostructure](figs-infostructure.md) | Word/clause order differs from natural target language order |

### G. Cultural/Reference

#### Names & People
| Issue | Description |
|-------|-------------|
| [translate-names](translate-names.md) | Proper names needing clarification (person, place, group identification) |
| [translate-kinship](translate-kinship.md) | Kinship terms requiring language-specific relationship words |
| [translate-blessing](translate-blessing.md) | Short sayings asking God to do good for another person |
| [translate-transliterate](translate-transliterate.md) | Non-name words ULT keeps in original form (Amen, Abba, Hosanna) |
| [translate-unknown](translate-unknown.md) | Concepts/objects unfamiliar to target culture (animals, foods, practices) |
| [translate-plural](translate-plural.md) | Number mismatches: plurals for singular (intensive plural, royal we) OR singulars for plural (representative singular) |

#### Numbers & Measures
| Issue | Description |
|-------|-------------|
| [translate-numbers](translate-numbers.md) | Cardinal numbers - large/complex numbers, exact vs approximate |
| [translate-ordinal](translate-ordinal.md) | Ordinal numbers - position in sequence (first, second, seventh) |
| [translate-fraction](translate-fraction.md) | Fractions - parts of a whole (half, third, tenth) |
| [translate-bdistance](translate-bdistance.md) | Biblical distance units (cubits, spans, stadia) |
| [translate-bmoney](translate-bmoney.md) | Biblical monetary units (denarii, talents, minas) |
| [translate-bvolume](translate-bvolume.md) | Biblical volume units (ephah, hin, bath) |
| [translate-bweight](translate-bweight.md) | Biblical weight units (shekels, talents as weight) |
| [translate-hebrewmonths](translate-hebrewmonths.md) | Hebrew calendar month names or ordinal month references |

#### Text Issues
| Issue | Description |
|-------|-------------|
| [translate-textvariants](translate-textvariants.md) | Manuscript differences - ancient copies have different words |
| [translate-alternativereadings](translate-alternativereadings.md) | Hebrew text issues - Qere/Ketiv, LXX corrections |
| [translate-versebridge](translate-versebridge.md) | Combining verses when information needs reordering (always multi-verse) |
| [translate-tense](translate-tense.md) | Tense/aspect issues in translation |
| [figs-pastforfuture](figs-pastforfuture.md) | Past tense used for future events (prophetic perfect) |
| [figs-go](figs-go.md) | Motion verbs (go/come, bring/take) needing perspective adjustment |
| [writing-politeness](writing-politeness.md) | Politeness strategies in speech |

## Recognition Flow

For detailed recognition guidance, consult the individual issue skill files.

## Adding New Issue Types

To create a skill for a new translation issue:
1. See `../utilities/create-issue-skill.md`
2. Check `data\translation-issues.csv` for issue list and tracking
