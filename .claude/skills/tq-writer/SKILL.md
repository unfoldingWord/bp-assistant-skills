---
name: tq-writer
description: Update translation questions to align with current ULT/UST. Use when asked to update translation questions or generate TQ for a chapter.
---

# Translation Question Writer

Update existing Translation Questions (TQs) to align with current ULT/UST texts. A preparation script handles all data extraction, then the AI reviews each chapter's TQs against the source texts and produces updated TSV.

## Workspace Tools Execution

Run workspace tools via the blessed CLI wrapper:

    node /app/src/workspace-tools-cli.js <tool_name> '<json-args>'

stdout is the tool result (identical to what the MCP tool returns). For args that
contain quotes, markdown, or newlines (e.g. the `note` text in update_note_text),
pass `-` as the second argument and pipe the JSON object on stdin via a heredoc.
Fallback (if Bash is unavailable): call `mcp__workspace-tools__<tool_name>` with
the same args.

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

For a single chapter, run:

    node /app/src/workspace-tools-cli.js prepare_tq '{"book":"PSA","chapter":150,"output":"/tmp/claude/prepared_tq.json"}'

For a whole book, omit `chapter` and add `"wholeBook":true`:

    node /app/src/workspace-tools-cli.js prepare_tq '{"book":"PSA","output":"/tmp/claude/prepared_tq.json","wholeBook":true}'

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
5. **Fill coverage gaps.** After the existing rows are updated, look at which verses in the chapter still have no question, and **aim for at least one question per verse**: for each uncovered verse where you can write a plain, answerable what/who/where/when/how comprehension question from the ULT/UST, add one. New rows carry the correct verse Reference and a fresh ID from `generate_ids` (see "Rules for AI updates" below — never invent one); they do not renumber or displace existing rows. Only skip a verse when no straightforward comprehension question can be written for it (e.g. a bare superscription or a fragment whose content is fully carried by an adjacent range row)

**Output format:** Write updated TSV rows to the output file, one chapter at a time. Include the header row. Use the same 7-column format:

```
Reference	ID	Tags	Quote	Occurrence	Question	Response
```

Rules for AI updates:
- This is an update-and-fill pass, not a fresh authoring pass. **Each existing row is edited in place** and produces exactly one updated row — do not re-author it, do not re-sequence or compress existing References. Separately, **add new rows to reach roughly one question per verse** where a verse currently has none and a good comprehension question can be written (see the Coverage rule in the guidelines); a coverage pass legitimately raises the row count, so the `verify_tq` >30% row-count warning is expected and not an error here
- Edit each existing question's wording in place to reflect the updated ULT/UST; keep its subject and scope. Do not replace a question with a different question on the same row
- Prefer "what / who / where / when / how" framings; do not introduce new "why" questions (existing why-questions that work stay as-is)
- Fail safe: if an existing row cannot be confidently matched to a verse in the prepared data, keep it unchanged rather than regenerating it
- Return the full set of rows for the chapter (not just changed ones)
- Preserve existing IDs -- do not change the ID column
- **Never invent an ID yourself.** Mint new IDs only with `generate_ids`, which draws from a real random source and re-seeds every run:

      node /app/src/workspace-tools-cli.js generate_ids '{"book":"1CH","count":<number of new rows>}'

  Ask for one ID per new row in a single call and assign them in order. Do not tweak, re-letter, or pattern-fill a returned ID. Hand-invented IDs are not random: they repeat across runs in the same relative order, and shortcuts like `tq01`/`tq02` are chapter-agnostic by construction — note both failure modes *pass* the `[a-z][a-z0-9]{3}` format check, so the format rule will not catch them.
- **ID uniqueness is book-wide, not chapter-wide.** The downstream editor keys rows `PRIMARY KEY (book, id)` with soft deletes, so a retired row owns its ID for that book permanently. A new ID must be unused across the entire book — every chapter in this session's output *and* the published `tq_{BOOK}.tsv` on master — not merely within the chapter being generated. Keep existing IDs on rows being revised (that reuse is what keeps generator and master aligned) and mint fresh IDs only for genuinely new rows. If two emitted rows still collide — including a single-verse row against a range row covering the same verse — replace the later one with another `generate_ids` value. Never emit two rows with the same ID.
- Preserve Tags, Quote, and Occurrence columns as-is (usually empty)
- Only modify Reference (if the ULT/UST content has genuinely moved to a different verse), Question, and Response
- **Multi-verse reference spans**: if the source row carries a range reference (e.g., `18:9-10`, `24:1-2`), copy it exactly into the output — do NOT collapse it to only the first verse
- Follow tq-guidelines.md for content rules (third person, present tense, ESL level, etc.)
- If a row already matches the current ULT/UST, leave its content unchanged — but still proofread its Question and Response for spelling, grammar, and punctuation errors and fix any found (see "Spelling, grammar, and punctuation" in tq-guidelines.md). No row is exempt from that pass

Write the result as a TSV file to `output/tq/{BOOK}/{BOOK}-{CHAPTER}.tsv` using exactly 3-digit chapter padding (e.g., `PSA/PSA-007.tsv`, `PSA/PSA-023.tsv`, `PSA/PSA-150.tsv`), or `output/tq/{BOOK}/{BOOK}.tsv` for whole-book processing.

### Step 5: Post-Process Quotes

Run:

    node /app/src/workspace-tools-cli.js curly_quotes '{"input":"output/tq/PSA/PSA-006.tsv","inPlace":true}'

### Step 6: Verify Output

Run:

    node /app/src/workspace-tools-cli.js verify_tq '{"tsvFile":"output/tq/PSA/PSA-006.tsv","inputJson":"/tmp/claude/prepared_tq.json"}'

### Step 6.5: Duplicate ID Check

After writing all chapter files, scan the full output for duplicate IDs before proceeding to insertion. Run `check_tn_quality` with `tsvPath` pointing to the output TSV and look for any `id_duplicate` findings:

    node /app/src/workspace-tools-cli.js check_tn_quality '{"tsvPath":"<output TSV>"}'

For multi-chapter or whole-book runs, check each chapter file in sequence and maintain a cross-chapter seen-ID set.

If `check_tn_quality` is unavailable for TQ files, run the dedicated checker instead — it validates ID format and finds duplicates within and across files in one pass. Pass all chapter files from this session together, and **always** pass `against` the published book TSV — because the consumer keys rows per book, a new ID that is merely chapter-unique is not safe:

Primary — CLI wrapper:
```
node /app/src/workspace-tools-cli.js check_duplicate_ids '{"files":["output/tq/{BOOK}/{BOOK}-{CH1}.tsv","output/tq/{BOOK}/{BOOK}-{CH2}.tsv"],"against":["door43-repos/en_tq/tq_{BOOK}.tsv"]}'
```

Fallback A — MCP tool (when Bash is unavailable):
```
mcp__workspace-tools__check_duplicate_ids({
  files: ["output/tq/{BOOK}/{BOOK}-{CH1}.tsv", "output/tq/{BOOK}/{BOOK}-{CH2}.tsv"],
  against: ["door43-repos/en_tq/tq_{BOOK}.tsv"]
})
```

Fallback B — dedicated `.mjs` checker via Bash:
```bash
node .claude/skills/utilities/scripts/validation/check_duplicate_ids.mjs \
  output/tq/{BOOK}/{BOOK}-*.tsv --against door43-repos/en_tq/tq_{BOOK}.tsv
```

Exit code 1 means duplicates or malformed IDs were found; fix each by replacing the later-occurring ID with a fresh `generate_ids` value, re-run until clean, and only then proceed to insertion.

> **Why this step exists**: `verify_tq` (Step 6) does not detect duplicate IDs. Duplicates break downstream processing software (merge/delete matching fails). This explicit check is the safety net against two failure modes: the same ID assigned to two rows in one session (e.g. verse 53:2 and the range 53:2-3), and an ID reissued to a new chapter that another chapter of the same book already owns on master (issue #158, where six 1CH 23 IDs landed on rows minted for 1CH 5).

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
