---
name: issue-to-tn
description: Convert issue identification TSV to TN-ready format via tnwriter-dev pipeline. Runs language conversion and/or AI note generation.
---

# Issue to Translation Notes

Processes issue TSV files (from issue-identification output) through the tnwriter-dev pipeline to generate complete translation notes.

## What This Does

1. **Language Conversion** - Converts English ULT quotes to Hebrew, generates unique IDs
2. **AI Note Generation** - Creates translation notes based on issue type and context

## Prerequisites

- tnwriter-dev installed at `/home/bmw/Documents/dev/tnwriter-dev`
- Virtual environment with dependencies: `/home/bmw/Documents/dev/tnwriter-dev/venv`
- Input TSV in `output/issues/` directory

## Usage

### Full Processing with USFM Context (Recommended)

Pass the plain USFM files from issue-identification to provide verse context for AI note generation:

```bash
cd /home/bmw/Documents/dev/tnwriter-dev && \
./venv/bin/python tsv_processor.py \
    /home/bmw/Documents/dev/cSkillBP/output/issues/PSA-058.tsv \
    /home/bmw/Documents/dev/cSkillBP/output/notes/PSA-058.tsv \
    --ult-usfm /tmp/ult_plain.usfm \
    --ust-usfm /tmp/ust_plain.usfm \
    --no-ai-limit
```

The `/tmp/ult_plain.usfm` and `/tmp/ust_plain.usfm` files are created by the issue-identification agent during its workflow. If they don't exist, fetch and parse them:

```bash
# Fetch ULT/UST
python3 .claude/skills/utilities/scripts/fetch_door43.py PSA > /tmp/book_ult.usfm
python3 .claude/skills/utilities/scripts/fetch_door43.py PSA --type ust > /tmp/book_ust.usfm

# Parse to plain text
node .claude/skills/utilities/scripts/usfm/parse_usfm.js /tmp/book_ult.usfm --plain-only > /tmp/ult_plain.usfm
node .claude/skills/utilities/scripts/usfm/parse_usfm.js /tmp/book_ust.usfm --plain-only > /tmp/ust_plain.usfm
```

### Language Conversion Only

Get Hebrew quotes and IDs without AI note generation:

```bash
cd /home/bmw/Documents/dev/tnwriter-dev && \
./venv/bin/python tsv_processor.py \
    /home/bmw/Documents/dev/cSkillBP/output/issues/PSA-058.tsv \
    /home/bmw/Documents/dev/cSkillBP/output/converted/PSA-058.tsv \
    --language-only
```

### Dry Run (Preview)

```bash
cd /home/bmw/Documents/dev/tnwriter-dev && \
./venv/bin/python tsv_processor.py \
    /home/bmw/Documents/dev/cSkillBP/output/issues/PSA-058.tsv \
    /home/bmw/Documents/dev/cSkillBP/output/test.tsv \
    --dry-run
```

## Input Format

cSkillBP issue TSV (no headers, tab-separated):

```
psa	65:1	figs-activepassive	a vow will be paid			passive - by whom? worshippers
```

Columns (positional):
1. Book code (psa)
2. Reference (65:1)
3. Issue type (figs-activepassive)
4. ULT quote (a vow will be paid)
5. Go? flag (empty = LA)
6. AT (usually empty)
7. Explanation (passive - by whom? worshippers)

## Output Format

TN-ready TSV (7 columns with headers):

```
Reference	ID	Tags	SupportReference	Quote	Occurrence	Note
65:1	a1b2		rc://*/ta/man/translate/figs-activepassive	[Hebrew]	1	[AI-generated note]
```

## Processing Modes

| Mode | Flag | Description |
|------|------|-------------|
| LA | (default) | Language conversion + AI note generation |
| L | `--language-only` or `--mode L` | Language conversion only |
| AI | `--mode AI` | AI only (assumes Hebrew already present) |

## Options

| Option | Description |
|--------|-------------|
| `--book CODE` | Override book code (auto-detected from filename) |
| `--mode L/LA/AI` | Processing mode |
| `--language-only` | Shortcut for `--mode L` |
| `--ult-usfm PATH` | Path to plain ULT USFM for verse context |
| `--ust-usfm PATH` | Path to plain UST USFM for verse context |
| `--no-ai-limit` | Remove 10-item limit on AI processing |
| `--dry-run` | Preview without processing |
| `--max-items N` | Limit items to process |
| `--verbose` | Enable debug logging |
