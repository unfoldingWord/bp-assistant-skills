# editor-compare Skill

## Context

When humans edit AI-generated ULT/UST, their changes reveal preferences the AI should learn from. Currently there is no systematic way to capture those preferences. This skill compares editor-edited text from Door43 master against our AI output, identifies patterns purely by inference from the diffs, and feeds findings back into the ULT memory system (project glossary, quick-ref CSV) and an interim UST notes file.

Detailed execution plan: `/tmp/claude-1000/-home-bmw-Documents-dev-cSkillBP/6c96fe55-7cf4-4701-a8ed-f33abbbc043a/scratchpad/editor-compare-exec.md`

## Files to Create

```
.claude/skills/editor-compare/
  SKILL.md                        # Skill definition
  scripts/
    prepare_compare.py            # Deterministic comparison script
```

## 1. Script: `prepare_compare.py`

Prepares verse-by-verse comparison JSON. The AI then analyzes it.

**Arguments:**
```
python3 .claude/skills/editor-compare/scripts/prepare_compare.py PSA 65 --type ult
```
- `book` (positional): abbreviation (PSA, GEN, etc.)
- `chapter` (positional): number
- `--type`: `ult` or `ust` (default: `ult`)
- `--output`: JSON path (default: stdout)
- `--editor-file`: explicit override path to editor USFM

**Editor source resolution (in order):**
1. `--editor-file` if provided (for rare editor-feedback files with prose comments -- weigh those heavily)
2. Local git clone at `$DOOR43_REPOS_PATH/en_{type}/` (read from `.env`, run `git pull` first)
3. HTTP fetch from `unfoldingWord/en_{type}` master via Door43

The normal case is #2 or #3 -- fetching from master where there are no prose comments. The skill must infer editor preferences purely from the diffs. Editor-feedback files (#1) are rare but high-value when available.

**AI source:** `output/AI-{ULT|UST}/{BOOK}-{CHAPTER:03d}.usfm`

**Reuses existing code:**
- Import `strip_alignment_markers` from `extract_ult_english.py` (`.claude/skills/utilities/scripts/extract_ult_english.py`)
- Import `BOOK_NUMBERS`, `normalize_book`, `get_filename`, `build_url` from `fetch_door43.py` (`.claude/skills/utilities/scripts/fetch_door43.py`)

**Processing:**
- Read `.env` for `DOOR43_REPOS_PATH` (used for local clone path)
- If using local clone: `git -C $DOOR43_REPOS_PATH/en_{type} pull` before reading
- Strip alignment markers from editor file (master USFM has zaln markers; no-op if already plain)
- Extract target chapter from full-book file using `\c N` markers
- If `--editor-file` provided: extract prose comments before first `\c` marker (editor-feedback files may have these)
- Parse `\v` markers into verse dict, strip USFM formatting (`\q1`, `\q2`, etc.) to plain text
- Compare verse-by-verse using `difflib.SequenceMatcher` at word level
- Categorize changes heuristically: vocabulary, restructuring, bracket_change, voice_change, formatting

**Output JSON:**
```json
{
  "book": "PSA", "chapter": 65, "type": "ult",
  "source": "local_clone",
  "editor_comments": null,
  "verses": [
    {
      "verse": 1,
      "ai": "To you {there is} silence, praise, God...",
      "editor": "Praise {is in} silence toward you, God...",
      "changed": true
    }
  ],
  "summary": { "total": 13, "changed": 10, "unchanged": 3 }
}
```

## 2. SKILL.md

```yaml
---
name: editor-compare
description: Compare editor-edited ULT/UST against AI output to identify editor preferences and feed them back into memory.
allowed-tools: Read, Grep, Glob, Bash, Write, Edit
---
```

**Workflow in SKILL.md:**

### Step 1: Run prepare script
Run once per type. If no type specified, run for both ult and ust (skipping if AI output doesn't exist for a type).

### Step 2: Read the comparison JSON
If editor_comments is present (rare, from --editor-file), note them -- these carry high weight as direct editor explanations.

### Step 3: Analyze changed verses (inference from diffs)
For each changed verse, identify what the editor preferred. Group into categories:
- **Vocabulary** -- different English word for same Hebrew (e.g., "atone for" -> "cover")
- **Structure** -- clause reordering, fronting changes
- **Brackets** -- changes to `{implied words}`
- **Voice/form** -- passive->reflexive, participle handling, tense changes

Focus on patterns appearing 2+ times (single occurrences noted with lower confidence).

### Step 4: Check existing memory before writing
Grep project_glossary.md and ult_decisions.csv for Strong's numbers. If editor preference already matches memory, skip (system is calibrated). Only write new findings.

### Step 5: Write to memory

**ULT vocabulary preferences** -> append to `data/glossary/project_glossary.md` (Words table):
```
| כָּפַר | H3722 | cover | atone for | editor PSA 65:3 |
```

**ULT decisions with Strong's** -> append to `data/quick-ref/ult_decisions.csv` (create with header if missing):
```
Strong,Hebrew,Rendering,Book,Context,Notes,Date
```

**UST findings** -> append to `data/quick-ref/ust_editor_notes.csv` (create with header if missing):
```
Book,Chapter,Verse,Category,AIText,EditorText,Notes,Date
```
The skill checks if this file exists, creates if not. Notes that this is interim until a proper UST memory system is built.

### Step 6: Write comparison report
Save to `output/editor-compare/{BOOK}-{CHAPTER}-{type}.md` with sections:
- Summary stats
- Editor comments (if present)
- Vocabulary preferences (with Strong's where identifiable)
- Structural preferences
- Bracket changes
- Voice/form changes
- Memory updates applied

## Key Design Decisions

- **Script-first**: Script handles fetching, parsing, diffing. AI handles pattern analysis and memory writes.
- **Local clone primary**: Default to local git clone (pulls fresh), falls back to HTTP fetch. Editor-feedback files only via `--editor-file` flag.
- **Inference-based**: The common case has no prose feedback. The skill infers all editor preferences from verse diffs alone. When editor-feedback files are provided via flag, their prose comments carry high weight.
- **UST flexibility**: Check for UST memory system, use interim CSV, note it's temporary.
- **Light hand**: Nudges, not mandates. The report suggests; human decides what to adopt.

## Critical Files to Reuse

| File | What to reuse |
|------|--------------|
| `.claude/skills/utilities/scripts/extract_ult_english.py` | `strip_alignment_markers()` |
| `.claude/skills/utilities/scripts/fetch_door43.py` | `BOOK_NUMBERS`, `normalize_book`, `get_filename`, `build_url`, fetch logic |
| `data/glossary/project_glossary.md` | Append vocabulary findings (Words and Phrases tables) |
| `data/quick-ref/ult_decisions.csv` | Append decisions (create if missing) |
| `.claude/skills/tn-writer/SKILL.md` | Pattern for script-first skill (prepare script -> AI analysis -> output) |

## Verification

1. Run script on PSA 65 ULT using local clone (default path):
   ```bash
   python3 .claude/skills/editor-compare/scripts/prepare_compare.py PSA 65 --type ult
   ```
   Verify JSON output has 13 verses with changed/unchanged breakdown.

2. Run script with editor-feedback file (rare case, prose comments):
   ```bash
   python3 .claude/skills/editor-compare/scripts/prepare_compare.py PSA 66 --type ult \
       --editor-file "data/editor-feedback/Psalm 66 ULT.usfm"
   ```
   Verify editor_comments field is populated, source shows "editor_file".

3. Run script with HTTP fallback (when local clone unavailable):
   ```bash
   python3 .claude/skills/editor-compare/scripts/prepare_compare.py PSA 67 --type ult
   ```

4. Run full skill `/editor-compare psa 65` and verify:
   - Comparison report written to `output/editor-compare/PSA-065-ult.md`
   - Memory files updated only with new findings
   - No duplicate entries in project_glossary.md
