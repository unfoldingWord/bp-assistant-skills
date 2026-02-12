---
name: tn-writer
description: Generate translation notes from issue identification TSV. Runs deterministic preparation script then AI generates notes following the style guide.
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
    --aligned-usfm output/AI-ULT/<BOOK>-<CHAPTER>-aligned.usfm \
    --output /tmp/claude/prepared_notes.json
```

This produces a JSON file with fully-assembled prompts for each item.

The script automatically:
- Filters out items with "has tW article" in the explanation (Translation Words already covers them)
- Sorts output so `front` references come before verse references

Options:
- `--aligned-usfm PATH` -- Extract Hebrew quotes directly from aligned ULT (preferred; bypasses lang_convert.js roundtrip and eliminates QUOTE_NOT_FOUND from ULT version mismatch). Auto-detected if omitted and aligned file exists at the standard path.
- `--skip-lang` -- Skip language conversion (keep original English quotes)
- `--skip-ids` -- Skip ID generation

### Step 3: Verify Roundtrip Alignment

After prepare_notes.py runs (which roundtrips gl_quotes internally), verify the results before investing in note generation. Check each item's `gl_quote` vs `gl_quote_roundtripped` in the prepared JSON. If they differ, the original gl_quote may not align cleanly to Hebrew words -- investigate before proceeding.

```bash
python3 -c "
import json
with open('/tmp/claude/prepared_notes.json') as f:
    data = json.load(f)
diffs = [(i['id'], i['reference'], i['gl_quote'], i['gl_quote_roundtripped'])
         for i in data['items']
         if i['gl_quote'].strip().lower() != i['gl_quote_roundtripped'].strip().lower()]
if diffs:
    print(f'{len(diffs)} roundtrip discrepancies:')
    for d in diffs:
        print(f'  {d[0]} {d[1]}: \"{d[2]}\" -> \"{d[3]}\"')
else:
    print('All gl_quotes roundtrip cleanly.')
"
```

Review any discrepancies. Minor differences (capitalization, whitespace) are usually fine. If a gl_quote roundtrips to something substantially different, the Hebrew alignment may be off -- check the original quote against the ULT verse and fix before continuing.

### Step 4: Flag Narrow Quotes

Run the narrow-quote flagger against the prepared JSON:

```bash
python3 .claude/skills/tn-writer/scripts/flag_narrow_quotes.py \
    /tmp/claude/prepared_notes.json
```

Review flagged items. These quotes are correct for focusing the note body on the issue, but may need wider phrase boundaries for AT fit later. Keep this list in mind during note generation -- write initial ATs that anticipate the surrounding phrase context.

### Step 5: Read the Style Guide

Read `reference/note-style-guide.md` for the note writing rules.

### Step 6: Generate Notes (write keyed JSON, not TSV)

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
   - For items flagged as narrow in Step 4: the narrow gl_quote is still correct in the prompt (it focuses the note body on the issue). But write the initial AT with the surrounding phrase context in mind, since the quote boundary may be expanded for AT fit in Step 7.

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

### Step 7: Expand Narrow Quotes and AT Fit Check (iterative)

Run the verification script to see all substitutions:

```bash
python3 .claude/skills/tn-writer/scripts/verify_at_fit.py \
    /tmp/claude/prepared_notes.json \
    /tmp/claude/generated_notes.json
```

Read the full stdout -- every substitution line is the review, not just the error summary at the end.

For each substitution that reads unnaturally (broken grammar, orphaned words, verb agreement issues):

1. **Expand the gl_quote** to a wider phrase boundary in the ULT verse. For example, if `distress` sits inside "in my distress", expand the quote to `in my distress`.

2. **Roundtrip the expanded quote** to verify Hebrew alignment. Build a one-row TSV with the expanded quote and run:
   ```bash
   echo -e "Reference\tID\tTags\tQuote\tOccurrence\tNote\n<REF>\t\t<SREF>\t<EXPANDED_QUOTE>\t1\t" | \
       node .claude/skills/tn-writer/scripts/lang_convert.js roundtrip unfoldingWord/en_ult/master <BOOK> -
   ```
   Verify the roundtripped OrigQuote has Hebrew content and the GLQuote matches.

3. **Update prepared_notes.json** -- set `gl_quote`, `gl_quote_roundtripped`, and `orig_quote` for the expanded item.

4. **Rewrite the AT** in `generated_notes.json` to fit the expanded quote boundary. The AT should now be a seamless replacement for the wider phrase.

5. **Re-run verify_at_fit.py**. Repeat until every substitution reads as natural English.

Do not proceed to assembly until every substitution line has been reviewed and reads correctly.

Also check:
- Fix any ERRORS (gl_quote not found -- usually a curly brace or case issue)
- Watch for prepositions/conjunctions adjacent to the gl_quote that may need inclusion in the AT (Hebrew prefixes like bet/lamed/mem often correspond to English "to/in/from" outside the gl_quote)
- Verify no AT is identical to UST phrasing

### Step 8: Assemble Output TSV (script)

Run the assembly script to produce the final TSV. The script reads metadata from the prepared JSON and note text from the generated JSON, matching by ID. This prevents note/row misalignment.

```bash
python3 .claude/skills/tn-writer/scripts/assemble_notes.py \
    /tmp/claude/prepared_notes.json \
    /tmp/claude/generated_notes.json \
    --output output/notes/<BOOK>-<CHAPTER>.tsv
```

### Step 9: Post-Process

Run curly quote conversion on the output:

```bash
python3 .claude/skills/utilities/scripts/curly_quotes.py output/notes/<BOOK>-<CHAPTER>.tsv --in-place
```

### Step 10: Final Review

Read the assembled TSV alongside the aligned ULT. For each row, verify:

1. **Quote column** is non-empty and contains Hebrew text
2. **Note text** addresses the issue type indicated by SupportReference
3. **AT fit** -- if an Alternate Translation is present, mentally substitute it for the GLQuote in the ULT verse and confirm it reads naturally
4. **Quote scope** -- the Hebrew quote covers the right range (not too narrow or too wide for the issue)
5. **No duplicate UST phrasing** -- ATs should differ from the UST for the same verse

Fix any issues found and rewrite the TSV row(s) if needed. This is a lightweight review pass, not a regeneration -- just catch structural problems the scripts can't judge.

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
