---
name: tq-writer
description: Update translation questions to align with current ULT/UST. Runs preparation script then AI reviews and updates Q&A content following the guidelines.
---

# Translation Question Writer

Update existing Translation Questions (TQs) to align with current ULT/UST texts. A preparation script handles all data extraction, then the AI reviews each chapter's TQs against the source texts and produces updated TSV.

## Prerequisites

- en_tq repo cloned at `/mnt/c/Users/benja/Documents/GitHub/en_tq`
- ULT/UST available (output/ files, repo clones, or fetched from Door43)

## Workflow

### Step 1: Ensure en_tq Clone

```bash
TQ_REPO="/mnt/c/Users/benja/Documents/GitHub/en_tq"
if [ ! -d "$TQ_REPO" ]; then
  git clone git@git.door43.org:unfoldingWord/en_tq.git "$TQ_REPO"
fi
# Pull latest if stale (more than a day old)
cd "$TQ_REPO" && git pull origin master
```

### Step 2: Run Preparation Script

```bash
# Single chapter
python3 .claude/skills/tq-writer/scripts/prepare_tq.py PSA --chapter 150 \
    --output /tmp/claude/prepared_tq.json

# Whole book
python3 .claude/skills/tq-writer/scripts/prepare_tq.py PSA --whole-book \
    --output /tmp/claude/prepared_tq.json
```

The script auto-detects ULT/UST from:
1. `output/AI-ULT/` and `output/AI-UST/` (AI-generated files)
2. Repo clones at `/mnt/c/Users/benja/Documents/GitHub/en_ult` and `en_ust`
3. Door43 fetch as fallback

Override with `--ult-path` or `--ust-path` if needed.

### Step 3: Read Guidelines

Read `reference/tq-guidelines.md` for the TQ update rules.

### Step 4: Review and Update TQs

Read `/tmp/claude/prepared_tq.json`. For each chapter:

1. Read the existing TQ rows from `tq_rows_by_chapter`
2. Read the ULT text from `ult_by_verse` and UST text from `ust_by_verse`
3. Compare each TQ row's question and response against the current ULT/UST
4. Update rows where needed following the guidelines

**Output format:** Write updated TSV rows to the output file, one chapter at a time. Include the header row. Use the same 7-column format:

```
Reference	ID	Tags	Quote	Occurrence	Question	Response
```

Rules for AI updates:
- Return the full set of rows for the chapter (not just changed ones)
- Preserve existing IDs -- do not change the ID column
- Preserve Tags, Quote, and Occurrence columns as-is (usually empty)
- Only modify Reference (if verse range changed), Question, and Response
- Follow tq-guidelines.md for content rules (third person, present tense, ESL level, etc.)
- If a row already matches the current ULT/UST, leave it unchanged

Write the result as a TSV file to `output/tq/{BOOK}-{CHAPTER}.tsv` (zero-padded chapter, e.g., `PSA-150.tsv`), or `output/tq/{BOOK}.tsv` for whole-book processing.

### Step 5: Post-Process Quotes

```bash
python3 .claude/skills/utilities/scripts/curly_quotes.py output/tq/PSA-150.tsv --in-place
```

### Step 6: Verify Output

```bash
python3 .claude/skills/tq-writer/scripts/verify_tq.py output/tq/PSA-150.tsv \
    --input-json /tmp/claude/prepared_tq.json
```

### Step 7: Insertion (when ready)

Reuse `insert_tn_rows.py` from repo-insert -- it works on TQ files too since both share the Reference column in the first position:

```bash
# Dry run first
python3 .claude/skills/repo-insert/scripts/insert_tn_rows.py \
    --book-file /mnt/c/Users/benja/Documents/GitHub/en_tq/tq_PSA.tsv \
    --source-file output/tq/PSA-150.tsv \
    --dry-run

# Apply
python3 .claude/skills/repo-insert/scripts/insert_tn_rows.py \
    --book-file /mnt/c/Users/benja/Documents/GitHub/en_tq/tq_PSA.tsv \
    --source-file output/tq/PSA-150.tsv \
    --backup
```

## Input Format

TQ TSV (7 columns with header):
```
Reference	ID	Tags	Quote	Occurrence	Question	Response
150:1	u3co				Where should everyone praise God?	Everyone should praise God in his sanctuary and the mighty heavens.
```

## Output Format

Same 7-column TSV with updated Question and Response content:
```
Reference	ID	Tags	Quote	Occurrence	Question	Response
150:1	u3co				Where should people praise God?	People should praise God in his holy place and in the mighty heavens.
```
