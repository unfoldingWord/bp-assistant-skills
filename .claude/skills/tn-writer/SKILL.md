---
name: tn-writer
description: Generate translation notes from issue identification TSV. Uses prompt-over-code: scripts handle mechanical extraction, prompts handle semantic content. Use when asked to write translation notes, create TN from issues, or generate notes for a chapter.
---

# Translation Note Writer

Generate translation notes from issue identification output. A preparation script handles all deterministic work (template matching, language conversion, ID generation, prompt assembly), then Claude generates the note text.

## Prerequisites

- Input TSV in `output/issues/` (from issue-identification)
- Plain ULT and UST USFM files (from issue-identification or fetched fresh)
- The tsv-quote-converters tool (path resolved automatically by the script)

## Workflow

### Step 1: Ensure ULT/UST USFM Files Exist

The issue-identification agent usually leaves these at `/tmp/ult_plain.usfm` and `/tmp/ust_plain.usfm`. If they do not exist, fetch them:

```bash
python3 .claude/skills/utilities/scripts/fetch_door43.py <BOOK> --output /tmp/claude/book_ult.usfm
python3 .claude/skills/utilities/scripts/fetch_door43.py <BOOK> --type ust --output /tmp/claude/book_ust.usfm
node .claude/skills/utilities/scripts/usfm/parse_usfm.js /tmp/claude/book_ult.usfm --plain-only > /tmp/claude/ult_plain.usfm
node .claude/skills/utilities/scripts/usfm/parse_usfm.js /tmp/claude/book_ust.usfm --plain-only > /tmp/claude/ust_plain.usfm
```

### Step 2a: Run the Preparation Script

```bash
python3 .claude/skills/tn-writer/scripts/prepare_notes.py \
    output/issues/<BOOK>/<BOOK>-<CHAPTER>.tsv \
    --ult-usfm /tmp/claude/ult_plain.usfm \
    --ust-usfm /tmp/claude/ust_plain.usfm \
    --aligned-usfm output/AI-ULT/<BOOK>/<BOOK>-<CHAPTER>-aligned.usfm \
    --output /tmp/claude/prepared_notes.json
```

This produces a JSON file with fully-assembled prompts for each item, plus alignment data at `/tmp/claude/alignment_data.json`.

The script automatically:
- Filters out items with "has tW article" in the explanation (Translation Words already covers them)
- Sorts output so `front` references come before verse references
- Extracts alignment data (English-to-Hebrew word mappings) from aligned USFM

Options:
- `--aligned-usfm PATH` -- Extract alignment data from aligned ULT (preferred). Auto-detected if omitted and aligned file exists at the standard path (`output/AI-ULT/<BOOK>/<BOOK>-<CHAPTER>-aligned.usfm`).
- `--alignment-json PATH` -- Custom output path for alignment data (default: `/tmp/claude/alignment_data.json`)
- `--skip-lang` -- Skip language conversion (keep original English quotes)
- `--skip-ids` -- Skip ID generation

Note: `orig_quote` fields in the prepared JSON will be empty when using aligned USFM. Hebrew quotes are filled in Step 2c below.

### Step 2b: Review Alignment Data

Read the alignment data JSON to understand the English-to-Hebrew word mappings:

```bash
python3 -c "
import json
with open('/tmp/claude/alignment_data.json') as f:
    data = json.load(f)
print(f'{len(data)} verses with alignment data')
for ref in sorted(data.keys(), key=lambda r: (int(r.split(\":\")[0]), int(r.split(\":\")[1]) if r.split(\":\")[1] != \"front\" else 0))[:3]:
    print(f'  {ref}: {len(data[ref])} aligned words')
    for w in data[ref][:5]:
        print(f'    {w[\"eng\"]} -> {w[\"heb\"]} (pos {w[\"heb_pos\"]})')
"
```

### Step 2c: Fill Hebrew Quotes (Claude Semantic Matching)

For each item in `/tmp/claude/prepared_notes.json` where `orig_quote` is empty:

1. Read the alignment data for the item's verse from `/tmp/claude/alignment_data.json`
2. Semantically identify which English aligned words correspond to the item's `gl_quote`
3. Collect the Hebrew `heb` values for those matched alignment entries
4. Read the Hebrew source verse from `data/hebrew_bible/*-<BOOK>.usfm` (find the `\c` and `\v` markers for the chapter:verse)
5. Order the collected Hebrew words to match their reading order in the Hebrew source verse
6. Verify EXACT Unicode match: each Hebrew word you collected must appear character-for-character as a `\w` token in the Hebrew source verse for that reference
7. Join the Hebrew words with spaces and update `orig_quote` in the prepared JSON

**CRITICAL**: You MUST copy Hebrew text character-for-character from the source file. Do not generate Hebrew from memory. Read the source, find the words, copy them exactly.

After filling all items, write the updated prepared JSON back to `/tmp/claude/prepared_notes.json`.

### Step 3: Verify Hebrew Quotes

After filling orig_quote values, verify each Hebrew quote is a valid substring of Hebrew source:

```bash
python3 -c "
import json
with open('/tmp/claude/prepared_notes.json') as f:
    data = json.load(f)
empty = [i for i in data['items'] if not i.get('orig_quote') and not i['reference'].endswith(':front')]
if empty:
    print(f'WARNING: {len(empty)} items still missing orig_quote:')
    for e in empty[:10]:
        print(f'  {e[\"id\"]} {e[\"reference\"]}: \"{e[\"gl_quote\"]}\"')
else:
    print(f'All {len(data[\"items\"])} items have orig_quote filled.')
"
```

Investigate any items still missing `orig_quote`. Common causes:
- The gl_quote doesn't match any words in the alignment data (check for typos)
- The aligned USFM is missing alignment for that verse

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

Process one item at a time. As you work through items, keep a mental map of interpretive commitments you have made (e.g., "in v9 I said inheritance = people"). When a note references or depends on a concept from a nearby verse, check that the interpretation is consistent with notes you already wrote. If you spot a conflict, resolve it before continuing -- adjust the current note or go back and revise the earlier one.

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
   - If the gl_quote boundary creates an orphaned preposition or conjunction, the preferred fix is to expand the gl_quote in Step 7, not to include the orphaned word only in the AT.
   - For restructuring issue types (figs-infostructure, grammar-connect-logic-goal, grammar-connect-logic-result, grammar-connect-condition-fact): if the note suggests reordering parts of the verse, ensure the gl_quote spans the full area being restructured. The AT must show the complete restructured text, not just a fragment.
   - For figs-parallelism: ensure the gl_quote captures both full parallel phrases, not just the key parallel terms. Check whether the parallelism involves ellipsis (words omitted in one phrase that are understood from the other) — if so, a separate figs-ellipsis note may be needed.

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

When reviewing each substitution line from verify_at_fit.py, check specifically:

1. **Orphaned conjunctions**: Is there a lonely "And", "But", "So", "Then"
   immediately before [the AT]? If yes, either:
   - Expand gl_quote to include the conjunction, OR
   - Rewrite the AT to include the conjunction

2. **Orphaned prepositions**: Is there a lonely "in", "to", "from", "by", "for",
   "with" before [the AT]? Same fix as above.

3. **Capitalization**: Does the first word of the AT match its sentence position?
   - Start of verse/sentence → capitalize
   - Mid-sentence → lowercase
   - Fix by rewriting the AT with correct case

4. **Read the full result sentence**: Does it parse as natural English? Watch for
   broken grammar at the boundaries.

5. **Restructuring scope**: For infostructure/logic notes (figs-infostructure, grammar-connect-logic-goal, grammar-connect-logic-result), verify the gl_quote and AT cover the full restructured area. If only a fragment is quoted, expand to include the complete reordering.

6. **Parallelism scope**: For parallelism notes (figs-parallelism), verify the gl_quote includes both entire parallel phrases. If only key words are quoted, expand to capture the full parallel structures.

Also check:
- Fix any ERRORS (gl_quote not found -- usually a curly brace or case issue)
- Verify no AT is identical to UST phrasing

### Step 8: Assemble Output TSV (script)

Run the assembly script to produce the final TSV. The script reads metadata from the prepared JSON and note text from the generated JSON, matching by ID. This prevents note/row misalignment.

```bash
python3 .claude/skills/tn-writer/scripts/assemble_notes.py \
    /tmp/claude/prepared_notes.json \
    /tmp/claude/generated_notes.json \
    --output output/notes/<BOOK>/<BOOK>-<CHAPTER>.tsv
```

### Step 9: Post-Process

Run curly quote conversion on the output:

```bash
python3 .claude/skills/utilities/scripts/curly_quotes.py output/notes/<BOOK>/<BOOK>-<CHAPTER>.tsv --in-place
```

### Step 10: Final Review

Read the assembled TSV alongside the aligned ULT. For each row, verify:

1. **Quote column** is non-empty and contains Hebrew text
2. **Note text** addresses the issue type indicated by SupportReference
3. **AT fit** -- if an Alternate Translation is present, mentally substitute it for the GLQuote in the ULT verse and confirm it reads naturally
4. **Quote scope** -- the Hebrew quote covers the right range (not too narrow or too wide for the issue)
5. **No duplicate UST phrasing** -- ATs should differ from the UST for the same verse

Fix any issues found and rewrite the TSV row(s) if needed. This is a lightweight review pass, not a regeneration -- just catch structural problems the scripts can't judge.

### Step 11: Deep Quality Check

Run the full quality-check suite inline so issues are caught and fixed before output.

#### 11a. Mechanical checks

```bash
python3 .claude/skills/tn-quality-check/scripts/check_tn_quality.py \
    output/notes/<BOOK>/<BOOK>-<CH>.tsv \
    --prepared-json /tmp/claude/prepared_notes.json \
    --ult-usfm /tmp/claude/ult_plain.usfm \
    --ust-usfm /tmp/claude/ust_plain.usfm \
    --book <BOOK> \
    --output /tmp/claude/tn_quality_findings.json
```

Read stderr for the summary and `/tmp/claude/tn_quality_findings.json` for full details. Fix every error (broken IDs, missing Hebrew quotes, bad AT syntax, rc:// links in note text, etc.).

#### 11b. Semantic review (checks 3a-3j)

Read the assembled TSV alongside the findings JSON. For each note, check the following — with emphasis on **3b** and **3j**:

- **3a. Correct issue type**: Note uses the right verbiage for its SupportReference figure of speech (see style guide).
- **3b. Template adherence**: Note follows the template shape for its issue type. Fixed phrases are preserved verbatim (e.g., figs-abstractnouns: "you could express the same idea in another way" — not "with a verb" or other drift). Flag notes that introduce non-template wording that subsequent notes repeat.
- **3c. AT naturalness**: Mentally substitute the AT for the gl_quote in the ULT verse. Check for broken grammar, orphaned words, verb agreement issues, dangling modifiers, or introduced punctuation.
- **3d. Antithetical parallelism**: If a `figs-parallelism` note covers two phrases expressing **opposite** ideas, flag it for removal (antithetical parallelism should not have a parallelism note).
- **3e. Note suppression**: If a semantic note (idiom, metaphor) overlaps a structural note (possession, activepassive) on the same phrase, flag the structural one as potentially redundant.
- **3f. Duplicate/combinable notes**: Flag notes in the same verse that overlap or could be merged.
- **3g. "Here" rule**: If a note starts with "Here, " verify the next content is a bolded lowercase quote.
- **3h. Restructuring quote scope**: For infostructure/logic notes, verify the gl_quote spans the full restructured area.
- **3i. Parallelism quote scope**: For figs-parallelism, verify the gl_quote includes both complete parallel phrases. Check for ellipsis needing a separate figs-ellipsis note.
- **3j. Cross-verse interpretive consistency**: Scan for notes that reference or depend on nearby verses:
  - Pronoun back-references: "it/they/this refers to X from verse N" — check verse N interprets X the same way.
  - Carried figures: A metaphor explained in one note must be interpreted consistently in later notes referencing the same image.
  - ATs across verses: If two notes address the same Hebrew word or referent, their ATs must be compatible (not "people" in one and "land" in the other for the same referent).

#### 11c. Fix issues

- For mechanical errors or semantic issues that can be fixed by editing note text: update `/tmp/claude/generated_notes.json` directly.
- For issues requiring quote boundary changes: update `/tmp/claude/prepared_notes.json` (gl_quote, orig_quote fields).
- After any changes, re-run assembly and post-processing:

```bash
python3 .claude/skills/tn-writer/scripts/assemble_notes.py \
    /tmp/claude/prepared_notes.json \
    /tmp/claude/generated_notes.json \
    --output output/notes/<BOOK>/<BOOK>-<CHAPTER>.tsv
python3 .claude/skills/utilities/scripts/curly_quotes.py output/notes/<BOOK>/<BOOK>-<CHAPTER>.tsv --in-place
```

- Re-run the mechanical checks to confirm fixes. Repeat until clean.

### Step 12: Gemini Review (optional, activation only)

Skip unless `--gemini` is explicitly passed.

```bash
python3 .claude/skills/utilities/scripts/gemini_review.py --stage notes --book <BOOK> --chapter <CHAPTER>
```

1. If exit code 2 (Gemini failed/rate-limited): log and continue
2. If exit code 0: no findings, continue
3. If exit code 1: read `output/review/<BOOK>/<BOOK>-<CH>-notes-gemini.md`
4. For each finding: check it against the note-style-guide and prompt-templates. If legit, fix the notes TSV. If false positive, ignore.

This is complementary to tn-quality-check -- Gemini does semantic/judgment review while the quality check script handles mechanical validation.

## Troubleshooting

- **Empty orig_quote after Step 2c**: The Hebrew quote extraction found no match. Check that the issue row's Book/Chapter/Verse matches the Hebrew USFM. Re-run with `--verbose` to see candidate matches.
- **verify_at_fit.py ERRORS**: The alignment token check failed. Common causes: stale ULT (re-fetch with fetch_door43.py), or orig_quote spans a verse boundary. Fix the quote and re-run verification.
- **assemble_notes.py missing items**: Rows were filtered out during assembly. Check that every row has a non-empty SupportReference and that the issue type matches a known TA article.
- **QUOTE_NOT_FOUND from lang_convert.js**: The Greek/Hebrew quote could not be located in the source text. Verify the quote is copied exactly from the USFM (including cantillation marks for Hebrew).

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
