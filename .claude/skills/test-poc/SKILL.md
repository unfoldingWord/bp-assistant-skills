---
name: test-poc
description: A/B test comparing prompt-over-code vs old script approaches for Hebrew quote extraction and AT fit.
allowed-tools: Read, Grep, Glob, Bash, Write, Edit
---

# Prompt-Over-Code A/B Test

Compare Claude's semantic Hebrew quote selection against old fuzzy-matching scripts, and validate AT fit on existing notes output.

## Usage

```
/test-poc                -- run both tests on default chapter (PSA 128)
/test-poc quote 125      -- Hebrew quote test only, on PSA 125
/test-poc at-fit         -- AT fit test only on existing output
/test-poc at-fit 130     -- AT fit test on PSA 130
```

Parse arguments from the skill invocation:
- First arg: test name (`quote`, `at-fit`, or omitted for both)
- Second arg: chapter number (default 128)

## Setup

### Resolve paths

1. **Data root**: Check for `data/hebrew_bible/` in this repo. If missing, try sibling `cSkillBP` repo (`../cSkillBP/`).
2. **Output root**: Check for `output/AI-ULT/` in this repo. If missing, try sibling `cSkillBP` repo.
3. Set file paths (where `{ch}` is the zero-padded chapter, e.g. `128`):
   - `ALIGNED` = `{output_root}/output/AI-ULT/PSA/PSA-{ch}-aligned.usfm`
   - `ISSUES` = `{output_root}/output/issues/PSA/PSA-{ch}.tsv`
   - `HEBREW` = `{data_root}/data/hebrew_bible/19-PSA.usfm`
4. Verify all required files exist. Abort with a clear message listing any missing files.
5. Ensure `/tmp/claude/` exists:
   ```bash
   mkdir -p /tmp/claude
   ```

## Test A: Hebrew Quote Selection

This is the main comparison. The old script uses fuzzy sliding-window matching to find Hebrew words. Claude uses semantic understanding of the English-to-Hebrew alignment data.

### Step 1 -- Run old script for baseline

```bash
python3 .claude/skills/tn-writer/scripts/.old/extract_quotes_from_alignment.py \
    {ALIGNED} {ISSUES} --output /tmp/claude/test_old_quotes.json
```

This produces a JSON array where each item has: `reference`, `gl_quote`, `orig_quote` (Hebrew), `gl_quote_roundtripped`.

### Step 2 -- Run new alignment extraction

```bash
python3 .claude/skills/tn-writer/scripts/extract_alignment_data.py \
    {ALIGNED} --output /tmp/claude/test_alignment.json
```

This produces a JSON object keyed by `"chapter:verse"`, where each value is an array of alignment records: `{eng, heb, heb_pos, strong}`.

### Step 3 -- Read source data

Read three files:
1. The old script results (`/tmp/claude/test_old_quotes.json`)
2. The alignment data (`/tmp/claude/test_alignment.json`)
3. The issue TSV (`{ISSUES}`) -- 7-column format: Book, Ref, SRef, GLQuote, Go?, AT, Explanation
4. The Hebrew source (`{HEBREW}`) -- extract verses for this chapter by finding `\c {chapter}` then reading `\v` markers. Each `\w surface|attrs\w*` token is a Hebrew word.

### Step 4 -- Claude does the semantic work

For each issue item (skipping `:intro` and `:front` references):

1. Read the `gl_quote` (the English phrase to match)
2. Look up the alignment data for this verse from the alignment JSON
   - Each alignment record has: `eng` (English word), `heb` (Hebrew word), `heb_pos` (position), `strong` (Strong's number)
3. Identify which alignment records correspond to the `gl_quote` words:
   - Semantically match the English words in `gl_quote` to the `eng` fields in the alignment records
   - Account for minor differences: the gl_quote may include curly-brace implied words `{like this}` that have no Hebrew alignment -- skip those
   - Match case-insensitively; strip punctuation when comparing
   - If the gl_quote is a multi-word phrase, find the contiguous or near-contiguous span of alignment records whose English words cover the phrase
4. Collect the `heb` values from the matched alignment records
5. Read the Hebrew source verse and find each collected Hebrew word as a `\w` token in it
6. Order the Hebrew words by their position in the Hebrew source verse (left-to-right reading order in the USFM, which is the canonical order)
7. Verify each Hebrew word appears character-for-character in the source verse as a `\w` token. Copy text exactly from the source -- do not generate Hebrew from memory.
8. Join the Hebrew words with spaces to form the Hebrew quote string

Record the result as `new_hebrew` for this item.

### Step 5 -- Build comparison

For each item, collect:
- `ref` -- the verse reference (e.g. `128:1`)
- `gl_quote` -- the English phrase
- `old_hebrew` -- from old script results (`orig_quote` field)
- `new_hebrew` -- from Claude's work in Step 4
- `old_valid` -- is each word in `old_hebrew` a substring of the Hebrew source verse?
- `new_valid` -- is each word in `new_hebrew` a substring of the Hebrew source verse?
- `old_order` -- do the words in `old_hebrew` appear in left-to-right order in the source verse?
- `new_order` -- do the words in `new_hebrew` appear in left-to-right order in the source verse?
- `old_dupes` -- does `old_hebrew` contain duplicate Hebrew words?
- `new_dupes` -- does `new_hebrew` contain duplicate Hebrew words?
- `agree` -- do old and new produce the same Hebrew quote?

Compute summary counts:
- Total items tested
- Old: valid quotes, correct order, duplicates found
- New: valid quotes, correct order, duplicates found
- Agreement count (old == new)

### Step 6 -- Write to report

Write results to `/tmp/claude/poc_ab_report.md` (created or overwritten). Print a brief summary to the conversation.

## Test B: AT Fit Check

Validation-only: checks substitution quality of existing notes output. No note generation.

### Step 1 -- Find existing notes

Check these locations in order:
1. `/tmp/claude/prepared_notes.json` AND `/tmp/claude/generated_notes.json` (both must exist)
2. `{output_root}/output/notes/PSA/PSA-{ch}.tsv`
3. `{output_root}/output/notes/PSA-{ch}.tsv`

If none found, report clearly and skip this test.

### Step 2 -- Run the AT fit test

```bash
python3 .claude/skills/tn-writer/scripts/test_prompt_over_code.py \
    --test at-fit --chapter {chapter_number} \
    --report /tmp/claude/poc_atfit.json
```

If prepared/generated JSON was found, add:
```
    --prepared-json /tmp/claude/prepared_notes.json \
    --generated-json /tmp/claude/generated_notes.json
```

If a notes TSV was found instead, add:
```
    --notes {path_to_notes_tsv}
```

### Step 3 -- Read results

Read `/tmp/claude/poc_atfit.json` and extract the `at_fit` test results. Append findings to the report.

## Report Format

Write `/tmp/claude/poc_ab_report.md`:

```markdown
# Prompt-Over-Code A/B Results

## Hebrew Quote Selection (PSA {chapter})

Items tested: N

| Metric | Old Script | Claude |
|--------|-----------|--------|
| Valid Hebrew quotes | X/N | Y/N |
| Correct word order | X/N | Y/N |
| Duplicate words | X | Y |

Agreement: Z/N items produced identical Hebrew quotes.

### Disagreements

| Ref | GL Quote | Old Hebrew | New Hebrew | Notes |
|-----|----------|-----------|-----------|-------|
| ... | ... | ... | ... | which is valid, order issues, etc. |

(Only rows where old != new)

## AT Fit (PSA {chapter})

Items checked: N
Orphaned conjunctions: X
Orphaned prepositions: Y
Capitalization errors: Z

### Flagged Items

| Ref | Issue | AT | Substitution |
|-----|-------|-----|-------------|
| ... | conj/prep/cap | ... | ... |
```

After writing the report, print a short summary to the conversation with the key numbers and the path to the full report.
