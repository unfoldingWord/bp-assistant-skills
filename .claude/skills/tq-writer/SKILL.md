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
- ULT/UST require no local setup by default — `prepare_tq` pulls them from Door43 master; pass `ultPath`/`ustPath` to use local files instead (see Step 2)

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

By default the tool pulls ULT and UST from the current Door43 **master** text (implemented in bp-assistant PR #149): it fetches `en_ult` and `en_ust` for the book, de-aligns them (collapsing each verse and stripping alignment markup), and exposes them as `ult_by_verse` / `ust_by_verse`. It checks each file's git blob sha first and reuses a cached de-alignment when master is unchanged, so repeat runs do not re-download or re-parse. Always feed **de-aligned** text — aligned USFM parses to almost nothing. For the TQ workflow this default is correct: TQs update the *already-published* question set, whose ULT/UST is on master.

To base questions on text that is not the current master — e.g. freshly generated AI ULT/UST for a book not yet pushed to Door43 — pass `ultPath` and/or `ustPath` pointing at those local files; an override is de-aligned the same way.

### Step 3: Read Guidelines

Read `reference/tq-guidelines.md` for the TQ update rules.

### Step 4: Review and Update TQs

Read `/tmp/claude/prepared_tq.json`. For each chapter:

1. Read the existing TQ rows from `tq_rows_by_chapter`
2. Read the ULT text from `ult_by_verse` and UST text from `ust_by_verse`
3. Compare each TQ row's question and response against the current ULT and UST; **default to ULT language** for questions and responses; **fall back to UST language only when the ULT rendering is metaphorical, uses Hebrew idioms, or is otherwise not plain/accessible English** — use the UST's non-figurative wording for those cases
4. Update rows where needed following the guidelines

**Output format:** Write updated TSV rows to the output file, one chapter at a time. Include the header row. Use the same 7-column format:

```
Reference	ID	Tags	Quote	Occurrence	Question	Response
```

Rules for AI updates:
- Return the full set of rows for the chapter (not just changed ones)
- Preserve existing IDs -- do not change the ID column
- **ID uniqueness is mandatory**: Before emitting each row, check its ID against every ID already written in the current output (across all chapters processed so far in this session). If a collision is detected — including between a single-verse row and a multi-verse range row that covers the same verse — assign a new unique 4-char ID (`[a-z][a-z0-9]{3}`) to the colliding row and confirm the replacement ID is not already in use. Never emit two rows with the same ID.
- Preserve Tags, Quote, and Occurrence columns as-is (usually empty)
- Only modify Reference (if the ULT/UST content has genuinely moved to a different verse), Question, and Response
- **Multi-verse reference spans**: if the source row carries a range reference (e.g., `18:9-10`, `24:1-2`), copy it exactly into the output — do NOT collapse it to only the first verse
- Follow tq-guidelines.md for content rules (third person, present tense, ESL level, etc.)
- If a row already matches the current ULT/UST, leave it unchanged

Write the result as a TSV file to `output/tq/{BOOK}/{BOOK}-{CHAPTER}.tsv` using exactly 3-digit chapter padding (e.g., `PSA/PSA-007.tsv`, `PSA/PSA-023.tsv`, `PSA/PSA-150.tsv`), or `output/tq/{BOOK}/{BOOK}.tsv` for whole-book processing.

### Step 5: Post-Process Quotes

Use `mcp__workspace-tools__curly_quotes` with `input="output/tq/PSA/PSA-006.tsv"`, `inPlace=true`.

### Step 6: Verify Output

Use `mcp__workspace-tools__verify_tq` with `tsvFile="output/tq/PSA/PSA-006.tsv"`, `inputJson="/tmp/claude/prepared_tq.json"`.

### Step 6.5: Duplicate ID Check

After writing all chapter files, scan the full output for duplicate IDs before proceeding to insertion. Use `mcp__workspace-tools__check_tn_quality` with `tsvFile` pointing to the output TSV and look for any `id_duplicate` findings. For multi-chapter or whole-book runs, check each chapter file in sequence and maintain a cross-chapter seen-ID set.

If `check_tn_quality` is unavailable for TQ files, run the dedicated checker instead — it validates ID format and finds duplicates within and across files in one pass (pass all chapter files from this session together, and optionally check collisions against the published book TSV):

Option A — MCP tool (preferred, works without Bash):
```
mcp__workspace-tools__check_duplicate_ids({
  files: ["output/tq/{BOOK}/{BOOK}-{CH1}.tsv", "output/tq/{BOOK}/{BOOK}-{CH2}.tsv"],
  against: ["door43-repos/en_tq/tq_{BOOK}.tsv"]
})
```

Option B — Bash (when available):
```bash
node .claude/skills/utilities/scripts/validation/check_duplicate_ids.mjs \
  output/tq/{BOOK}/{BOOK}-*.tsv --against door43-repos/en_tq/tq_{BOOK}.tsv
```

Exit code 1 means duplicates or malformed IDs were found; fix each by replacing the later-occurring ID with a freshly generated unique value, re-run until clean, and only then proceed to insertion.

> **Why this step exists**: `verify_tq` (Step 6) does not detect duplicate IDs. Duplicates break downstream processing software (merge/delete matching fails). This explicit check is the safety net against AI sessions that generate the same random ID for two different verse rows (e.g., one for verse 53:2 and one for the range 53:2-3).

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
