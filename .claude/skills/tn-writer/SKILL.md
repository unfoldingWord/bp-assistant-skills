---
name: tn-writer
description: Generate translation notes from issue identification TSV. Runs deterministic preparation script then AI generates notes following the style guide.
model: sonnet
---

# Translation Note Writer

Generate translation notes from issue identification output. A preparation script handles all deterministic work (template matching, language conversion, ID generation, prompt assembly), then Claude generates the note text.

## Prerequisites

- Input TSV in `output/issues/` (from issue-identification)
- Plain ULT and UST USFM files (from issue-identification or fetched fresh)
- `tsv-quote-converters` built at `/home/bmw/Documents/dev/tsv-quote-converters/`

## Workflow

### Step 1: Ensure ULT/UST USFM Files Exist

The issue-identification agent usually leaves these at `/tmp/ult_plain.usfm` and `/tmp/ust_plain.usfm`. If they do not exist, fetch them:

```bash
python3 .claude/skills/utilities/scripts/fetch_door43.py <BOOK> --output /tmp/claude/book_ult.usfm
python3 .claude/skills/utilities/scripts/fetch_door43.py <BOOK> --type ust --output /tmp/claude/book_ust.usfm
node .claude/skills/utilities/scripts/usfm/parse_usfm.js /tmp/claude/book_ult.usfm --plain-only > /tmp/claude/ult_plain.usfm
node .claude/skills/utilities/scripts/usfm/parse_usfm.js /tmp/claude/book_ust.usfm --plain-only > /tmp/claude/ust_plain.usfm
```

### Step 2: Run the Preparation Script

```bash
python3 .claude/skills/tn-writer/scripts/prepare_notes.py \
    output/issues/<BOOK>-<CHAPTER>.tsv \
    --ult-usfm /tmp/claude/ult_plain.usfm \
    --ust-usfm /tmp/claude/ust_plain.usfm \
    --output /tmp/claude/prepared_notes.json
```

This produces a JSON file with fully-assembled prompts for each item.

The script automatically:
- Filters out items with "has tW article" in the explanation (Translation Words already covers them)
- Sorts output so `front` references come before verse references

Options:
- `--skip-lang` -- Skip language conversion (keep original English quotes)
- `--skip-ids` -- Skip ID generation

### Step 3: Read the Style Guide

Read `reference/note-style-guide.md` for the note writing rules.

### Step 4: Generate Notes (write keyed JSON, not TSV)

Read `/tmp/claude/prepared_notes.json`. For each item, generate a note and write it to a JSON object keyed by the item's `id`. Write the result to `/tmp/claude/generated_notes.json`.

Process one item at a time:

1. Read the `system_prompt_key` field to know which persona to use:
   - `ai_writes_at_agent` -- Generate the note AND an alternate translation
   - `given_at_agent` -- Generate the note only (AT already provided or not needed)

2. Read the `prompt` field -- it contains all context (templates, verse text, explanation). Generate the note following the style guide.

3. For items with `needs_at: true`:
   - Place the AT at the end of the note: `Alternate translation: [text here]`
   - Use square brackets, not quotes, around the AT text
   - The AT must fit seamlessly: removing `gl_quote` from `ult_verse` and inserting the AT should read as natural English
   - The AT must differ from the UST phrasing in `ust_verse`
   - Use minimal changes to the ULT wording; only change what the translation issue requires

4. For items with `tcm_mode: true`:
   - Present multiple interpretations using the "This could mean:" format
   - Each interpretation gets its own AT in square brackets

Output format -- a flat JSON object mapping item ID to note text:
```json
{
  "em7t": "A **chief musician** is a person who...",
  "dcc8": "A **stringed instrument** is a type of...",
  ...
}
```

Write this to `/tmp/claude/generated_notes.json`. Do NOT assemble the TSV yourself -- the assembly script handles that to prevent row misalignment.

### Step 5: AT Fit Check

For each generated note that contains an alternate translation (text in `[square brackets]`):

1. Extract the AT text from the note
2. Take the `gl_quote_roundtripped` value (or `gl_quote` if no roundtrip)
3. In the `ult_verse`, replace the GLQuote with the AT
4. Check: does the substituted verse read as natural English?
5. If not, adjust the AT (or expand the GLQuote if the AT needs more surrounding text)
6. Verify the AT is not identical to UST phrasing
7. Update the entry in `/tmp/claude/generated_notes.json` if changes were needed

### Step 6: Assemble Output TSV (script)

Run the assembly script to produce the final TSV. The script reads metadata from the prepared JSON and note text from the generated JSON, matching by ID. This prevents note/row misalignment.

```bash
python3 .claude/skills/tn-writer/scripts/assemble_notes.py \
    /tmp/claude/prepared_notes.json \
    /tmp/claude/generated_notes.json \
    --output output/notes/<BOOK>-<CHAPTER>.tsv
```

### Step 7: Post-Process

Run curly quote conversion on the output:

```bash
python3 .claude/skills/utilities/scripts/curly_quotes.py output/notes/<BOOK>-<CHAPTER>.tsv --in-place
```

## Input Format

Issue TSV (no headers, 7 columns):
```
PSA	65:1	figs-abstractnouns	Praise			abstract noun - could be expressed as verb
```

Columns: Book, Reference, SRef, GLQuote, Go?, AT, Explanation

## Output Format

TN-ready TSV (7 columns with headers):
```
Reference	ID	Tags	SupportReference	Quote	Occurrence	Note
65:1	a1b2		rc://*/ta/man/translate/figs-abstractnouns	[Hebrew]	1	[generated note]
```

## Note Types

| Type | Condition | What happens |
|------|-----------|--------------|
| `writes_at` | No AT provided, templates have AT section | Generate note + AT |
| `given_at` | AT already provided | Generate note only |
| `see_how_at` | Explanation starts with "see how", no AT | Generate AT only |
| `see_how` | Explanation starts with "see how", has AT | Generate note with given AT |

## Special Modes

### TCM (This Could Mean)
When explanation starts with "TCM", present multiple interpretations:
"This could mean: (1) [interpretation]. Alternate translation: [AT] or (2) [interpretation]. Alternate translation: [AT]"

### i: prefix
Information that must be included in the note. May reference other verses.

### t: prefix
Hint about which template variant to use.
