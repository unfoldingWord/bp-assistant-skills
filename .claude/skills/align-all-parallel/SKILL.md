---
name: align-all-parallel

description: Run ULT-alignment and UST-alignment in parallel for a single chapter. Use when asked to align both ULT and UST or run all alignments for a chapter.

allowed-tools: Task, Bash
---

## Quick Alignment Pipeline

Spawn both alignment agents in parallel and wait for both to complete.

## Pipeline Context

If `--context <path>` is provided, read the context.json file. It contains the authoritative source paths:
- `sources.ult` — the ULT to align (may be a freshly generated file, not Door43 master)
- `sources.ust` — the UST to align
- `sources.hebrew` — Hebrew source file

Pass the ULT and UST paths to the alignment subagents so they align the correct files. Include these in the subagent prompts, e.g.: `PSA 35 --ult output/AI-ULT/PSA/PSA-035.usfm`

## Input

- **Book**: 3-letter abbreviation (PSA, GEN, 2SA, etc.)
- **Chapter**: number
- **--context** (optional): path to pipeline context.json

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
