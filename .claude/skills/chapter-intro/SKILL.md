---
name: chapter-intro
description: Write chapter introductions for biblical text chapters. Run after pipeline (ULT-gen, issue-id, UST-gen) to produce translator-oriented intros.
allowed-tools: Read, Grep, Glob, Bash, Write, Edit
---

# Chapter Introduction

Generate a chapter introduction that orients translators to a psalm's structure, type, key concepts, and translation challenges. Run this after the pipeline (ULT-gen, issue-identification, UST-gen) has completed for a chapter.

## Arguments

When invoked as `/chapter-intro psa 18`:
- First argument: Book abbreviation (psa, gen, 2sa, etc.)
- Second argument: Chapter number

Book abbreviations follow standard 3-letter codes or common variants:
- psa, ps -> PSA
- 2sam, 2sa -> 2SA
- gen -> GEN

## Workflow

### Step 1: Gather Inputs

Normalize arguments:
- Book code: uppercase 3-letter code (e.g., `PSA`)
- Chapter: zero-padded 3-digit for filenames (e.g., `061`), plain number for references (e.g., `61`)

Read the following files. Not all may exist; work with what's available.

**Pipeline output (preferred):**
- ULT: `output/AI-ULT/<BOOK>-<CHAPTER_PAD>.usfm`
- Issues: `output/issues/<BOOK>-<CHAPTER_PAD>.tsv`
- UST: `output/AI-UST/<BOOK>-<CHAPTER_PAD>.usfm`

**Fallbacks if pipeline output doesn't exist:**
- Published ULT: `data/published_ult_english/` (find the book file, extract the chapter)
- Published UST: `data/published_ust_english/` (find the book file, extract the chapter)

**Always read:**
- Hebrew source: find the chapter in `data/hebrew_bible/` (search for the book's USFM file containing the chapter)

**Reference materials (consult as needed):**
- Published TN intros for style reference: `data/published-tns/tn_PSA.tsv` (grep for `^PSA\t<chapter>\tintro`)
- Translation Words for key terms: use `python3 .claude/skills/issue-identification/scripts/check_tw_headwords.py "term1" "term2"` or browse `data/en_tw/`
- Translation Academy for psalm type definitions: `data/ta-flat/`

### Step 2: Determine Psalm Type and Context

Parse the superscription (verse 1 or "front" matter) looking for:
- Authorship attribution ("Of David", "Of Asaph", "Of the sons of Korah")
- Genre markers ("maskil", "miktam", "song of ascents", "a prayer")
- Performance instructions ("For the chief musician", "On a stringed instrument")
- Historical occasion ("When he fled from Absalom")

Classify the psalm type:
- **Lament** (individual or communal) -- complaint, petition, trust, praise
- **Praise/Hymn** -- celebration of Yahweh's character or deeds
- **Thanksgiving** -- response to specific deliverance
- **Wisdom** -- instruction, contrast of righteous/wicked
- **Royal/Messianic** -- about the king, enthronement
- **Trust/Confidence** -- expression of reliance on Yahweh
- **Worship** -- liturgical, temple-focused (e.g., Psalms 95-100)
- **Imprecatory** -- appeals against enemies
- **Penitential** -- confession and plea for mercy

Check if the psalm belongs to a known group:
- Psalms 95-100: worship psalms
- Psalms 103-107: praise psalms
- Psalms 120-134: songs of ascents
- Psalms 146-150: Hallel psalms

### Step 3: Analyze Structure

Read through the ULT (or Hebrew if ULT unavailable) and identify natural divisions:
- Thematic shifts (complaint -> petition -> praise)
- Speaker changes (psalmist -> God -> congregation)
- Selah markers as possible section breaks
- Stanza patterns in poetic sections
- Shifts in addressee (speaking to God vs. speaking about God)

Create a numbered outline with verse ranges and brief descriptions:
- Format: `1. Description of section content (verse-range)`
- Keep descriptions concise (one phrase or short sentence)
- Use inclusive verse ranges with en-dashes: `(1-5)` not `(1-4)`
- Cover all verses with no gaps or overlaps
- If a superscription exists, it can be its own section or included with the first section

### Step 4: Identify Key Concepts

Scan the issues TSV for recurring patterns:
- Multiple metaphors around the same concept = extended metaphor worth mentioning
- Recurring metonymy with body parts = pattern worth noting
- Abstract nouns clustering around a theme (righteousness, faithfulness, etc.)

Identify cultural/religious concepts translators need context for:
- Covenant language (hesed/steadfast love, name, way)
- Temple/worship references (Zion, sanctuary, offerings)
- Historical allusions
- Theological claims about God's nature
- Concepts that may not translate directly across cultures

For key theological terms, check Translation Words:
```bash
python3 .claude/skills/issue-identification/scripts/check_tw_headwords.py "covenant" "righteous" "salvation"
```

Use `[[rc://*/tw/dict/bible/kt/<term>]]` format for Translation Word links.

### Step 5: Check for Translation Issues

Only include a "Translation Issues" section when genuinely distinctive challenges exist:
- Extended metaphors spanning multiple verses
- Singular/plural shifts in referents
- Hebrew poetry patterns that affect translation (acrostic, chiasm)
- Speaker ambiguity or changes
- Text-critical issues or debated interpretations
- Unusual wordplay that translators should be aware of

Do NOT include this section for routine issues that are already covered in verse-level notes. Most psalms will not need this section.

### Step 6: Draft the Introduction

Follow the template below. Use the **detailed format** for most psalms. Use the **brief format** only for psalms that are part of a well-known group AND have straightforward content (e.g., Psalms 96-100).

#### Detailed Format Template

```
# Psalm N Introduction

## Structure and Formatting

[One sentence classifying the psalm type. Link to tA or tW if helpful.]

  1. [Section description] ([verse-range])
  2. [Section description] ([verse-range])
  ...

[Optional: note about superscription genre term, e.g., "See the introduction to Psalm 6 for a discussion of the word 'miktam.'"]

## About the Psalm

[1-2 paragraphs: historical context, authorship, occasion if known, relationship to other psalms or biblical passages. Cross-references use markdown links: [2 Samuel 22](../2sa/22/01.md). Keep this translator-oriented, not devotional commentary.]

## Religious and Cultural Concepts in This Psalm

### [Concept Name]

[1-2 sentences explaining the concept and why it matters for translators.]

### [Additional concepts as needed]

[...]

## Translation Issues

### [Issue Name]

[Only include if there are distinctive translation challenges beyond normal verse-level notes.]
```

#### Brief Format Template (for grouped psalms)

```
# Psalm NNN General Notes

## Type of Psalm

[One sentence classifying the psalm and its group membership.]

## Religious and Cultural Concepts in This Chapter

### [Concept Name]

[1-2 sentences.]
```

**Decision rule:** Use detailed format unless the psalm is part of a well-known group AND the content is straightforward. When in doubt, use detailed.

#### Quality Checks Before Finalizing

- Structure outline covers all verses (no gaps)
- Verse ranges don't overlap
- Psalm type matches actual content
- tW links use `[[rc://*/tw/dict/bible/kt/<term>]]` or `[[rc://*/tw/dict/bible/other/<term>]]` format
- Cross-references use `[Book Chapter](../book/chapter/verse.md)` format
- Content is translator-oriented, not devotional commentary
- No verse-level detail that belongs in translation notes instead
- Tone is informative and measured, not dramatic
- Follow shared style rules in `../ULT-gen/reference/gl_guidelines.md`

### Step 7: Format and Insert into Issue File

**Format the intro for TSV storage:**
1. Escape all newlines as literal `\n` (two characters: backslash + n)
2. The intro content goes in column 7 (the explanation/content column)

**Build the issue TSV row (7 tab-separated columns, matching issue TSV format):**
```
<book>\t<chapter>:intro\t\t\t\t\t<escaped intro content>
```

Example:
```
psa	61:intro					# Psalm 61 Introduction\n\n## Structure and Formatting\n\n...
```

Columns:
1. Book code (lowercase, e.g., `psa`)
2. Reference: `<chapter>:intro`
3. Issue type: (empty)
4. ULT quote: (empty)
5. Go? flag: (empty)
6. AT: (empty)
7. Content: the full intro with `\n` escapes

**Insert into the issue file:**
1. Read the existing issue file at `output/issues/<BOOK>-<CHAPTER_PAD>.tsv`
2. Prepend the intro row as the first line
3. Write back to the same file

If the issue file already has an intro row (first line contains `:intro`), replace it rather than adding a duplicate.

**Confirm the result** by reading back the first 3 lines of the file to verify the intro row is correctly placed and formatted.
