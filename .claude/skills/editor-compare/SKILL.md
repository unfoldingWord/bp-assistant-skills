---
name: editor-compare
description: Compare editor-edited ULT/UST against AI output to identify editor preferences and feed them back into memory.
allowed-tools: Read, Grep, Glob, Bash, Write, Edit
---

# Editor Compare

Compare editor-edited text against AI-generated ULT/UST to identify vocabulary, structure, and style preferences. Feeds findings back into the project glossary and quick-ref decisions files.

## Prerequisites

- AI output in `output/AI-ULT/` or `output/AI-UST/` (from ULT-gen or UST-gen)
- Editor source: Door43 master (HTTP fetch) or editor-feedback file

## Single-Chapter Mode

### Step 1: Run the comparison script

Run once per type. If the user doesn't specify a type, run for both ult and ust (skip if AI output doesn't exist for that type).

```bash
python3 .claude/skills/editor-compare/scripts/prepare_compare.py <BOOK> <CHAPTER> --type <ult|ust> \
    --output /tmp/claude/compare_<type>.json
```

If the user provides an editor-feedback file:
```bash
python3 .claude/skills/editor-compare/scripts/prepare_compare.py <BOOK> <CHAPTER> --type <ult|ust> \
    --editor-file "<path>" --output /tmp/claude/compare_<type>.json
```

The script uses `parse_usfm.js` (AST-based parser) for plain text extraction. It handles both aligned USFM (with `\zaln` markers from Door43 master) and unaligned USFM (AI output) through the same code path.

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

Where possible, identify the Hebrew word or Strong's number involved. Check the Hebrew source at `data/hebrew_bible/` if needed for Strong's lookup.

### Step 4: Check existing memory before writing

Before adding any finding, check if it already exists:

```bash
grep -i "<Strong's number or Hebrew word>" data/glossary/project_glossary.md
grep "<Strong's number>" data/quick-ref/ult_decisions.csv 2>/dev/null
grep "<Strong's number>" data/quick-ref/ust_decisions.csv 2>/dev/null
```

If the editor's preference already matches what's in memory, skip it -- the system is already calibrated. Only write genuinely new findings.

### Step 5: Write to memory

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

**ULT vocabulary preferences** -- append to `data/glossary/project_glossary.md` Words table:
```
| <Hebrew> | <Strong's> | <editor rendering> | <AI rendering> | editor <BOOK> <CH>:<VS> |
```

**ULT decisions with Strong's** -- append to `data/quick-ref/ult_decisions.csv`:
```
<Strong's>,<Hebrew>,<editor rendering>,<BOOK>,<CH>:<VS> context description,<notes>,<date>
```

**UST decisions with Strong's** -- append to `data/quick-ref/ust_decisions.csv` (same format):
```
<Strong's>,<Hebrew>,<editor rendering>,<BOOK>,<CH>:<VS> context description,<notes>,<date>
```

### Step 6: Write comparison report

Save to `output/editor-compare/{BOOK}/{BOOK}-{CHAPTER:03d}-{type}.md` with sections:
- Summary stats (total verses, changed count, unchanged count)
- Editor comments (if present from editor-feedback file)
- Vocabulary preferences (with Strong's where identified)
- Structural preferences
- Bracket changes
- Voice/form changes
- Memory updates applied (list what was written to glossary/quick-ref)


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
   - **High** (3+ chapters): Strong pattern, write to memory
   - **Medium** (2 chapters): Likely pattern, write to memory
   - **Low** (1 chapter): Note only, do not write to memory
3. **Check existing memory**: Skip preferences already captured in glossary/quick-ref
4. **Write memory updates**: For high and medium confidence only (Steps 4-5 from single-chapter mode)
5. **Write consolidated report**: Save to `output/editor-compare/{BOOK}/{BOOK}-multi-{type}.md` with:
   - Per-chapter summaries (changed/unchanged counts)
   - Cross-chapter patterns with confidence levels and chapter citations
   - Memory updates applied
   - Low-confidence observations (noted but not written to memory)

## Key Design Points

- **Script-first**: The Python script handles fetching, AST-based parsing (via parse_usfm.js), and diffing. The AI handles pattern analysis and memory writes.
- **HTTP fetch**: The script fetches from unfoldingWord Door43 master via HTTP. Editor-feedback files are provided via `--editor-file`. Pre-fetched USFM (for multi-chapter mode) is provided via `--editor-usfm`.
- **AST parsing**: Both aligned and unaligned USFM go through `parse_usfm.js --plain-only` for consistent plain text extraction, replacing the old regex chain.
- **Inference-based**: The common case has no prose feedback. Infer all editor preferences from verse diffs alone. When prose comments are available, they carry high weight.
- **Two-phase multi-chapter**: Phase 1 runs chapters in parallel without writing to shared files. Phase 2 consolidates findings and writes memory updates, ensuring cross-chapter patterns are detected before committing to memory.
- **Light hand**: The report suggests patterns; the human decides what to adopt. Note confidence levels (multi-verse pattern vs. single occurrence).
