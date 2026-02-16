---
name: editor-compare
description: Compare editor-edited ULT/UST against AI output to identify editor preferences and feed them back into memory.
allowed-tools: Read, Grep, Glob, Bash, Write, Edit
---

# Editor Compare

Compare editor-edited text against AI-generated ULT/UST to identify vocabulary, structure, and style preferences. Feeds findings back into the project glossary and quick-ref decisions files.

## Prerequisites

- AI output in `output/AI-ULT/` or `output/AI-UST/` (from ULT-gen or UST-gen)
- Editor source: Door43 master (local clone or HTTP) or editor-feedback file

## Workflow

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

**Important**: The script automatically handles aligned USFM with `\zaln` markers via `extract_ult_english.py`. Do not manually parse aligned USFM. If you need plain English text outside the script:
```bash
python3 .claude/skills/utilities/scripts/extract_ult_english.py <file.usfm>
```

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

## Key Design Points

- **Script-first**: The Python script handles fetching, parsing, alignment stripping, and diffing. The AI handles pattern analysis and memory writes.
- **Local clone preferred**: The script tries local git clone first (with `git pull`), then falls back to HTTP fetch. Editor-feedback files are provided via `--editor-file` only.
- **Inference-based**: The common case has no prose feedback. Infer all editor preferences from verse diffs alone. When prose comments are available, they carry high weight.
- **Light hand**: The report suggests patterns; the human decides what to adopt. Note confidence levels (multi-verse pattern vs. single occurrence).
