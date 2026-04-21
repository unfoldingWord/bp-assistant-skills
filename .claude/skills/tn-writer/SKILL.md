---
name: tn-writer
description: Generate translation notes from issue identification TSV. Uses prompt-over-code: scripts handle mechanical extraction, prompts handle semantic content. Use when asked to write translation notes, create TN from issues, or generate notes for a chapter.
---

# Translation Note Writer

Generate translation notes from issue identification output. The preparation stage owns deterministic work and note interpretation (template matching, `t:` / `i:` parsing, AT policy, issue-type rules, language conversion, ID generation, prompt assembly). Claude's job is the prose: write the note text for one prepared item, then do at most one bounded rewrite pass if AT-fit fails.

## MCP-First Execution

When running in restricted mode, use workspace MCP tools instead of direct shell/python calls. Primary tools:
- `mcp__workspace-tools__prepare_and_validate` — **preferred**: runs prepare + alignment + gl_quote resolution + flagging + AT verification in one call (saves turns)
- `mcp__workspace-tools__prepare_notes` — prepare only (use when you need to modify the prepared JSON between steps)
- `mcp__workspace-tools__extract_alignment_data`
- `mcp__workspace-tools__resolve_gl_quotes`
- `mcp__workspace-tools__flag_narrow_quotes`
- `mcp__workspace-tools__verify_at_fit`
- `mcp__workspace-tools__assemble_notes`
- `mcp__workspace-tools__curly_quotes`
- `mcp__workspace-tools__fix_hebrew_quotes` — pass `output` param to write to file instead of returning inline
- `mcp__workspace-tools__generate_ids` — do not call when running inside the pipeline: IDs are pre-populated by the pipeline runner during mechanical prep. Calling this again risks collisions.

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

**Do not use the raw `Read` tool on `runtime.preparedNotes`** — the file can exceed the SDK's 10K-token read limit and cause an error. Instead, use the `mcp__workspace-tools__read_prepared_notes` tool:

1. `read_prepared_notes({ preparedJson: <path>, summaryOnly: true })` — get total count and item IDs
2. `read_prepared_notes({ preparedJson: <path>, start: 0, end: 19 })` — fetch items 0–19
3. Continue in batches of ≤20 until all items are loaded (check `hasMore` in the response)

Each item has all fields populated including `writer_packet`, `orig_quote`, `gl_quote`, templates, AT policy, and style rules. Do not re-run preparation MCP tools.

If any items have empty `orig_quote` (and reference does not end with `:front`), note them for graceful degradation -- do not attempt manual resolution loops.

Items flagged as narrow quotes are correct for focusing the note body on the issue, but may need wider phrase boundaries for AT fit later. Keep this in mind during note generation -- write initial ATs that anticipate the surrounding phrase context.

If no context.json is provided (standalone invocation outside the pipeline), fall back to the MCP tools: `mcp__workspace-tools__prepare_and_validate` runs all four steps in one call.

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

If `issues_resolved.txt` contains a decision about how a specific issue type should be handled, follow it. If a note references a Hebrew term, use the rendering from canonical CSVs unless `issues_resolved.txt` specifies otherwise.

### Step 3: Generate Notes (write keyed JSON, not TSV)

Use `mcp__workspace-tools__read_prepared_notes` to load all items from the prepared-notes path (see Step 1 above for batching protocol). For each item, generate a note and write it to a JSON object keyed by the item's `id`. Write the result to `runtime.generatedNotes` from context.json when available, otherwise `tmp/claude/generated_notes.json`.

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

Use `mcp__workspace-tools__assemble_notes` with `preparedJson`, `generatedJson`, and the determined output path.

### Step 6: Post-Process

Run curly quote conversion on the output:

Use `mcp__workspace-tools__curly_quotes` with `input` set to the notes TSV and `inPlace: true`.

Fix Hebrew quote Unicode to match UHB source byte order (prevents UI highlighting failures):

Use `mcp__workspace-tools__fix_unicode_quotes` with `tsvFile` set to the notes TSV path.

Strip bold from any quoted word that doesn't exactly match the ULT verse text:

Use `mcp__workspace-tools__verify_bold_matches` with `tsvFile` set to the notes TSV path and `ultUsfm` set to the plain ULT USFM path.

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

Fix any issues found and rewrite the TSV row(s) if needed. This is a lightweight review pass, not a regeneration -- just catch structural problems the scripts can't judge.

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

- **Empty orig_quote after Step 2c**: The Hebrew quote extraction found no match. Check that the issue row's Book/Chapter/Verse matches the Hebrew USFM. Re-run with `--verbose` to see candidate matches.
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

## Special Modes

### TCM (This Could Mean)
When explanation starts with "TCM", present multiple interpretations:
"This could mean: (1) [interpretation]. Alternate translation: [AT] or (2) [interpretation]. Alternate translation: [AT]"

### i: prefix
Information that must be included in the note. Already parsed into `must_include` during preparation. Treat it as authoritative.

### t: prefix
Hint about which template variant to use. Preparation resolves this into `template_type`, `template_locked`, and `template_text`; do not re-decide the template at generation time unless the packet explicitly left it unresolved.
