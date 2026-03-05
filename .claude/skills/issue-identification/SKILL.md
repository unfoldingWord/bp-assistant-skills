---
name: issue-identification
description: Find translation issues in ULT/Hebrew/Greek texts. Covers 94 issue types across 7 categories. Use when asked to identify issues, find what needs notes, or analyze a passage for translation concerns.
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

#### Step 2b: Check Editor Notes

```bash
EDITOR_NOTES="data/editor-notes/<BOOK>.md"
if [ -f "$EDITOR_NOTES" ]; then
  cat "$EDITOR_NOTES"
fi
```

If editor notes exist for this book, read them carefully. These are observations from human editors who have already been working through the text. They may flag:
- Patterns to watch for (e.g., "heavy implicit information around covenant context")
- Specific chapter concerns
- Issue types they expect to be prevalent

Incorporate these observations into your analysis — they should heighten your attention to the flagged patterns, not replace your systematic review.

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

#### Step 4: Run Automated Detection and Identify Passives

**Abstract nouns** -- run the detection script:

```bash
# Abstract nouns - evaluate each for note necessity
python3 .claude/skills/issue-identification/scripts/detection/detect_abstract_nouns.py \
  /tmp/alignments.json --format tsv >> /tmp/detected_issues.tsv
```

**Passive voice** -- identify ALL passive constructions during your verse-by-verse analysis (no script needed). Read the detection instructions in `figs-activepassive.md` for the passive voice pattern (auxiliary "be" + past participle), stative adjective exclusions, and worked examples. Every passive construction needs a note.

Merge detected issues into final output.

### Option B: Quick Workflow (plain English text)

When you just have English text (no USFM, no alignments), use `--text` to run detection directly. This skips source language morphology checks but still finds abstract nouns. Passive voice is identified by Claude during analysis (see `figs-activepassive.md`).

```bash
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

For any unusual phrases noticed, check the published TN index first, then fall back to raw grep:
```bash
# Fast: check index for keyword classification precedent
python3 .claude/skills/utilities/scripts/build_tn_index.py --lookup "phrase"

# Fallback: raw grep when index doesn't have what you need
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
# Fast: check index for keyword or issue type
python3 .claude/skills/utilities/scripts/build_tn_index.py --lookup "keyword"
python3 .claude/skills/utilities/scripts/build_tn_index.py --issue figs-metonymy

# Check prior decisions
grep "keyword" data/quick-ref/issue_decisions.csv 2>/dev/null

# Fallback: raw grep when index doesn't have what you need
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
- Check abstract noun detection script output first - abstract nouns are pre-identified
- Identify all passive constructions yourself using the patterns in `figs-activepassive.md`
- Mark those tasks as completed with the findings
- For names/unknowns, run `check_tw_headwords.py` before flagging

### Systematic Review Principles

1. **Detection first** - integrate abstract nouns from scripts and passives from your own analysis
2. **tW check for names** - run `check_tw_headwords.py` before flagging translate-names/translate-unknown
3. **Search when uncertain** - check the published TN index first (`build_tn_index.py --lookup`), then `data/published-tns/` for similar phrases
4. **Consult Issues Resolved and Note Templates** - when classifications conflict, `data/issues_resolved.txt` and `data/templates.csv` have final authority on how issues are classified
5. **Check implicit info** - would modern readers miss cultural practices, theological concepts, or covenant language?
6. **Record non-trivial decisions** - after resolving a classification that required checking published precedent or where multiple issue types were plausible, append to `data/quick-ref/issue_decisions.csv`

The goal is coverage: it's easier for reviewers to delete a suggested issue than to identify one from scratch. When in doubt, include it.

### Genre-Specific Checks

**For Psalms/Prayers**: Make an extra pass for:
- **figs-imperative**: Imperatives addressed to God are requests, not commands
- **figs-explicit**: Covenant concepts (hesed, name, way) may need explanation
- **figs-parallelism vs figs-doublet**: If synonymous expressions fall on different poetic lines, classify as parallelism not doublet. For 3-line parallel verses, one parallelism note covers all lines. Quote the full parallel lines, not just key words.
- **figs-ellipsis with parallelism**: Check parallel lines for omitted words, but skip if ULT already supplies them in `{}`.
- **figs-rquestion across poetic lines**: When a rhetorical question spans multiple \q lines, quote the full question through the `?`. Do not stop at the first poetic line.
- **figs-123person for "your servant"**: When the psalmist addresses God using "your servant" to refer to himself, flag as figs-123person (Type 1: self-reference for humility). This is common in Psalms (e.g., PSA 19:11, 19:13, 119:17, 119:49, 119:65, 119:122, 119:125, 119:135, 119:176) and needs its own note even when the verse also has another issue like figs-imperative or figs-metaphor. Do not use writing-politeness for this pattern in Psalms.

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
| hand, hands, eyes, face | figs-metonymy or figs-synecdoche (body part for action/person?) |
| heart | figs-metaphor (heart = thoughts/feelings/will; see template) |
| all, every, never, always | figs-hyperbole (exaggeration for emphasis?) |
| the righteous, the wicked, the poor | figs-nominaladj (adjective as noun?) |

### Commonly Confused Issue Pairs

Before finalizing a tag, check if a related issue fits better:

| If considering... | Also check... | Key distinction |
|-------------------|---------------|-----------------|
| writing-pronouns | figs-gendernotations | Unclear referent vs. generic masculine |
| figs-metaphor | figs-simile | No comparison word vs. explicit "like/as" |
| figs-metonymy | figs-synecdoche | Associated thing vs. part/whole relationship |
| figs-idiom | figs-metonymy / figs-synecdoche | Fixed cultural expression vs. live figure (body-part triple) |
| figs-doublet | figs-parallelism | Word-level pair vs. clause-level repetition |
| figs-doublet | figs-hendiadys | Synonyms for emphasis vs. one modifies other |
| figs-idiom | figs-metaphor | Fixed expression vs. live comparison |
| figs-hyperbole | figs-merism | General exaggeration vs. two extremes = whole |
| figs-rquestion | figs-exclamations | Question form vs. exclamation form |
| figs-explicit | figs-ellipsis | Adding background info vs. supplying omitted words |
| grammar-connect-logic-goal | grammar-connect-logic-result | Intended outcome vs. unintended consequence |

### Competing Figurative Analyses (Pick One)

When the same phrase could be classified under multiple figurative issue types (e.g., synecdoche, metonymy, and idiom for "a lip of falsehood"), these represent competing analyses of the same feature, not complementary layers. Pick the single best fit.

Decision hierarchy for body-part and cultural expressions:
1. Is it a fixed cultural expression where the literal meaning has faded? -> figs-idiom
2. Is it association-based (thing for related thing, organ for its function)? -> figs-metonymy
3. Is it part-for-whole (can the whole person be substituted)? -> figs-synecdoche

This hierarchy reflects content team decisions in `data/issues_resolved.txt`. Grammar-layer issues (figs-abstractnouns, figs-activepassive, figs-possession) remain independent and always coexist alongside a figurative tag on the same phrase.

### Biblical Imagery Classification

When classifying body parts, nature imagery, or cultural concepts as metonymy vs metaphor, consult the authoritative lists in `figs-metonymy.md` and `figs-metaphor.md` (under "Authoritative Biblical Imagery" sections).

### Final Review Pass

After completing all identification, review your output:

1. **Tag verification**: For each issue tagged, can you point to specific criteria in the skill definition it meets? If unsure, re-read the skill file.

2. **Cross-verse interpretive consistency**: Scan the full issue list for explanations that reference or depend on adjacent verses. Specifically check:
   - **Pronoun resolution**: When a `writing-pronouns` issue resolves a referent from another verse (e.g., "it refers to X in the previous verse"), verify that your explanation of X in that other verse is compatible. If v9 says "inheritance" is a metaphor for people, v10 cannot say "it" refers to the land.
   - **Carried figures**: When a metaphor, metonymy, or other figure in one verse is referenced by an issue in a nearby verse, ensure the interpretations agree on what the figure represents.
   - **Ambiguous terms**: When the same Hebrew word or phrase is discussed in multiple verses, check that your explanations don't silently adopt different interpretations. If the interpretation is genuinely debatable, use a TCM note in the originating verse rather than letting different verses assume different answers.

3. **Duplicate check**: Did you tag the same phrase twice for issues that are really one? (e.g., tagging both figs-doublet and figs-parallelism for the same word pair)
   Also check for **competing figurative analyses**: if the same phrase has two or more
   figurative tags (e.g., figs-synecdoche + figs-metonymy + figs-idiom), keep only the
   single best fit using the decision hierarchy in "Competing Figurative Analyses" above.

4. **Missing overlap check**: Are there phrases that genuinely need two tags? (e.g., a simile that also contains an abstract noun - both figs-simile AND figs-abstractnouns may apply)
   Abstract nouns, passives (figs-abstractnouns, figs-activepassive) are script-detected
   and exist at a different analytical layer than figures of speech. They always coexist --
   a figurative issue on the same phrase does not replace a grammar issue. Other grammar-level
   issues (figs-possession, figs-ellipsis, figs-nominaladj) should also generally not be
   dropped or merged with figurative issues.
   But multiple figurative issue types on the same phrase (figurative+figurative, not
   grammar+figurative) represent competing analyses -- see "Competing Figurative Analyses."

5. **Keyword sweep**: Scan output for any keyword triggers above that you may have tagged incorrectly.

## Authoritative Sources

### Final Authority: Issues Resolved
Consult `data/issues_resolved.txt` before finalizing issue classifications.
This document contains content team decisions that override other guidance.

```bash
# Search for relevant decisions
cat data/issues_resolved.txt | grep -i "[search term]"
```

### Note Templates (Classification Reference)
The note templates in `data/templates.csv` reflect confirmed team decisions on how issues are classified and described. When a template exists for an expression (e.g., "heart" under figs-metaphor), that classification is authoritative. Issue identification should tag issues consistently with how templates classify them.

Note: issue-identification produces *explanations*, not notes. But the template classifications indicate which support reference to use.

```bash
# Check how a term is classified in templates
grep -i "heart" data/templates.csv
```

### Published TN Index
Pre-built index of all published translation notes by issue type and keyword. Use for fast precedent lookups instead of raw grep:

```bash
# Check how a keyword was classified across all published notes
python3 .claude/skills/utilities/scripts/build_tn_index.py --lookup "hand"

# List examples for a specific issue type
python3 .claude/skills/utilities/scripts/build_tn_index.py --issue figs-metaphor
```

Source: `data/cache/tn_index.json` (built from `data/published-tns/`)

**Precedent evidence is positive-only.** Finding examples in the index supports a classification. Finding none is only meaningful if the chapter you searched actually has published TNs. Psalms is partially published — many chapters have no published TNs because AI drafting was adopted before they were completed. Do not cite "no results in this chapter" as evidence against a classification.

### Issue Decisions
Accumulated classification decisions from prior runs. Check before re-deriving:

```bash
grep "hand of" data/quick-ref/issue_decisions.csv 2>/dev/null
```

Source: `data/quick-ref/issue_decisions.csv` (append-only)

### Reference Examples: Published Notes
When the index doesn't have what you need, search `data/published-tns/` directly:

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
| detect_abstract_nouns.py | scripts/detection/ | Find abstract nouns (591 word list). Use `--text "..."` for plain English |
| check_tw_headwords.py | scripts/ | Check names/unknowns against tW headwords - filters translate-names/translate-unknown |
| build_tn_index.py | utilities/scripts/ | Published TN index lookup. `--lookup "hand"` for keyword, `--issue figs-metaphor` for issue type |

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

## Troubleshooting

- **fetch_door43.py fails**: Check network connectivity and that the book/chapter exists on Door43. The script retries 3 times with backoff. If the resource was recently published, allow a few minutes for CDN propagation.
- **detect_abstract_nouns.py returns empty**: The detection script found no abstract nouns in the passage. This is normal for short or concrete passages. Verify the input USFM has content and is not a header-only file.
- **Too many issues flagged**: If a passage generates more than ~30 issues, review for duplicates and low-confidence entries. Use the confidence threshold filter (0.7 default) and check that the same verse span is not being flagged by overlapping issue types.
- **Too few issues flagged**: Ensure all 7 category modules ran. Check the log for skipped categories (usually caused by missing input files). Re-run with `--categories all` to force all categories.

## Output Format

After identifying issues, output a tab-separated file to `output/issues/`:

```
output/issues/[BOOK]/[BOOK]-[CHAPTER].tsv
```

Examples:
- `output/issues/PSA/PSA-063.tsv` - Psalm 63
- `output/issues/GEN/GEN-01.tsv` - Genesis 1
- `output/issues/2SA/2SA-01.tsv` - 2 Samuel 1

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

**Ordering**: Within each verse, output issues in ULT reading order:
1. **First to last** by start position of the quoted phrase in the ULT verse
2. **Longest to shortest** when phrases overlap or nest (the containing phrase comes before its sub-phrases)

Example for "For you are a refuge to me, a strong tower from the face of the enemy":
```
psa	61:3	figs-metaphor	For you are a refuge to me, a strong tower from the face of the enemy
psa	61:3	figs-metaphor	For you are a refuge to me
psa	61:3	figs-metaphor	a refuge
psa	61:3	figs-metonymy	from the face of the enemy
psa	61:3	figs-possession	of the enemy
```

General example:
```
psa	78:17	writing-pronouns	And they added			ancestors/israelites
psa	78:19	figs-rquestion	Is God able			rhetorical - asserting doubt
gen	1:5	figs-infostructure	evening and morning			time phrase order
```

## Available Issue Types

94 issue types organized into 7 categories: Discourse Structure, Grammar, Clause Relations, Figures of Speech, Speech Acts, Information Management, Cultural/Reference.

For the full catalog with links to each issue skill, see [reference/issue-types-catalog.md](reference/issue-types-catalog.md).

## Recognition Flow

For detailed recognition guidance, consult the individual issue skill files.

## Adding New Issue Types

To create a skill for a new translation issue:
1. See `../utilities/create-issue-skill.md`
2. Check `data/translation-issues.csv` for issue list and tracking
