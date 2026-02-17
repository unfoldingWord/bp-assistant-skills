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
2. **English ULT text** - either from `output/AI-ULT/{BOOK}/` or user-provided

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
| `english_text` | Complete English translation - **this is the authoritative word order** |
| `alignments` | Array mapping Hebrew indices to English word arrays |
| `d_text` | (Optional) Superscription text for `\d` line, used when a psalm has a superscription aligned to Hebrew words in verse 1 |

### Alignment Entry Structure

- `hebrew_indices`: Array of Hebrew word indices (0-based)
  - Single index `[0]` for one Hebrew word
  - Multiple indices `[3, 4]` when multiple Hebrew words map to one English phrase
- `english`: Array of English words that render this Hebrew
- `section`: (Optional) Set to `"d"` for alignment entries that belong on the `\d` superscription line rather than the `\v` verse line

### Critical: `english_text` Controls Output Word Order

The `english_text` field is **authoritative** for the final output word order. The conversion script:
1. Parses `english_text` to determine correct word sequence
2. Outputs each word in that exact order
3. Wraps each word in its corresponding Hebrew alignment

This means:
- **Alignment array order doesn't matter** - you can create alignments in any order (Hebrew order, English order, etc.)
- **The script will reorder** based on where each word appears in `english_text`
- **Non-consecutive aligned words work correctly** - words grouped in one alignment may appear separated in output

Example: Hebrew וַ⁠יִּקַ֖ץ אֲדֹנָי means "and-he-awoke the-Lord" but English is "And the Lord awoke"
```json
{
  "english_text": "And the Lord awoke...",
  "alignments": [
    {"hebrew_indices": [0], "english": ["And", "awoke"]},  // וַ⁠יִּקַ֖ץ
    {"hebrew_indices": [1], "english": ["the", "Lord"]}    // אֲדֹנָי
  ]
}
```
Output will be: "And" ... "the Lord" ... "awoke" (correct English order), not "And awoke the Lord"

### Superscription Alignment

There are two cases depending on how the ULT source structures the superscription:

#### Case 1: Superscription is part of verse 1 (e.g., Psalms 120-134)

When the ULT source has the superscription inside `\v 1` (with an empty `\d` marker):
```
\d
\v 1 A song of ascents
\q1 Remember, Yahweh, for David,
```

Do NOT use `d_text` or `section: "d"`. Include all words (superscription + body) in `english_text` and use normal alignment entries:
```json
{
  "reference": "PSA 132:1",
  "hebrew_words": [
    {"index": 0, "word": "...", "strong": "H7892a", "lemma": "שִׁיר"},
    {"index": 1, "word": "...", "strong": "d:H4609b", "lemma": "מַעֲלָה"},
    {"index": 2, "word": "...", "strong": "H2142", "lemma": "זָכַר"},
    {"index": 3, "word": "...", "strong": "H3068", "lemma": "יְהֹוָה"}
  ],
  "english_text": "A song of ascents Remember, Yahweh, for David, all of his afflictions,",
  "alignments": [
    {"hebrew_indices": [0], "english": ["A", "song"]},
    {"hebrew_indices": [1], "english": ["of", "ascents"]},
    {"hebrew_indices": [2], "english": ["Remember"]},
    {"hebrew_indices": [3], "english": ["Yahweh"]}
  ]
}
```

The script picks up the empty `\d` and `\q1`/`\q2` markers from the ULT source file automatically.

#### Case 2: Superscription on `\d` line, separate from verse 1 (`d_text` and `section`)

When the ULT source has the superscription text on the `\d` line (Hebrew v1 is only superscription, body starts at Hebrew v2 mapped to English v1):
```
\d For the chief musician. A song. A psalm.
\v 1 Shout to God, all the earth!
```

Use the `d_text` field and `"section": "d"` on relevant alignment entries:
```json
{
  "reference": "PSA 66:1",
  "hebrew_words": [
    {"index": 0, "word": "...", "strong": "l:H5329", "lemma": "נָצַח"},
    {"index": 1, "word": "...", "strong": "H7892a", "lemma": "שִׁיר"},
    {"index": 2, "word": "...", "strong": "H4210", "lemma": "מִזְמוֹר"},
    {"index": 3, "word": "...", "strong": "H7321", "lemma": "רוּעַ"},
    {"index": 4, "word": "...", "strong": "l:H0430", "lemma": "אֱלֹהִים"},
    {"index": 5, "word": "...", "strong": "H3605", "lemma": "כֹּל"},
    {"index": 6, "word": "...", "strong": "d:H0776", "lemma": "אֶרֶץ"}
  ],
  "d_text": "For the chief musician. A song. A psalm.",
  "english_text": "Shout to God, all the earth!",
  "alignments": [
    {"hebrew_indices": [0], "english": ["For", "the", "chief", "musician."], "section": "d"},
    {"hebrew_indices": [1], "english": ["A", "song."], "section": "d"},
    {"hebrew_indices": [2], "english": ["A", "psalm."], "section": "d"},
    {"hebrew_indices": [3], "english": ["Shout"]},
    {"hebrew_indices": [4], "english": ["to", "God,"]},
    {"hebrew_indices": [5, 6], "english": ["all", "the", "earth!"]}
  ]
}
```

The script will:
1. Process `section: "d"` alignments using `d_text` for word order, output on a `\d` line
2. Process remaining alignments using `english_text`, output on the `\v` line as normal
3. Both sections share the same `hebrew_words` array

### Automatic Inter-verse Markers

The script automatically detects and preserves inter-verse markers from the source ULT file, including:
- `\qa <text>` (acrostic headings, e.g., `\qa Nun`)
- `\ts\*` (text section breaks)
- `\s1 <text>`, `\s2 <text>` (section headings)
- `\b` (blank line markers)
- `\d <text>` (superscriptions, when not using `d_text` for aligned output)
- `\d` (empty superscription paragraph marker, when superscription is part of `\v 1`)
- `\cl <text>` (chapter labels)

These markers are inserted on their own lines before the verse they precede. No manual insertion is needed.

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
grep -A 20 "\\\\v 1$" data/hebrew_bible/01-GEN.usfm | head -20
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

After saving JSON files, validate them with the validation script:

```bash
python3 .claude/skills/utilities/scripts/validate_alignment_json.py \
  /path/to/alignments/*.json
```

This checks that every Hebrew index is aligned, every English word appears exactly once, and required fields are present.

### Step 6: Save JSON

Write to scratchpad or output directory:

```
/tmp/claude-*/scratchpad/alignments/GEN-01-01.json
```

### Step 7: Verify Text Preservation

After generating aligned USFM, verify the English text is preserved exactly. This requires two checks since the extraction script strips USFM markers:

**Part A: Verify English text and word order**

Extract English from the aligned output and compare with the original unaligned ULT:

```bash
# Extract English from aligned output
python3 .claude/skills/utilities/scripts/extract_ult_english.py \
  --input-dir output/AI-ULT/{BOOK} \
  --output-dir /tmp/verify-alignment \
  --force

# Compare extracted text with original unaligned ULT
diff <(cat /tmp/verify-alignment/{BOOK}.usfm) <(cat output/AI-ULT/{BOOK}/{BOOK}-unaligned.usfm)
```

The extracted text should match exactly - same words, same order, same punctuation.

**Part B: Verify USFM marker placement**

Since the extraction script removes USFM markers (\q1, \q2, \v, etc.), verify marker placement separately:

```bash
# Extract USFM markers from aligned output
grep -oE '\\(q[12]|v [0-9]+|p|s[0-9]?)' aligned.usfm | sort > /tmp/aligned_markers.txt

# Extract markers from original unaligned ULT
grep -oE '\\(q[12]|v [0-9]+|p|s[0-9]?)' original.usfm | sort > /tmp/original_markers.txt

# Compare - should be identical
diff /tmp/aligned_markers.txt /tmp/original_markers.txt
```

Both comparisons should show no differences. If there are differences, the alignment process has altered the text and must be corrected.

## Conversion to Aligned USFM

After creating the mapping JSON, run the conversion script:

```bash
node .claude/skills/utilities/scripts/usfm/create_aligned_usfm.js \
  --hebrew data/hebrew_bible/01-GEN.usfm \
  --mapping /tmp/alignments/GEN-01-01.json \
  --ult output/AI-ULT/GEN/GEN-01.usfm \
  --chapter 1 --verse 1
```

The script:
1. Reads Hebrew USFM to get full word metadata (Strong's, lemma, morph, x-content)
2. Reads your mapping JSON
3. Parses `english_text` to determine correct word order
4. Outputs each English word individually in `english_text` order
5. Wraps each word in its Hebrew alignment milestone (`\zaln-s`, `\zaln-e`, `\w`)
6. Tracks word occurrences (`x-occurrence`, `x-occurrences` attributes)

### Output Structure

Each English word gets its own alignment milestone:
```
\zaln-s |x-strong="H1234" x-lemma="..." x-occurrence="1" x-occurrences="1" x-content="הַמֶּלֶךְ"\*\w the|x-occurrence="1" x-occurrences="3"\w*\zaln-e\*
\zaln-s |x-strong="H1234" x-lemma="..." x-occurrence="1" x-occurrences="1" x-content="הַמֶּלֶךְ"\*\w king|x-occurrence="1" x-occurrences="1"\w*\zaln-e\*
```

For duplicate English words (e.g., "the" appearing 3 times), each gets sequential occurrence numbers:
- First "the": `x-occurrence="1" x-occurrences="3"`
- Second "the": `x-occurrence="2" x-occurrences="3"`
- Third "the": `x-occurrence="3" x-occurrences="3"`

## Final Output

After converting all verses, save the combined aligned USFM to `output/AI-ULT/{BOOK}/`.

### Combining Multiple Verses

The script outputs **multi-line USFM** (one line per word/alignment). When combining verses:

```bash
# Create header
cat > output/AI-ULT/PSA/PSA-078-44-72-aligned.usfm << 'EOF'
\id PSA EN_ULT - Aligned
\usfm 3.0
\ide UTF-8
\h Psalms
\mt Psalms

\c 78
EOF

# Append each verse (--ult preserves poetry markers, inter-verse markers, and \d lines)
for v in $(seq 44 72); do
  vpad=$(printf "%03d" $v)
  node .claude/skills/utilities/scripts/usfm/create_aligned_usfm.js \
    --hebrew data/hebrew_bible/19-PSA.usfm \
    --mapping alignments/PSA-078-${vpad}.json \
    --ult output/AI-ULT/PSA/PSA-078-44-72.usfm \
    --chapter 78 --verse $v 2>/dev/null | sed -n '/^\\[vqdstb]/,/^$/p' >> output/AI-ULT/PSA/PSA-078-44-72-aligned.usfm
done
```

**Notes:**
- Use `sed -n '/^\\[vqdstb]/,/^$/p'` to capture verse line, inter-verse markers (`\qa`, `\ts\*`, `\d`, `\s1`, `\b`), and all alignment lines until blank
- Do NOT use `grep "^\v"` - this only gets the first line and truncates alignments
- Use zero-padded verse numbers in mapping filenames (e.g., `PSA-078-044.json`)
- Inter-verse markers (`\qa`, `\ts\*`, `\s1`, `\b`, etc.) and aligned `\d` lines are inserted automatically by the script -- no manual insertion needed

### Naming Convention

```
{BOOK}-{CHAPTER}-aligned.usfm              # whole chapter
{BOOK}-{CHAPTER}-{START}-{END}-aligned.usfm  # partial chapter
```

Examples:
- `output/AI-ULT/PSA/PSA-078-aligned.usfm` (whole chapter)
- `output/AI-ULT/PSA/PSA-078-44-72-aligned.usfm` (verses 44-72 only)
- `output/AI-ULT/GEN/GEN-01-aligned.usfm` (whole chapter)

Use zero-padded chapter numbers: 3 digits for Psalms (150 chapters), 2 digits for all other books.

### Convert to Curly Quotes

After creating the final aligned USFM, run the curly quotes script:

```bash
python3 .claude/skills/utilities/scripts/curly_quotes.py \
  output/AI-ULT/{BOOK}/{BOOK}-{CHAPTER}-aligned.usfm --in-place
```

This converts:
- Straight double quotes `"..."` to curly `"..."`
- Straight single quotes/apostrophes `'...'` to curly `'...'`

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
- [ ] `english_text` contains the exact English translation with correct word order
- [ ] Hebrew words copied exactly from source (not typed manually)

### Verifying Output (Critical)

Use Step 7's two-part verification to ensure the aligned output perfectly preserves the original text:

1. **Text verification** - Extract English from aligned USFM using `extract_ult_english.py` and diff against original unaligned ULT
2. **USFM marker verification** - Compare USFM markers (\q1, \q2, \v, etc.) between aligned and original

Both must match exactly. Any differences indicate the alignment process altered the text and must be corrected before finalizing.

Quick single-verse check:
```bash
# Extract words from aligned output
grep -oE '\\w [^|]+\|' aligned.usfm | sed 's/\\w //;s/|//' | tr '\n' ' '

# Should match original ULT text word-for-word
```

## Related Skills

- [ULT-gen](../ULT-gen/SKILL.md) - Create the English ULT text
- [Pipeline Overview](../pipeline-overview/SKILL.md) - Where alignment fits in workflow

## Reference

See `reference/alignment_rules.md` for detailed alignment rules.
