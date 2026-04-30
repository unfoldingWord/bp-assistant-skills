---
name: tq-writer
description: Update translation questions to align with current ULT/UST. Use when asked to update translation questions or generate TQ for a chapter.
---

# Translation Question Writer

Update existing Translation Questions (TQs) to align with current ULT/UST texts. A preparation script handles all data extraction, then the AI reviews each chapter's TQs against the source texts and produces updated TSV.

## Prerequisites

```bash
source .env  # provides $DOOR43_REPOS_PATH
```

- en_tq repo cloned at `$DOOR43_REPOS_PATH/en_tq`
- ULT/UST available (output/ files, repo clones, or fetched from Door43)

## Workflow

### Step 1: Ensure en_tq Clone

```bash
TQ_REPO="$DOOR43_REPOS_PATH/en_tq"
if [ ! -d "$TQ_REPO" ]; then
  git clone git@git.door43.org:unfoldingWord/en_tq.git "$TQ_REPO"
fi
# Pull latest if stale (more than a day old)
cd "$TQ_REPO" && git pull origin master
```

### Step 2: Run Preparation Script

Use `mcp__workspace-tools__prepare_tq` with `book="PSA"`, `chapter=150`, `output="/tmp/claude/prepared_tq.json"` for a single chapter. For a whole book, omit `chapter` and pass `wholeBook=true`.

The tool auto-detects ULT/UST from:
1. `output/AI-ULT/` and `output/AI-UST/` (AI-generated files)
2. Repo clones at `$DOOR43_REPOS_PATH/en_ult` and `en_ust`
3. Door43 fetch as fallback

Override with `ultPath` or `ustPath` if needed.

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

Write the result as a TSV file to `output/tq/{BOOK}/{BOOK}-{CHAPTER}.tsv` using exactly 3-digit chapter padding (e.g., `PSA/PSA-007.tsv`, `PSA/PSA-023.tsv`, `PSA/PSA-150.tsv`), or `output/tq/{BOOK}/{BOOK}.tsv` for whole-book processing.

### Step 5: Post-Process Quotes

Use `mcp__workspace-tools__curly_quotes` with `input="output/tq/PSA/PSA-006.tsv"`, `inPlace=true`.

### Step 6: Verify Output

Use `mcp__workspace-tools__verify_tq` with `tsvFile="output/tq/PSA/PSA-006.tsv"`, `inputJson="/tmp/claude/prepared_tq.json"`.

### Step 7: Insertion (when ready)

Use `door43-push-cli.js` with `--type tn` (TQ uses the same insertion path as TN). For interactive dry-run preview, use the `repo-insert` skill's Step 2 guidance.

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
