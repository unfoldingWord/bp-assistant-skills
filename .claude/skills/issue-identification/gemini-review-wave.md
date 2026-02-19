# Gemini Review Wave

Run Gemini CLI as an independent reviewer after the merge writes final output.
Skip if `--skip-gemini` is passed.

## Command

```bash
python3 .claude/skills/utilities/scripts/gemini_review.py --stage <STAGE> --book <BOOK> --chapter <CHAPTER>
```

## Stages by Orchestrator

| Orchestrator | Stages |
|--------------|--------|
| deep-issue-id | `issues` only |
| initial-pipeline | `ult`, `issues`, `ust` |

## Exit Code Handling

| Code | Meaning | Action |
|------|---------|--------|
| 0 | No findings | Continue |
| 1 | Findings present | Read `output/review/<BOOK>/<BOOK>-<CH>-{stage}-gemini.md`, evaluate each |
| 2 | Gemini failed (rate limit, timeout) | Log and continue, don't block |

## Evaluate-and-Fix Loop

For exit code 1: Claude reads each finding, checks it against the actual
guideline doc. If legit, fix the output file. If false positive, ignore.
This is a judgment loop, not a pass-through report.
