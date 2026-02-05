---
name: ULT-alignment

description: Create word-level alignments between Hebrew source and English ULT text. AI produces a simple index-based mapping JSON that a script converts to properly formatted aligned USFM.

allowed-tools: Read, Grep, Glob, Bash
---

## Overview

This skill maps English ULT words to Hebrew source words. The workflow is two-step:
1. **AI creates** a simple index-based mapping (English words to Hebrew word positions)
2. **Script converts** that mapping to properly formatted aligned USFM

## Input Requirements

You need:
1. **Hebrew USFM** from `data/hebrew_bible/*.usfm` - contains Strong's numbers, lemmas, morphology
2. **English ULT text** - either from `output/AI-ULT/` or user-provided

## Output Format: Simple Mapping JSON

Create a JSON file with this structure:

```json
{
  "reference": "GEN 1:1",
  "hebrew_words": [
    {"index": 0, "word": "בְּ⁠רֵאשִׁ֖ית", "strong": "b:H7225", "lemma": "רֵאשִׁית"},
    {"index": 1, "word": "בָּרָ֣א", "strong": "H1254a", "lemma": "בָּרָא"},
    {"index": 2, "word": "אֱלֹהִ֑ים", "strong": "H0430", "lemma": "אֱלֹהִים"},
    {"index": 3, "word": "אֵ֥ת", "strong": "H0853", "lemma": "אֵת"},
    {"index": 4, "word": "הַ⁠שָּׁמַ֖יִם", "strong": "d:H8064", "lemma": "שָׁמַיִם"},
    {"index": 5, "word": "וְ⁠אֵ֥ת", "strong": "c:H0853", "lemma": "אֵת"},
    {"index": 6, "word": "הָ⁠אָֽרֶץ", "strong": "d:H0776", "lemma": "אֶרֶץ"}
  ],
  "english_text": "In the beginning God created the heavens and the earth.",
  "alignments": [
    {"hebrew_indices": [0], "english": ["In", "the", "beginning"]},
    {"hebrew_indices": [2], "english": ["God"]},
    {"hebrew_indices": [1], "english": ["created"]},
    {"hebrew_indices": [3, 4], "english": ["the", "heavens"]},
    {"hebrew_indices": [5], "english": ["and"]},
    {"hebrew_indices": [6], "english": ["the", "earth"]}
  ]
}
```

### Key Fields

| Field | Description |
|-------|-------------|
| `reference` | Book chapter:verse (e.g., "GEN 1:1") |
| `hebrew_words` | Array of Hebrew words with index, word form, Strong's, lemma |
| `english_text` | Complete English translation |
| `alignments` | Array mapping Hebrew indices to English word arrays |

### Alignment Entry Structure

- `hebrew_indices`: Array of Hebrew word indices (0-based)
  - Single index `[0]` for one Hebrew word
  - Multiple indices `[3, 4]` when multiple Hebrew words map to one English phrase
- `english`: Array of English words that render this Hebrew

## Alignment Principles

### 1. Precision is Highest Priority

Keep alignments at the smallest practical units. Prefer many precise alignments over few broad ones.

**Good:**
```json
{"hebrew_indices": [0], "english": ["In", "the", "beginning"]}
```

**Avoid:**
```json
{"hebrew_indices": [0, 1, 2], "english": ["In", "the", "beginning", "God", "created"]}
```

### 2. Articles Align with Head Nouns

English "the" and "a" align with the Hebrew word they modify, not separately.

Hebrew: הַ⁠שָּׁמַ֖יִם (the heavens)
```json
{"hebrew_indices": [4], "english": ["the", "heavens"]}
```

### 3. Direct Object Marker (אֵת)

The Hebrew direct object marker אֵת typically aligns with the following noun phrase.

Hebrew: אֵ֥ת הַ⁠שָּׁמַ֖יִם
```json
{"hebrew_indices": [3, 4], "english": ["the", "heavens"]}
```

### 4. Conjunction Handling

Prefixed conjunctions (וְ, וַ) usually align to English "and", "but", "then", etc.

Hebrew: וְ⁠אֵ֥ת
```json
{"hebrew_indices": [5], "english": ["and"]}
```

### 5. Bracketed Words (Grammatical Additions)

When English adds grammatical words not in Hebrew (marked with {brackets} in ULT), align them to the nearest Hebrew word they support - either before or after:

```json
// For "God {is} good" where טוֹב is the adjective
{"hebrew_indices": [tov_idx], "english": ["{is}", "good"]}

// For "{it was} morning" where בֹּקֶר is "morning"
{"hebrew_indices": [boqer_idx], "english": ["{it}", "{was}", "morning"]}
```

The bracketed word attaches to whichever Hebrew word it grammatically supports.

### 6. Construct Chains (Split Preferred)

For construct chains, split at each word to maintain word-level precision:

Hebrew: בֵּית אֱלֹהִים (house of God)
```json
{"hebrew_indices": [0], "english": ["house", "of"]},
{"hebrew_indices": [1], "english": ["God"]}
```

The "of" goes with the first word (construct form) since it represents the construct relationship.

### 7. Word Order Differences

Alignments follow English word order in the `alignments` array, regardless of Hebrew order.

Hebrew: בָּרָ֣א אֱלֹהִ֑ים (created God = God created)
```json
{"hebrew_indices": [2], "english": ["God"]},
{"hebrew_indices": [1], "english": ["created"]}
```

## Step-by-Step Workflow

### Step 1: Extract Hebrew Words

Read the Hebrew USFM for the verse:

```bash
grep -A 20 "\\v 1$" data/hebrew_bible/01-GEN.usfm | head -20
```

Parse each `\w` tag to extract:
- Word form (with cantillation marks)
- Strong's number
- Lemma

### Step 2: List English Words

Take the English ULT text and split into individual words. Preserve punctuation attached to words.

### Step 3: Create Alignments

For each Hebrew word (in English rendering order):
1. Identify which English word(s) translate it
2. Create an alignment entry with the Hebrew index and English words

### Step 4: Handle Special Cases

- Bracketed words `{like}` indicate additions - give empty hebrew_indices
- Multiple Hebrew words to one English phrase - use array of indices
- Untranslated Hebrew particles - may merge with following word

### Step 5: Verify Completeness

Check that:
- Every Hebrew word index appears in at least one alignment
- Every English word appears in exactly one alignment
- Total English words in alignments equals words in english_text

### Step 6: Save JSON

Write to scratchpad or output directory:

```
/tmp/claude-*/scratchpad/alignments/GEN-01-01.json
```

## Conversion to Aligned USFM

After creating the mapping JSON, run the conversion script:

```bash
node .claude/skills/utilities/scripts/usfm/create_aligned_usfm.js \
  --hebrew data/hebrew_bible/01-GEN.usfm \
  --mapping /tmp/alignments/GEN-01-01.json \
  --ult output/AI-ULT/GEN-01.usfm \
  --chapter 1 --verse 1
```

The script:
1. Reads Hebrew USFM to get full word metadata (Strong's, lemma, morph, x-content)
2. Reads your mapping JSON
3. Reads source ULT to preserve poetry markers (`\q1`, `\q2`)
4. Generates aligned USFM with proper `\zaln-s`, `\zaln-e`, and `\w` markers

**Important:** Always include `--ult` to preserve poetry formatting from the source translation.

## Final Output

After converting all verses, save the combined aligned USFM to `output/AI-ULT/`.

### Combining Multiple Verses

The script outputs **multi-line USFM** (one line per alignment). When combining verses, capture all lines including poetry markers:

```bash
# Create header
cat > output.usfm << 'EOF'
\id PSA EN_ULT - Aligned
\usfm 3.0
\ide UTF-8
\h Psalms
\mt Psalms

\c 78
EOF

# Append each verse (capture poetry markers, verse line, AND all alignment lines)
for v in $(seq 44 72); do
  node .claude/skills/utilities/scripts/usfm/create_aligned_usfm.js \
    --hebrew data/hebrew_bible/19-PSA.usfm \
    --mapping alignments/PSA-078-0${v}.json \
    --ult output/AI-ULT/PSA-078.usfm \
    --chapter 78 --verse $v 2>/dev/null | sed -n '/^\\q\|^\\v/,/^$/p' >> output.usfm
done
```

**Notes:**
- Always include `--ult` to preserve poetry markers (`\q1`, `\q2`)
- Use `sed -n '/^\\q\|^\\v/,/^$/p'` to capture lines starting with `\q` or `\v`
- Do NOT use `grep "^\v"` - this truncates all other lines

### Naming Convention

```
{BOOK}-{CHAPTER}-aligned.usfm              # whole chapter
{BOOK}-{CHAPTER}-{START}-{END}-aligned.usfm  # partial chapter
```

Examples:
- `PSA-078-aligned.usfm` (whole chapter)
- `PSA-078-44-72-aligned.usfm` (verses 44-72 only)
- `GEN-01-aligned.usfm` (whole chapter)

Use zero-padded chapter numbers: 3 digits for Psalms (150 chapters), 2 digits for all other books.

## Example: Genesis 1:1

### Hebrew Input
```
בְּ⁠רֵאשִׁ֖ית בָּרָ֣א אֱלֹהִ֑ים אֵ֥ת הַ⁠שָּׁמַ֖יִם וְ⁠אֵ֥ת הָ⁠אָֽרֶץ
```

### English Input
```
In the beginning God created the heavens and the earth.
```

### Mapping JSON Output
```json
{
  "reference": "GEN 1:1",
  "hebrew_words": [
    {"index": 0, "word": "בְּ⁠רֵאשִׁ֖ית", "strong": "b:H7225", "lemma": "רֵאשִׁית"},
    {"index": 1, "word": "בָּרָ֣א", "strong": "H1254a", "lemma": "בָּרָא"},
    {"index": 2, "word": "אֱלֹהִ֑ים", "strong": "H0430", "lemma": "אֱלֹהִים"},
    {"index": 3, "word": "אֵ֥ת", "strong": "H0853", "lemma": "אֵת"},
    {"index": 4, "word": "הַ⁠שָּׁמַ֖יִם", "strong": "d:H8064", "lemma": "שָׁמַיִם"},
    {"index": 5, "word": "וְ⁠אֵ֥ת", "strong": "c:H0853", "lemma": "אֵת"},
    {"index": 6, "word": "הָ⁠אָֽרֶץ", "strong": "d:H0776", "lemma": "אֶרֶץ"}
  ],
  "english_text": "In the beginning God created the heavens and the earth.",
  "alignments": [
    {"hebrew_indices": [0], "english": ["In", "the", "beginning"]},
    {"hebrew_indices": [2], "english": ["God"]},
    {"hebrew_indices": [1], "english": ["created"]},
    {"hebrew_indices": [3, 4], "english": ["the", "heavens"]},
    {"hebrew_indices": [5], "english": ["and"]},
    {"hebrew_indices": [6], "english": ["the", "earth"]}
  ]
}
```

## Quality Checklist

Before finalizing alignment JSON:

- [ ] Every Hebrew word index (0 to n-1) appears in at least one alignment
- [ ] Every English word appears exactly once across all alignments
- [ ] Articles align with their head nouns
- [ ] Direct object markers align with following noun
- [ ] Bracketed words align to the Hebrew word they support
- [ ] Construct chains are split (each word aligned separately)
- [ ] Word order in alignments array follows English text
- [ ] Hebrew words copied exactly from source (not typed manually)

## Related Skills

- [ULT-gen](../ULT-gen/SKILL.md) - Create the English ULT text
- [Pipeline Overview](../pipeline-overview/SKILL.md) - Where alignment fits in workflow

## Reference

See `reference/alignment_rules.md` for detailed alignment rules.
