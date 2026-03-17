---
name: editor-compare
description: Compare editor-edited ULT/UST against AI output to identify systematic preferences. Feeds findings back into glossary and quick-ref. Use when asked to compare editor changes or learn from editing patterns.
allowed-tools: Read, Grep, Glob, Bash, Write, Edit
---

# Editor Compare

Compare editor-edited text against AI-generated ULT/UST to identify vocabulary, structure, and style preferences. Feeds findings back into the project glossary and quick-ref decisions files.

## Prerequisites

- AI output in `output/AI-ULT/` or `output/AI-UST/` (from ULT-gen or UST-gen)
- Editor source: Door43 master (HTTP fetch) or editor-feedback file

## Protected Canonical Files -- NEVER modify

These are fetched from Google Drive and represent content team decisions.
Editor-compare must never write to, append to, or modify them.
If an editor preference contradicts a canonical source, log the conflict
and present it for escalation -- do not change the canonical file.

- `data/issues_resolved.txt`
- `data/glossary/hebrew_ot_glossary.csv`
- `data/glossary/biblical_measurements.csv`
- `data/glossary/psalms_reference.csv`
- `data/glossary/sacrifice_terminology.csv`
- `data/glossary/biblical_phrases.csv`

## Single-Chapter Mode

### Step 1: Run the comparison script

Run once per type. If the user doesn't specify a type, run for both ult and ust (skip if AI output doesn't exist for that type).
If the user requested verse scope (for example `1:1-6`), pass only the in-chapter verse segment (`1-6`) to the comparison step.

Use `mcp__workspace-tools__prepare_compare` (preferred in restricted environments):
- Required: `book`, `chapter`, `type`
- Optional verse filter: `verses` (for example `"1-6"` or `"1,3,5-7"`)
- Output path: `output`

Example arguments:
`{"book":"LAM","chapter":1,"type":"ult","verses":"1-6","output":"/tmp/claude/compare_ult.json"}`

If the user provides an editor-feedback file, pass `editorUsfm` to `prepare_compare`.

Comparison output includes normalized fields. Curly-brace and quote-mark-only differences are formatting noise and should not be treated as substantive editor preferences.

### Step 2: Read the comparison JSON

Read `/tmp/claude/compare_<type>.json`. Note the summary stats (total, changed, unchanged).

If `editor_comments` is present (from `--editor-file`), these are direct editor explanations. They carry high weight -- treat each comment as a confirmed preference.

### Step 3: Analyze changed verses

For each changed verse, identify what the editor preferred. Use the `diff` field for word-level detail. Group findings into categories:

- **Vocabulary** -- different English word for same Hebrew concept (e.g., "atone for" -> "cover", "words" -> "matters")
- **Structure** -- clause reordering, fronting changes (e.g., moving subject before verb)
- **Brackets** -- changes to `{implied words}` (additions, removals, different wording)
- **Voice/form** -- passive to active, participle handling, tense changes

Look for patterns that appear 2+ times across verses (higher confidence). Single occurrences are noted but flagged as lower confidence.

**Editor-discretion patterns**: Some changes reflect case-by-case editorial judgment, not systematic preferences. Do not write these to glossary/quick-ref as AI rules. Instead, flag them as "editor discretion" in the report and log as situational. Known editor-discretion areas:
- **Participial noun expansion**: editor changes an agent noun to a fuller phrase (e.g., "his fearers" -> "the ones fearing him", "callers" -> "the ones calling"). The AI defaults to agent-noun -er forms; editors expand when context requires it. These are not vocabulary corrections.

Where possible, identify the Hebrew word or Strong's number involved. Check the Hebrew source at `data/hebrew_bible/` if needed for Strong's lookup.

### Step 4: Check existing memory and canonical sources before writing

Before adding any finding, run a two-phase check:

**Phase A -- Duplicate check** (existing memory):

```bash
grep -i "<Strong's number or Hebrew word>" data/glossary/project_glossary.md
grep "<Strong's number>" data/quick-ref/ult_decisions.csv 2>/dev/null
grep "<Strong's number>" data/quick-ref/ust_decisions.csv 2>/dev/null
```

If the editor's preference already matches what's in memory, skip it -- the system is already calibrated. Only write genuinely new findings.

**Phase B -- Canonical contradiction check**:

For each proposed write, grep the Hebrew word/Strong's number against the protected canonical files:
- `data/issues_resolved.txt` (highest authority, free-form text)
- All 5 Google Drive glossary CSVs (structured data)

Column mapping for canonical CSVs:
- `hebrew_ot_glossary.csv`: col 0 = Hebrew, col 4 = ULT GLOSS, col 5 = UST GLOSS
- `psalms_reference.csv`: col 0 = Hebrew, col 1 = ULT GLOSS, col 2 = UST GLOSS
- `sacrifice_terminology.csv`: col 0 = Hebrew, col 4 = ULT GLOSS, col 5 = UST GLOSS
- `biblical_phrases.csv`: col 1 = OrigL (Hebrew), col 4 = ULT GLOSS, col 5 = UST GLOSS

Decision logic:
- If a canonical source specifies a rendering and the editor's preference **contradicts** it: **block the write**. Log to `data/editor-feedback/proofreader_patterns.csv` with verdict `canonical_conflict`. Present the conflict in the Turn 3 report for escalation.
- If no canonical source addresses this term: proceed normally.
- If the canonical source matches the editor's preference: proceed (reinforces existing decision).

### Step 4b: Classify context-specificity

Between the Phase B check and Turn 3 writes, classify each accepted finding:

- **Single-Chapter Mode**: finding in only 1 verse = `context-specific`
- **Multi-Chapter Mode**: finding in only 1 chapter = `context-specific`; 2+ chapters = `general`

Context-specific items get scoped annotations when written to memory (see Turn 3).

### Step 5: Write full comparison report

Save to `output/editor-compare/{BOOK}/{BOOK}-{CHAPTER:03d}-{type}.md` with sections:
- Summary stats (total verses, changed count, unchanged count)
- Editor comments (if present from editor-feedback file)
- Vocabulary preferences (with Strong's where identified)
- Structural preferences
- Bracket changes
- Voice/form changes

Do NOT write to glossary, quick-ref, or any memory files yet. That happens after the editor approves in the adjudication protocol below.

### Step 6: Format discrepancy list for Zulip

Produce a numbered list of discrepancies for the editor to review. Rank by frequency/impact -- patterns appearing in 3+ verses first, then 2, then 1.

Each item shows:
1. **Number** (sequential)
2. **Verse reference** (chapter:verse; include chapter if multi-chapter review)
3. **Side-by-side**: AI original | Editor edit (only the changed phrase, not the full verse)
4. **One-line hypothesis** about why the editor changed it
5. **Category tag**: vocabulary / structure / brackets / voice

Example format:
```
1. **147:3** "he heals" -> "he is the one who heals" -- adds emphasis on agency (structure)
2. **147:5** "great" -> "mighty" -- stronger rendering of H1419 gadol (vocabulary, 3x in ch)
3. **147:8** "{rain}" -> "{showers}" -- bracket wording preference (brackets)
```

End with:
> Reply with which items to ignore (e.g. "not 2, 8"), mark as situational (e.g. "10 is situational"), or say "all good" to accept all. No @-mention needed.

Do NOT write to memory yet. Wait for the editor's response.

## Adjudication Protocol (Multi-Turn)

This skill runs as a multi-turn conversation. The system prompt handles the overall protocol; the steps below describe what to do at each turn.

### Turn 1 -- Present discrepancy list

Run Steps 1-6 above. Present the numbered discrepancy list in Zulip. Do not write to any memory/guidance files.

### Turn 2 -- Parse editor response and confirm

Parse the editor's natural language response. Supported patterns:
- "don't do 2, 8" / "not 2, 8" / "ai was right on 2, 8" -- ignore those items (keep AI version)
- "all good" / "yes to all" -- accept all human edits
- "for 10, that's situational" / "10 is situational" -- flag as context-dependent
- "1, 3-7, 9 only" -- accept only those, ignore the rest
- "3 is general" / "treat 3 as general" -- promotes a context-specific item to a general rule

Default rule: if an item is not explicitly mentioned as ignored or situational, the human edit is accepted. Items keep their inferred specificity level (from Step 4b) unless the editor explicitly promotes them with "is general" / "treat as general".

Confirm back in plain language:
> Applying human edits for items 1, 3-7, 9. Ignoring 2, 8 (keeping AI version, no glossary update). Item 10 flagged as situational. Anything to adjust?

Wait for the editor to approve before proceeding.

### Turn 3 -- Execute after approval

**For accepted items** -- write to memory using the logic below:

Ensure the quick-ref directory exists and CSV files have headers:

```python
import os
os.makedirs("data/quick-ref", exist_ok=True)
```

If `data/quick-ref/ult_decisions.csv` doesn't exist, create it with header:
```
Strong,Hebrew,Rendering,Book,Context,Notes,Date
```

If `data/quick-ref/ust_decisions.csv` doesn't exist, create it with header:
```
Strong,Hebrew,Rendering,Book,Context,Notes,Date
```

ULT vocabulary preferences -- append to `data/glossary/project_glossary.md` Words table:
```
| <Hebrew> | <Strong's> | <editor rendering> | <AI rendering> | editor <BOOK> <CH>:<VS> |
```
For context-specific items, append to the Notes column: `context-specific: <BOOK> <CH>:<VS> only`

ULT decisions with Strong's -- append to `data/quick-ref/ult_decisions.csv`:
```
<Strong's>,<Hebrew>,<editor rendering>,<BOOK>,<CH>:<VS> context description,<notes>,<date>
```
For context-specific items: use the Book column to scope (e.g., `PSA` not `ALL`) and add to Notes: `context-specific: applies to <BOOK> <CH>:<VS>; may differ elsewhere`

UST decisions with Strong's -- append to `data/quick-ref/ust_decisions.csv` (same format):
```
<Strong's>,<Hebrew>,<editor rendering>,<BOOK>,<CH>:<VS> context description,<notes>,<date>
```
Same context-specificity rules as ULT decisions above.

**For ignored items** (AI was right) -- log to `data/editor-feedback/proofreader_patterns.csv`:
```
<date>,<BOOK>,<CH>,<VS>,<Strong's>,<Hebrew>,<proofreader edit>,<AI original>,<hypothesis>,ignored
```
This surfaces proofreader patterns without corrupting the glossary/quick-ref.

**For situational items** -- add conditional entries with context:
- In quick-ref: add a notes field like "use X when Y, use Z when W"
- In glossary: note the condition in the source column

Report what was done (how many items updated, how many logged, how many situational, how many context-specific).

If any items were blocked by canonical contradiction (Phase B), add a section:

```
**Canonical conflicts (not written to memory):**
- Item 5: editor prefers "X" for H1234, but issues_resolved specifies "Y"
  (decision date). Escalate to content team to update the Google Sheet
  or issues_resolved if this should change.
```

End with "Review complete."


## Multi-Chapter Mode

Use when comparing multiple chapters at once (e.g., "editor-compare PSA 81-84, 87").

### Phase 0: Fetch editor USFM once

Fetch the full-book USFM from Door43 master once per type. The Door43 file is per-book (e.g., `19-PSA.usfm` contains all 150 chapters), so one fetch covers all chapters.

```bash
python3 .claude/skills/utilities/scripts/fetch_door43.py <BOOK> --type <ult|ust> --output /tmp/claude/editor_<type>.usfm
```

Do this for each type being compared (ULT, UST, or both).

### Phase 1: Parallel per-chapter comparison

Parse the chapter spec (e.g., "81-84, 87, 120-130") into a flat list of chapter numbers.

Run `prepare_compare.py` for each chapter in parallel, passing the pre-fetched file via `--editor-usfm`:

```bash
# Run all chapters in parallel (each as a separate subagent or background shell)
python3 .claude/skills/editor-compare/scripts/prepare_compare.py <BOOK> <CH> --type <type> \
    --editor-usfm /tmp/claude/editor_<type>.usfm \
    --output /tmp/claude/compare_<type>_<CH>.json
```

For each chapter, after reading its comparison JSON:
- Write a per-chapter report to `output/editor-compare/{BOOK}/{BOOK}-{CH:03d}-{type}.md`
- Do NOT write memory updates yet -- that happens in Phase 2

### Phase 2: Consolidated analysis

Read all per-chapter comparison JSONs together. Perform cross-chapter pattern detection:

1. **Count occurrences**: For each vocabulary/structure preference, count how many chapters show it
2. **Confidence levels**:
   - **High** (3+ chapters): Strong pattern
   - **Medium** (2 chapters): Likely pattern
   - **Low** (1 chapter): Note only
3. **Check existing memory**: Skip preferences already captured in glossary/quick-ref
4. **Write consolidated report**: Save to `output/editor-compare/{BOOK}/{BOOK}-multi-{type}.md` with:
   - Per-chapter summaries (changed/unchanged counts)
   - Cross-chapter patterns with confidence levels and chapter citations
   - Low-confidence observations
5. **Present discrepancy list**: Use Step 6 format (numbered, ranked by frequency). Then follow the Adjudication Protocol for Turns 2-3. Memory writes only happen after editor approval.

## Key Design Points

- **Script-first**: The Python script handles fetching, AST-based parsing (via parse_usfm.js), and diffing. The AI handles pattern analysis and memory writes.
- **HTTP fetch**: The script fetches from unfoldingWord Door43 master via HTTP. Editor-feedback files are provided via `--editor-file`. Pre-fetched USFM (for multi-chapter mode) is provided via `--editor-usfm`.
- **AST parsing**: Both aligned and unaligned USFM go through `parse_usfm.js --plain-only` for consistent plain text extraction, replacing the old regex chain.
- **Inference-based**: The common case has no prose feedback. Infer all editor preferences from verse diffs alone. When prose comments are available, they carry high weight.
- **Two-phase multi-chapter**: Phase 1 runs chapters in parallel without writing to shared files. Phase 2 consolidates findings and writes memory updates, ensuring cross-chapter patterns are detected before committing to memory.
- **Light hand**: The report suggests patterns; the human decides what to adopt. Note confidence levels (multi-verse pattern vs. single occurrence).
