---
name: align-all-parallel

description: Run ULT-alignment and UST-alignment in parallel as subagents for a chapter.

allowed-tools: Task, Bash
---

## Quick Alignment Pipeline

Spawn both alignment agents in parallel and wait for both to complete.

## Input

- **Book**: 3-letter abbreviation (PSA, GEN, 2SA, etc.)
- **Chapter**: number

## Model

This skill is coordination only -- run it as **haiku**. The alignment subagents require linguistic judgment -- spawn each with `model: "sonnet"`.

## What Happens

1. Spawns `ult-align` subagent (`model: "sonnet"`, runs ULT-alignment skill)
2. Spawns `ust-align` subagent (`model: "sonnet"`, runs UST-alignment skill)
3. Waits for both to complete
4. Reports when both alignments are done

## Output

- `output/AI-ULT/<BOOK>/<BOOK>-<CH>-aligned.usfm` - ULT with word-level alignments
- `output/AI-UST/<BOOK>/<BOOK>-<CH>-aligned.usfm` - UST with phrase-level alignments

Both are ready for insertion into Door43 repos.

## Usage

```
/align-all-parallel psa 124
```

That's it. Two agents spin up in parallel, you wait, both alignments are done.
