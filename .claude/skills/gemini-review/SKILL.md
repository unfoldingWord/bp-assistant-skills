---
name: gemini-review
description: Run Gemini CLI as an independent second-opinion reviewer for pipeline output. Catches blindspots from single-model review.
---

# Gemini Independent Review

Runs Google's Gemini model as an independent reviewer for pipeline output. Provides a second set of eyes to catch issues that a single model reviewing its own work might miss.

## How It Works

A Python script constructs a stage-specific review prompt, tells Gemini to read the output files and guideline docs directly from the workspace, and writes structured findings to `output/review/`.

Claude then reads the findings, evaluates each one against the actual guidelines, and fixes output files where findings are legitimate. False positives are ignored.

## Usage

```bash
python3 .claude/skills/utilities/scripts/gemini_review.py \
    --stage {ult|issues|ust|notes|alignment-ult|alignment-ust} \
    --book PSA --chapter 65 \
    [--dry-run]           # Print prompt, don't call Gemini
    [--output PATH]       # Override output path
    [--model MODEL]       # Override model (default: gemini-2.5-flash)
    [--timeout SECONDS]   # Override timeout (default: 180)
```

## Stages

| Stage | What it reviews | Cross-references |
|-------|----------------|------------------|
| `ult` | AI-ULT USFM | -- |
| `issues` | Issues TSV | AI-ULT USFM |
| `ust` | AI-UST USFM | AI-ULT USFM |
| `notes` | Notes TSV | AI-ULT + AI-UST USFM |
| `alignment-ult` | Aligned ULT USFM | -- |
| `alignment-ust` | Aligned UST USFM | -- |

## Output

Written to: `output/review/{BOOK}/{BOOK}-{CH}-{stage}-gemini.md`

Format is a markdown file with a findings table:
```
## Findings
| Ref | Severity | Finding |
|-----|----------|---------|
| 65:2 | major | ... |

## Summary
X findings (Y major, Z minor)
```

## Exit Codes

| Code | Meaning |
|------|---------|
| 0 | No findings -- output is clean |
| 1 | Findings present -- Claude should read and evaluate |
| 2 | Gemini failed (rate limit, timeout, CLI not found) |

## Integration Pattern

When calling from other skills (initial-pipeline, tn-writer, alignment skills):

```
1. Run: python3 .claude/skills/utilities/scripts/gemini_review.py --stage X --book B --chapter C
2. If exit code 2: log and continue (don't block pipeline)
3. If exit code 0: no findings, continue
4. If exit code 1: read output/review/{B}/{B}-{CH}-{stage}-gemini.md
5. For each finding: check against actual guideline doc. If legit, fix output. If false positive, ignore.
6. Continue pipeline
```

Skip with `--skip-gemini` flag on the orchestrator.

## Practical Notes

- Uses Gemini CLI headless mode: `gemini -p "prompt" -o text -y`
- `-y` (yolo mode) lets Gemini read workspace files directly
- Free tier may hit 429 rate limits; CLI has built-in retry with backoff
- Script adds its own 180s timeout on top of CLI retry
- Stderr filtered (deprecation warnings)
- Complementary to tn-quality-check (which does mechanical checks); Gemini review does semantic/judgment checks

## Prompt Files

Stage-specific review prompts live in:
`.claude/skills/utilities/prompts/gemini-review/{stage}.md`

Each prompt tells Gemini what to check and what NOT to check (avoiding duplication with mechanical validation).
