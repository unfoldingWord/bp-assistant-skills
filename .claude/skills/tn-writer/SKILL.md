---
name: tn-writer
description: Generate translation notes from issue identification TSV. Uses prompt-over-code: scripts handle mechanical extraction, prompts handle semantic content. Use when asked to write translation notes, create TN from issues, or generate notes for a chapter.
---

# Translation Note Writer

Generate translation notes from issue identification output. The preparation stage owns deterministic work and note interpretation (template matching, `t:` / `i:` parsing, AT policy, issue-type rules, language conversion, ID generation, prompt assembly). Claude's job is the prose: write the note text for one prepared item, then do at most one bounded rewrite pass if AT-fit fails.

## Workspace Tools Execution

Run workspace tools via the blessed CLI wrapper:

    node /app/src/workspace-tools-cli.js <tool_name> '<json-args>'

stdout is the tool result (identical to what the MCP tool returns). For args
that contain quotes, markdown, or newlines (e.g. the `note` text in
`update_note_text`), DO NOT inline them — pass `-` as the second argument and
pipe the JSON object on stdin via a heredoc:

    node /app/src/workspace-tools-cli.js update_note_text - <<'EOF'
    {"generatedJson":"tmp/claude/generated_notes.json","id":"ab1c","note":"Alternate translation: ..."}
    EOF

Fallback (if Bash is unavailable): call `mcp__workspace-tools__<tool_name>` with
the same args.

**Prohibited:** Follow the shared structured-edit policy in `.claude/skills/reference/structured-edit-policy.md` — no ad-hoc scripts, no hand-`Edit` of the notes JSON/TSV, no `Edit` retries after "string to replace not found".

## Prerequisites

- Input TSV in `output/issues/` (from issue-identification)
- Plain ULT and UST USFM files (from issue-identification or fetched fresh)
- The tsv-quote-converters tool (path resolved automatically by the script)

## Pipeline Context

If `--context <path>` is provided, read the context.json file first. It contains the authoritative source paths:
- `sources.ult` — current ULT for this chapter (fetched fresh from Door43 by the pipeline runner)
- `sources.ustPlain` — current UST for this chapter, **alignment markers stripped** — use this for reading
- `sources.ust` — raw UST USFM with alignment markers intact (very large for long chapters — do not read directly)
- `sources.ultAligned` — aligned ULT if available
- `sources.issues` — issues TSV path
- `runtime.preparedNotes` — persistent JSON output path for prepared notes
- `runtime.generatedNotes` — persistent JSON output path for generated notes
- `runtime.alignmentData` — persistent JSON output path for alignment data

When a context file is provided, use these paths as your inputs and outputs. Do not fetch from Door43 or write to `/tmp/` — the context file has the correct, current versions and persistent artifact paths under the pipeline working directory.

## Workflow

### Step 1: Read Prepared Data

The pipeline runner has already completed all mechanical preparation before invoking this skill:
- Parsed the issues TSV into writer packets (`prepare_notes`)
- Filled Hebrew orig_quotes from alignment data (`fill_orig_quotes`)
- Resolved gl_quotes to ULT English spans (`resolve_gl_quotes`)
- Flagged narrow quotes that may need expansion (`flag_narrow_quotes`)
- Generated unique 4-char TN IDs for every item (`generate_ids`)

Each item's `id` field is already populated. Do not generate or overwrite IDs — doing so risks collisions with upstream or within the chapter.

**Do not use the raw `Read` tool on `runtime.preparedNotes`** — the file can exceed the SDK's 10K-token read limit and cause an error. Instead, use the `read_prepared_notes` tool rather than the raw Read tool:

1. `node /app/src/workspace-tools-cli.js read_prepared_notes '{"preparedJson":"<path>","summaryOnly":true}'` — get total count and item IDs
2. `node /app/src/workspace-tools-cli.js read_prepared_notes '{"preparedJson":"<path>","start":0,"end":19}'` — fetch items 0–19
3. Continue in batches of ≤20 until all items are loaded (check `hasMore` in the response)

Each item has all fields populated including `writer_packet`, `orig_quote`, `gl_quote`, templates, AT policy, and style rules. Do not re-run preparation MCP tools.

If any items have empty `orig_quote` (and reference does not end with `:front`), note them for graceful degradation -- do not attempt manual resolution loops.

Items flagged as narrow quotes are correct for focusing the note body on the issue, but may need wider phrase boundaries for AT fit later. Keep this in mind during note generation -- write initial ATs that anticipate the surrounding phrase context.

If no context.json is provided (standalone invocation outside the pipeline), fall back to the prepare tool: `node /app/src/workspace-tools-cli.js prepare_and_validate '{"inputTsv":"output/issues/<BOOK>/<BOOK>-<CH>.tsv","alignedUsfm":"output/AI-ULT/<BOOK>/<BOOK>-<CH>-aligned.usfm","output":"tmp/claude/prepared_notes.json"}'` runs all four steps in one call.

### Step 2: Read the Style Guide

Read `reference/note-style-guide.md` for the note writing rules.

### Step 2a: Check canonical sources

Before generating notes, check for content team decisions that affect this chapter's issues:

```bash
# Search for decisions about specific terms or issue types
grep -i "<term or issue type>" data/issues_resolved.txt
```

Canonical vocabulary references (read-only -- never modify these):
- `data/issues_resolved.txt` -- content team decisions, highest authority
- `data/glossary/hebrew_ot_glossary.csv` -- standard ULT/UST renderings
- `data/glossary/psalms_reference.csv` -- Psalms-specific terms
- `data/glossary/sacrifice_terminology.csv` -- sacrifice/offering vocabulary
- `data/glossary/biblical_measurements.csv` -- weights, volumes, distances
- `data/glossary/biblical_phrases.csv` -- grammatical and prophetic phrases
- `data/quick-ref/ult_decisions.csv` / `ust_decisions.csv` -- prior rendering decisions
- `data/quick-ref/tn_decisions.csv` -- accumulated TN note-phrasing / quote-selection
  preferences learned from editor reviews (proposed by `tn-edit-compare`,
  recorded by `tn-edit-record`). When a row's `SupportReference` matches an
  issue you're noting (and its `Book` is `ALL` or this book), prefer that note
  wording and quote span:
  ```bash
  grep -i "<SupportReference>" data/quick-ref/tn_decisions.csv 2>/dev/null
  ```

If `issues_resolved.txt` contains a decision about how a specific issue type should be handled, follow it. If a note references a Hebrew term, use the rendering from canonical CSVs unless `issues_resolved.txt` specifies otherwise.

### Step 3: Generate Notes (write keyed JSON, not TSV)

Use `node /app/src/workspace-tools-cli.js read_prepared_notes '{"preparedJson":"<path>","start":0,"end":19}'` to load all items from the prepared-notes path (see Step 1 above for batching protocol). For each item, generate a note and write it to a JSON object keyed by the item's `id`. Write the result to `runtime.generatedNotes` from context.json when available, otherwise `tmp/claude/generated_notes.json`.

Process one item at a time. Each note addresses exactly one item from the prepared JSON, which corresponds to one issue in one verse. Never create summary notes that combine or reference multiple verse occurrences of the same pattern (e.g., do not write "The author uses synecdoche in verses 2, 5, and 6"). Each verse gets its own self-contained note even when the same figure recurs across the chapter.

As you work through items, keep a mental map of interpretive commitments you have made (e.g., "in v9 I said inheritance = people"). This mental map is for consistency, not for creating cross-verse summaries. When a note references or depends on a concept from a nearby verse, check that the interpretation is consistent with notes you already wrote. If you spot a conflict, resolve it before continuing -- adjust the current note or go back and revise the earlier one.

1. Read the `system_prompt_key` field to know which persona to use:
   - `ai_writes_at_agent` -- Generate the note AND an alternate translation
   - `given_at_agent` -- Generate the note only (AT already provided or not needed)

2. Read the `writer_packet` field first. This is the authoritative contract for note generation. It already contains the selected template, parsed directives, AT policy, and issue-type style rules. Use the `prompt` field only as a compact rendering of that packet.

3. Follow `at_policy`, not raw inference:
   - `required` -- do NOT include an alternate translation. The pipeline generates ATs separately after note writing. Write only the explanatory note text.
   - `forbidden` -- do not add an alternate translation
   - `provided` -- use the provided AT as context if needed, but do not output a new one unless the packet already contains a programmatic note
   - `not_needed` -- do not add an alternate translation

4. For items where `writer_packet.programmatic_note` is non-empty, write that note text exactly and move on. Do not reinterpret the row.

5. Do not generate alternate translations. The pipeline handles AT generation as a separate step after note writing. For all items with `at_policy: required`, write only the explanatory note text. The pipeline will programmatically append `Alternate translation: [text]` after generating ATs with a focused, validated process.

6. For items with `tcm_mode: true`:
   - Present multiple interpretations using the "This could mean:" format
   - Each interpretation gets its own AT in square brackets

7. For items with `note_type: "hint"` (editor-marked TN row hints):
   - Read the `seed` field for authorial guidance from a human translator.
   - When `seed` is a stub like `"This could mean: (1) NOTE Alternate translation: [ALT] (2) NOTE Alternate translation: [ALT]"`, expand each placeholder — replace `NOTE` with a real interpretive option and `[ALT]` with an actual alternate translation, in the same template shape.
   - When `seed` is a one-line reason ("Could be either the neighbor's view or the speaker's view"), build the note around that framing.
   - When `seed` is empty or null, write a fresh note as you would for any item, using `orig_quote` and `sref` as the anchors.
   - Never echo the seed verbatim. The seed is direction, not output.
   - The item's `id` is the editor's stable row id; do not change or replace it. Assembly will use it as the TSV ID column so the editor can update the existing row in place.
   - Hint items skip the see-how detection pass and don't carry a `writer_packet`. Treat them like a `given_at` item: generate note text only.

Output format -- a flat JSON object mapping item ID to note text:
```json
{
  "em7t": "A **chief musician** is a person who...",
  "dcc8": "A **stringed instrument** is a type of...",
  ...
}
```

Write this to the generated-notes path from context.json when available, otherwise `tmp/claude/generated_notes.json`. Do NOT assemble the TSV yourself -- the assembly script handles that to prevent row misalignment.

### Step 4: Skip — AT Generation Handled by Pipeline

AT generation is handled separately by the pipeline after note writing. Do not generate, verify, or fix alternate translations. Proceed directly to assembly.

The pipeline will:
1. Generate ATs using focused per-item API calls with a constrained prompt
2. Validate each AT by programmatically substituting it into the verse
3. Append `Alternate translation: [text]` to each note programmatically

If items have narrow gl_quotes that may need expansion for AT fit, the pipeline handles this during AT generation.

### Step 5: Assemble Output TSV (script)

Run the assembly script to produce the final TSV. The script reads metadata from the prepared JSON and note text from the generated JSON, matching by ID. This prevents note/row misalignment.

If `--output <path>` was provided in the invocation, use that exact path for `assemble_notes`. Otherwise default to `output/notes/<BOOK>/<BOOK>-<CH>.tsv`.

Use `node /app/src/workspace-tools-cli.js assemble_notes '{"preparedJson":"<path>","generatedJson":"<path>","output":"<path>"}'` with `preparedJson`, `generatedJson`, and the determined output path.

### Step 6: Post-Process

Run curly quote conversion on the output:

Use `node /app/src/workspace-tools-cli.js curly_quotes '{"input":"<notes-tsv>","inPlace":true}'` with `input` set to the notes TSV and `inPlace: true`.

Fix Hebrew quote Unicode to match UHB source byte order (prevents UI highlighting failures):

Use `node /app/src/workspace-tools-cli.js fix_unicode_quotes '{"tsvFile":"<notes-tsv>"}'` with `tsvFile` set to the notes TSV path.

Strip bold from any quoted word that doesn't exactly match the ULT verse text:

Use `node /app/src/workspace-tools-cli.js verify_bold_matches '{"tsvFile":"<notes-tsv>","ultUsfm":"<plain-ult-usfm>"}'` with `tsvFile` set to the notes TSV path and `ultUsfm` set to the plain ULT USFM path.

### Step 7: Final Review

Read the assembled TSV alongside the aligned ULT. For each row, verify:

1. **Quote column** is non-empty and contains Hebrew text
2. **Single-verse quotes** -- the Quote must contain material from one verse only (exception: `translate-versebridge`). If the issue relates to surrounding verses, discuss them in the Note text, not the Quote.
3. **Continuous text** -- avoid discontinuous quotes with ampersands (`&`). Expand the quote to include intervening text rather than breaking it.
4. **Note text** addresses the issue type indicated by SupportReference
5. **AT fit** -- if an Alternate Translation is present, mentally substitute it for the GLQuote in the ULT verse and confirm it reads naturally
6. **Quote scope** -- the Hebrew quote covers the right range (not too narrow or too wide for the issue)
7. **No duplicate UST phrasing** -- ATs should differ from the UST for the same verse

For `writing-pronouns` rows, apply three extra checks during final review:
1. If the referent is already obvious from the verse context or made explicit by the UST, remove the note instead of preserving a low-value pronoun explanation.
2. Narrow the Quote/GLQuote anchor to the first pronoun occurrence that actually needs clarification; do not leave a full-verse span for a single pronoun issue.
3. If multiple `writing-pronouns` rows in the same verse explain the same referent, keep only the first necessary note and remove later duplicates.

Fix any issues found via the structured by-id tools — never hand-`Edit` `generated_notes.json`, `prepared_notes.json`, or the assembled TSV:
- Note text problems → `update_note_text` with `generatedJson`, the affected `id`, and the full replacement `note` text. Because the note text can contain quotes/markdown, use the STDIN heredoc form:

  ```bash
  node /app/src/workspace-tools-cli.js update_note_text - <<'EOF'
  {"generatedJson":"<path>","id":"ab1c","note":"<full replacement note text>"}
  EOF
  ```
- Quote scope / continuity / single-verse violations → `update_prepared_quote` with `preparedJson`, the affected `id`, and the changed `glQuote` / `glQuoteRoundtripped` / `origQuote` fields, then re-run assembly (`assemble_notes`) and post-processing (`curly_quotes`, `fix_unicode_quotes`, `verify_bold_matches`) once. Because the quote fields can contain quotes, use the STDIN heredoc form:

  ```bash
  node /app/src/workspace-tools-cli.js update_prepared_quote - <<'EOF'
  {"preparedJson":"<path>","id":"ab1c","glQuote":"...","glQuoteRoundtripped":"...","origQuote":"...","sref":"..."}
  EOF
  ```
- Row removal (e.g. low-value pronoun note, duplicate) → `remove_note` with the `id`, `generatedJson`, and `tsvFile`. Use the STDIN heredoc form:

  ```bash
  node /app/src/workspace-tools-cli.js remove_note - <<'EOF'
  {"id":"ab1c","generatedJson":"<path>","tsvFile":"<notes-tsv>"}
  EOF
  ```

This is a lightweight review pass, not a regeneration -- just catch structural problems the scripts can't judge. If `update_note_text` / `update_prepared_quote` / `remove_note` returns a "not found" or similar error twice for the same id, stop trying to fix that row and move on; do not fall back to hand-`Edit`.

### Step 8: Gemini Review (optional, activation only)

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

- **Empty orig_quote in prepared notes**: The Hebrew quote extraction (pipeline mechanical prep, or `prepare_and_validate` in standalone runs) found no match. Check that the issue row's Book/Chapter/Verse matches the Hebrew USFM.
- **verify_at_fit.py ERRORS**: The alignment token check failed. Common causes: stale ULT (re-fetch with fetch_door43.py), or orig_quote spans a verse boundary. Fix the quote and re-run verification.
- **assemble_notes.py missing items**: Rows were filtered out during assembly. Check that every row has a non-empty SupportReference and that the issue type matches a known TA article.
- **QUOTE_NOT_FOUND from lang_convert.js**: The Greek/Hebrew quote could not be located in the source text. Verify the quote is copied exactly from the USFM (including cantillation marks for Hebrew).
- **assemble_notes fails repeatedly**: If `assemble_notes` returns an error twice in a row, stop immediately. Do not attempt to debug or repair the prepared JSON — it is a pipeline input, not your output. Report the error and the paths to any files already written (generated_notes.json) so a human can intervene.

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
| `writes_at` | `at_policy` is `required` | Generate note + AT |
| `given_at` | `at_policy` is `provided`, `forbidden`, or `not_needed` | Generate note only |
| `see_how_at` | Explanation starts with "see how", no AT | Generate AT only |
| `see_how` | Explanation starts with "see how", has AT | Prefer the programmatic note in `writer_packet.programmatic_note` |
| `hint` | Editor-marked TN row hint (carries `seed`, `hintRowId`, `fromHint: true`) | Expand `seed` into a complete note; keep the pre-assigned `id` so the editor can UPDATE in place |

## Special Modes

### TCM (This Could Mean)
When explanation starts with "TCM", present multiple interpretations:
"This could mean: (1) [interpretation]. Alternate translation: [AT] or (2) [interpretation]. Alternate translation: [AT]"

### i: prefix
Information that must be included in the note. Already parsed into `must_include` during preparation. Treat it as authoritative.

### t: prefix
Hint about which template variant to use. Preparation resolves this into `template_type`, `template_locked`, and `template_text`; do not re-decide the template at generation time unless the packet explicitly left it unresolved.

### Editor-marked TN row hints

Some prepared items represent rows a human translator pre-marked in bible-editor as "hints" — the translator already chose the issue type and quote, optionally seeded a stub or one-line reason, and queued the row for AI expansion. These items are easy to spot: `note_type: "hint"`, a `seed` string (may be null), `hintRowId` equal to `id`, and `fromHint: true`. The pipeline guarantees:

- No competing item exists for the same `(verse, supportReference, fuzzy-quote)` — the human's framing has already displaced any AI-derived issue on that slot.
- The item's `id` is the editor's stable row id and must not be regenerated; assembly writes it to the TSV's ID column unchanged so the editor can UPDATE the existing stub row in place rather than INSERT a new one.
- `writer_packet`, `template_text`, and `at_policy` are absent or generic. Hints don't go through the template / AT-policy selector; rely on `seed` + `sref` + `orig_quote` for the note's content and shape.

Expand `seed` into a fully-formed note (see Step 3 item 7). Never echo it verbatim and never drop the row.
