---
name: UST-alignment

description: Create meaning-based alignments between Hebrew source and English UST text. Handles radical restructuring and implied information. Use when asked to align UST or produce aligned UST USFM.

allowed-tools: Read, Grep, Glob, Bash
---

## Overview

This skill maps English UST phrases to Hebrew source words. The workflow is two-step:
1. **AI creates** an index-based mapping (English phrases to Hebrew word positions)
2. **Script converts** that mapping to properly formatted aligned USFM

UST alignment is fundamentally different from ULT alignment. Where ULT aims for word-level precision, UST shows which Hebrew word(s) contribute meaning to each English phrase. The mapping is concept-to-phrase, not word-to-word.

## Input Requirements

You need:
1. **Hebrew USFM** from `data/hebrew_bible/*.usfm` - contains Strong's numbers, lemmas, morphology
2. **English UST text** - from `output/AI-UST/` or user-provided

## Using Alignment Hints

If `output/AI-UST/hints/<BOOK>-<CH>.json` exists, read it first. These hints are a rough mapping from the UST generator showing which Hebrew words contributed to each English phrase. The generator wrote them while the translation decisions were fresh, so they capture the "why" behind each phrase.

Use hints as your starting point:
- Refine phrase boundaries (split large groups where meaning can be divided)
- Handle split alignments (same Hebrew index appearing in multiple entries)
- Verify against Hebrew source -- the hints are approximate, not authoritative
- Entries with `"implied": true` correspond to bracketed content with `hebrew_indices: []`

The hints give you the translator's intent. You provide the precision.

## Output Format: Simple Mapping JSON

Same JSON structure as ULT alignment:

```json
{
  "reference": "PSA 1:1",
  "hebrew_words": [
    {"index": 0, "word": "אַ֥שְֽׁרֵי", "strong": "H0835", "lemma": "אֶשֶׁר"},
    {"index": 1, "word": "הָ⁠אִ֗ישׁ", "strong": "d:H0376", "lemma": "אִישׁ"},
    {"index": 2, "word": "אֲשֶׁ֤ר", "strong": "H0834a", "lemma": "אֲשֶׁר"},
    {"index": 3, "word": "לֹ֥א", "strong": "H3808", "lemma": "לֹא"},
    {"index": 4, "word": "הָלַךְ֮", "strong": "H1980", "lemma": "הָלַךְ"},
    {"index": 5, "word": "בַּ⁠עֲצַ֪ת", "strong": "b:H6098", "lemma": "עֵצָה"},
    {"index": 6, "word": "רְשָׁ֫עִ֥ים", "strong": "H7563", "lemma": "רָשָׁע"}
  ],
  "english_text": "The person who will have a truly good life is the person who does not do what evil people tell him to do,",
  "alignments": [
    {"hebrew_indices": [1], "english": ["The", "person", "who", "will", "have", "a", "truly", "good", "life"]},
    {"hebrew_indices": [0], "english": ["is", "the", "person"]},
    {"hebrew_indices": [2], "english": ["who"]},
    {"hebrew_indices": [3, 4, 5, 6], "english": ["does", "not", "do", "what", "evil", "people", "tell", "him", "to", "do,"]}
  ]
}
```

### Key Differences from ULT

| Aspect | ULT | UST |
|--------|-----|-----|
| English arrays | 1-3 words typical | 5-15 words common |
| Hebrew indices | Usually 1 per entry | Often 3-5 per entry |
| Split alignment | Rare | Common (same Hebrew index in multiple entries) |
| `{brackets}` | Grammar additions | Implied information |
| `hebrew_indices: []` | Not used | Used for purely implied info |
| Alignment granularity | Word-level | Phrase-level |

### Key Fields

| Field | Description |
|-------|-------------|
| `reference` | Book chapter:verse (e.g., "PSA 1:1") |
| `hebrew_words` | Array of Hebrew words with index, word form, Strong's, lemma |
| `english_text` | Complete English UST translation - **authoritative word order** |
| `alignments` | Array mapping Hebrew indices to English word arrays |
| `d_text` | (Optional) Superscription text for `\d` line |

### Alignment Entry Structure

- `hebrew_indices`: Array of Hebrew word indices (0-based)
  - Multiple indices `[3, 4, 5, 6]` for meaning groups (very common in UST)
  - Empty `[]` for purely implied information with no Hebrew correspondent
  - Same index may appear in multiple entries (split alignment)
- `english`: Array of English words that render this Hebrew meaning
  - `{word}` for implied information
- `section`: (Optional) Set to `"d"` for superscription entries

### Superscription Alignment

There are two cases depending on how the UST source structures the superscription:

#### Case 1: Superscription is part of verse 1 (e.g., Psalms 120-134)

When the UST source has the superscription inside `\v 1` (with an empty `\d` marker):
```
\d
\v 1 A song of ascents.
\q1 Yahweh, remember David
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
  "english_text": "A song of ascents. Yahweh, remember David and all of the difficulties that he had.",
  "alignments": [
    {"hebrew_indices": [0], "english": ["A", "song"]},
    {"hebrew_indices": [1], "english": ["of", "ascents."]},
    {"hebrew_indices": [2], "english": ["remember"]},
    {"hebrew_indices": [3], "english": ["Yahweh"]}
  ]
}
```

The script picks up the empty `\d` and `\q1`/`\q2` markers from the UST source file automatically.

#### Case 2: Superscription on `\d` line, separate from verse 1 (`d_text` and `section`)

When the UST source has the superscription text on the `\d` line (Hebrew v1 is only superscription, body starts at Hebrew v2 mapped to English v1):
```
\d This is for the chief musician. It is a psalm of David.
\v 1 All the people on the earth, shout joyfully to God!
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
  "d_text": "This is for the chief musician. It is a psalm of David.",
  "english_text": "All the people on the earth, shout joyfully to God!",
  "alignments": [
    {"hebrew_indices": [0], "english": ["for", "the", "chief", "musician."], "section": "d"},
    {"hebrew_indices": [1], "english": ["a"], "section": "d"},
    {"hebrew_indices": [2], "english": ["a", "psalm", "of", "David."], "section": "d"},
    {"hebrew_indices": [3], "english": ["shout", "joyfully"]},
    {"hebrew_indices": [4], "english": ["to", "God"]},
    {"hebrew_indices": [5], "english": ["All", "the"]},
    {"hebrew_indices": [6], "english": ["people", "on", "the", "earth"]}
  ]
}
```

### Critical: `english_text` Controls Output Word Order

The `english_text` field is **authoritative** for the final output word order, just as with ULT. Alignment array order doesn't matter.

### Bracket Handling

Brackets in UST mark implied information -- content not directly present in the Hebrew but added for clarity. There are two categories:

1. **Implied info connected to Hebrew**: `{word}` + `hebrew_indices: [N]`
   - The implied content relates to a specific Hebrew word
   - Example: `{when Yahweh}` linked to the Hebrew word for "judgment"

2. **Purely implied info**: `{word}` + `hebrew_indices: []`
   - No Hebrew correspondent at all
   - Example: `{It seems like}` with no Hebrew source

Brackets are **pre-determined** by the UST-gen skill. The alignment skill preserves them; it does not add or remove brackets.

## Alignment Principles

### 1. Meaning Groups Over Word-Level Precision

Group Hebrew words that collectively produce a single English phrase. "Smaller" in UST context means phrase-level, not word-level.

**Typical UST alignment:**
```json
{"hebrew_indices": [3, 4, 5, 6], "english": ["does", "not", "do", "what", "evil", "people", "tell", "him", "to", "do,"]}
```

This groups a negation + verb + preposition-noun + adjective because the UST restructures them into a single clause.

### 2. Smaller Groups Still Preferred When Possible

Only merge Hebrew words when the meaning genuinely cannot be divided:

**Good -- separated when meaning allows:**
```json
{"hebrew_indices": [1], "english": ["wicked", "people"]},
{"hebrew_indices": [2], "english": ["are", "like"]}
```

**Avoid -- unnecessarily large groups:**
```json
{"hebrew_indices": [1, 2, 3, 4], "english": ["wicked", "people", "are", "like", "chaff", "..."]}
```

### 3. Split Alignment

Same Hebrew index in multiple entries when meaning maps to non-contiguous English. Very common in UST:

```json
{"hebrew_indices": [5], "english": ["in", "what"]},
{"hebrew_indices": [6], "english": ["Yahweh"]},
{"hebrew_indices": [5], "english": ["teaches"]}
```

Here Hebrew `בְּ⁠תוֹרַ֥ת` (in-law-of) splits to "in what...teaches" because UST restructures "in the law of Yahweh" to "in what Yahweh teaches."

### 4. Implied Information

Brackets from UST-gen are preserved:
- `{word}` + `hebrew_indices: [N]` = implied info connected to specific Hebrew
- `{word}` + `hebrew_indices: []` = purely implied, no Hebrew correspondent

### 5. Hebrew Coverage

Not every Hebrew index must appear. Some Hebrew words may be unaligned when:
- Direct object marker (את) without vav is not rendered (though typically it gets grouped)
- A Hebrew particle has no meaning correspondence in the UST

The validation script in `--ust` mode allows unaligned Hebrew indices.

## AI Workflow for UST Alignment

### Step 1: Extract Hebrew Words

Read the Hebrew USFM for the verse:
```bash
grep -A 20 "\\\\v 1$" data/hebrew_bible/19-PSA.usfm | head -20
```

Parse each `\w` tag to extract word form, Strong's number, lemma, and morphology.

### Step 2: Read UST Text

Read the UST text, noting any `{bracketed}` content. Each bracketed word will need `hebrew_indices` (either a specific index or `[]`).

### Step 3: Anchor on Names and Proper Nouns

Map proper nouns first -- these are direct 1:1 mappings:
- Yahweh, David, Moses, Jerusalem, etc.

### Step 4: Map Main Verbs

Find the English verb or clause that renders each Hebrew verb. In UST this often involves significant restructuring.

### Step 5: Map Nouns

Find English noun phrases that render Hebrew nouns. In UST, a single Hebrew noun may expand to a full clause.

### Step 6: Map Function Words

Prepositions, particles, conjunctions. These often get absorbed into larger phrase groups.

### Step 7: Handle Implied Information

Remaining `{bracketed}` English words that don't map to any Hebrew get `hebrew_indices: []`.

### Step 8: Verify Coverage

Every English word must appear in exactly one alignment entry. Run validation:

```bash
python3 .claude/skills/utilities/scripts/validate_alignment_json.py \
  --ust /path/to/alignments/*.json
```

### Step 9: Save JSON

Write to scratchpad or output directory:
```
/tmp/claude-*/scratchpad/alignments/PSA-001-001.json
```

## Conversion to Aligned USFM

After creating the mapping JSON, run the conversion script:

> **Critical:** `--source` MUST point to the **UST file** (`output/AI-UST/BOOK/...`). Never pass the ULT file here. If you pass the ULT file, the output will silently contain ULT English text and look structurally valid — the error will not be obvious.

```bash
node .claude/skills/utilities/scripts/usfm/create_aligned_usfm.js \
  --hebrew data/hebrew_bible/19-PSA.usfm \
  --mapping /tmp/alignments/PSA-001-001.json \
  --source output/AI-UST/PSA/PSA-001.usfm \
  --ust \
  --chapter 1 --verse 1
```

The `--ust` flag tells the script to:
- Place brackets outside milestones (not inside `\w` tags)
- Wrap contiguous bracket groups as a unit
- Use `EN_UST` in the header id tag

### Output Structure

In UST mode, brackets wrap milestone groups:

```
{\zaln-s |x-strong="H1234" ...\*\w when\w*
\w Yahweh\w*}\w judges\w*\zaln-e\*
```

vs ULT mode where brackets go inside `\w` tags:

```
\w {when}|...\w*
```

### Combining Multiple Verses

```bash
# Create header
cat > output/AI-UST/PSA/PSA-001-aligned.usfm << 'EOF'
\id PSA EN_UST - Aligned
\usfm 3.0
\ide UTF-8
\h Psalms
\mt Psalms

\c 1
EOF

# Append each verse
for v in $(seq 1 6); do
  vpad=$(printf "%03d" $v)
  node .claude/skills/utilities/scripts/usfm/create_aligned_usfm.js \
    --hebrew data/hebrew_bible/19-PSA.usfm \
    --mapping alignments/PSA-001-${vpad}.json \
    --source output/AI-UST/PSA/PSA-001.usfm \
    --ust \
    --chapter 1 --verse $v 2>/dev/null | sed -n '/^\\[vqdsb]\|^\\ts/,/^$/p' >> output/AI-UST/PSA/PSA-001-aligned.usfm
done
```

### Naming Convention

```
output/AI-UST/{BOOK}/{BOOK}-{CHAPTER}-aligned.usfm              # whole chapter
output/AI-UST/{BOOK}/{BOOK}-{CHAPTER}-{START}-{END}-aligned.usfm  # partial chapter
```

### Convert to Curly Quotes

After creating the final aligned USFM:

```bash
python3 .claude/skills/utilities/scripts/curly_quotes.py \
  output/AI-UST/{BOOK}/{BOOK}-{CHAPTER}-aligned.usfm --in-place
```

## Verification

### Step 0: Verify UST text differs from ULT (mandatory)

Before anything else, confirm the aligned UST contains different English than the aligned ULT. If these are the same, the alignment was run against the ULT source — discard and redo.

```bash
# Extract English words from both aligned files and compare
BOOK=HOS; CH=01
diff \
  <(grep -oE '\\w [^|]+\|' output/AI-UST/$BOOK/$BOOK-$CH-aligned.usfm | sed 's/\\w //;s/|//') \
  <(grep -oE '\\w [^|]+\|' output/AI-ULT/$BOOK/$BOOK-$CH-aligned.usfm | sed 's/\\w //;s/|//') \
  > /dev/null && echo "ERROR: UST and ULT aligned text are identical — wrong --source file was used" || echo "OK: UST and ULT text differ as expected"
```

### Step 1: Verify English Text Preservation

```bash
# Extract English from aligned output
python3 .claude/skills/utilities/scripts/extract_ult_english.py \
  --input-dir output/AI-UST \
  --output-dir /tmp/verify-alignment \
  --force

# Compare extracted text with original unaligned UST
diff <(cat /tmp/verify-alignment/BOOK.usfm) <(cat output/AI-UST/BOOK/BOOK-unaligned.usfm)
```

### Step 2: Verify Bracket Placement

In UST mode, brackets should appear OUTSIDE milestones:
```
{\zaln-s ...\*\w word\w*...\zaln-e\*}    # correct (UST)
\zaln-s ...\*{word}\zaln-e\*             # wrong (ULT style)
```

Quick check:
```bash
grep -oE '\\w [^|]+\|' aligned.usfm | sed 's/\\w //;s/|//' | tr '\n' ' '
```

## Quality Checklist

Before finalizing alignment JSON:

- [ ] Every English word appears exactly once across all alignments
- [ ] Bracketed words from UST-gen preserved correctly in alignment entries
- [ ] No over-merging (prefer smaller groups when meaning can be divided)
- [ ] Split alignments used where Hebrew meaning maps to non-adjacent English
- [ ] `hebrew_indices: []` used only for purely implied info (no Hebrew source)
- [ ] `english_text` contains the exact English UST text with correct word order
- [ ] Hebrew words copied exactly from source (not typed manually)
- [ ] Names and proper nouns mapped 1:1 where possible

## Gemini Review (optional, activation only)

After validation, run Gemini as an independent reviewer. Only run if `--gemini` is explicitly passed. Skip by default.

```bash
python3 .claude/skills/utilities/scripts/gemini_review.py --stage alignment-ust --book <BOOK> --chapter <CHAPTER>
```

1. If exit code 2 (Gemini failed/rate-limited): log and continue
2. If exit code 0: no findings, continue
3. If exit code 1: read `output/review/<BOOK>/<BOOK>-<CH>-alignment-ust-gemini.md`
4. For each finding: check against ust_alignment_rules.md. If legit, fix the alignment. If false positive, ignore.

## Related Skills

- [UST-gen](../UST-gen/SKILL.md) - Create the English UST text
- [ULT-alignment](../ULT-alignment/SKILL.md) - Word-level ULT alignment (different approach)
- [Pipeline Overview](../pipeline-overview/SKILL.md) - Where alignment fits in workflow

## Reference

See `reference/ust_alignment_rules.md` for detailed alignment rules and pattern catalog.
