# TN Quality Checker -- Design Plan

## Decision Record

**Chosen approach**: Tiered (fast script + deep prompt review)

### Approaches Considered

**A. Single-pass checker**: One script for mechanical checks, then Claude does semantic review. Simple but no way to run just the fast checks during iteration.

**B. Tiered checker (chosen)**: A "fast" script-only mode for mechanical checks. A "deep" mode that adds semantic review via Claude. Fast mode is cheap enough to run after every tn-writer step; deep mode is for final quality gate.

**C. Per-note checker**: Script checks each note individually against its prepared_notes.json entry. Overkill for mechanical checks; semantic review still needs verse context.

Approach B was chosen because the PSA 147-149 feedback identified a need for "a separate agent at the end of any process that just checks that you did all of what you were told to do." Fast mode fills that gap cheaply.

---

## Architecture

### Inputs

- Final assembled TSV (from tn-writer Step 8-9, e.g. `output/notes/PSA/PSA-147.tsv`)
- `prepared_notes.json` (from tn-writer Step 2a)
- Plain ULT USFM (`/tmp/claude/ult_plain.usfm`)
- Plain UST USFM (`/tmp/claude/ust_plain.usfm`)
- Book code (e.g. PSA) -- for fetching master TN to check ID collisions

### Outputs

- Findings JSON at `/tmp/claude/tn_quality_findings.json`
- Human-readable report at `output/quality/<BOOK>-<CHAPTER>-quality.md`

### Modes

- `--fast` (default): Script-only mechanical checks. Instant. Returns findings JSON.
- `--deep`: Script checks + Claude semantic review. Slower. Returns full report.

---

## Mechanical Checks (Script)

All checks run by `check_tn_quality.py`. Each finding has a severity (error/warning) and a category.

### 1. ID format
- Rule: Each ID must match `[a-z][a-z0-9]{3}` (4 chars, first must be lowercase letter)
- Severity: error
- Skip: intro rows (Occurrence = 0)

### 2. ID uniqueness (within file)
- Rule: No duplicate IDs in the output TSV
- Severity: error

### 3. ID collisions with master TN
- Rule: No ID in the output TSV should already exist in the published master TN for that book
- Implementation: Fetch master TN from Door43 (`git.door43.org/unfoldingWord/en_tn`), extract IDs for the book, compare. Delete the fetched file after check.
- Severity: error

### 4. Empty Hebrew quote
- Rule: Quote column must contain RTL Hebrew characters (for non-intro rows)
- Severity: error

### 5. AT bracket syntax
- Rule: Alternate translations must use `[square brackets]`, not `"quotes"` or other delimiters
- Check: If note contains `Alternate translation:`, verify text after it uses `[...]`
- Severity: error

### 6. AT does not match UST
- Rule: The AT text (inside brackets) must NOT be identical to the UST phrasing for that verse
- Implementation: Extract AT text, extract UST verse from prepared_notes.json, check for exact substring match
- Severity: warning (exact match = error, high overlap = warning)

### 7. GL quote found in ULT verse
- Rule: The gl_quote (from prepared_notes.json) must appear in the ULT verse text
- Implementation: Reuse the substitute logic from verify_at_fit.py (case-insensitive, strip braces)
- Severity: error if not found

### 8. Bold accuracy
- Rule: Any `**bolded text**` in the note must appear verbatim in the ULT verse for that reference
- Implementation: Extract all `**...**` spans, check each against ULT verse text
- Severity: error

### 9. No rc:// links in Note column
- Rule: The Note text must not contain `rc://` links (those belong in the SupportReference column only)
- Exception: Chapter intro rows (out of scope for this checker)
- Severity: error

### 10. Orphaned conjunctions/prepositions in AT substitution
- Rule: After substituting AT for gl_quote in ULT verse, check if the word immediately before the AT is a lonely conjunction (And, But, So, Then, Or) or preposition (in, to, from, by, for, with, on, at, of) that isn't incorporated into the AT
- Implementation: Perform the substitution, check the preceding word
- Severity: warning

### 11. "The writer" in Psalms
- Rule: In Psalms, notes should use "the psalmist" or the attributed author name, never "the writer"
- Implementation: If book is PSA, check for "the writer" (case-insensitive) in Note column
- Severity: warning

### 12. Curly/smart quotes
- Rule: No straight quotes (`"` or `'`) should remain; all should be curly
- Implementation: Check Note column for straight quote characters
- Exception: Within markdown bold markers or code spans
- Severity: warning

### 13. Capitalization in ATs
- Rule: If gl_quote appears at start of verse/after period, AT first word should be capitalized; if mid-sentence, lowercase
- Implementation: Find gl_quote position in ULT verse, check AT first character case
- Severity: warning

---

## Semantic Checks (Prompt -- deep mode only)

Claude reads the findings JSON plus the full TSV and prepared_notes.json to review:

### 1. Note addresses correct issue type
- Does a figs-metaphor note actually discuss metaphor using the standard verbiage?
- Does a figs-parallelism note describe parallel phrases?
- Cross-reference SupportReference against note content.

### 2. Template adherence
- Does the note follow the standard verbiage from the style guide Figure of Speech table?
- Is the note structure consistent with the template pattern?

### 3. AT naturalness (full substitution review)
- Read each AT substitution (gl_quote replaced by AT in ULT verse) as a complete sentence
- Flag any that read unnaturally, have broken grammar, or orphan words at boundaries

### 4. Antithetical parallelism filtering
- If a figs-parallelism note exists, check whether the two phrases express opposite ideas (antithetical) rather than similar ideas (synonymous). Antithetical parallelism should not get parallelism notes.

### 5. Note suppression opportunities
- If a semantic note (idiom, metaphor, metonymy) covers the same phrase as a structural note (possession, activepassive), flag the structural note as potentially redundant.

### 6. Duplicate/combinable notes
- Flag notes for the same verse that could be combined (e.g., two grammar-connect notes for the same connector pattern, or possession notes made redundant by other issue types).

### 7. "Here" rule compliance
- If a note starts with "Here, ", verify the next word is a bolded quote from the verse starting with lowercase.

---

## Implementation Plan

### Files to create

1. `.claude/skills/tn-quality-check/SKILL.md` -- Skill definition with workflow
2. `.claude/skills/tn-quality-check/scripts/check_tn_quality.py` -- Mechanical checks script

### Script design (`check_tn_quality.py`)

**Inputs (CLI args)**:
- `tsv_path` -- Path to assembled TN TSV
- `--prepared-json` -- Path to prepared_notes.json
- `--ult-usfm` -- Path to plain ULT USFM
- `--ust-usfm` -- Path to plain UST USFM
- `--book` -- Book code (for master TN ID collision check)
- `--output` -- Output findings JSON path (default: `/tmp/claude/tn_quality_findings.json`)

**Output JSON structure**:
```json
{
  "summary": {
    "total_notes": 50,
    "errors": 3,
    "warnings": 7,
    "passed": 40
  },
  "findings": [
    {
      "row": 5,
      "reference": "147:3",
      "id": "2414",
      "category": "bold_accuracy",
      "severity": "error",
      "message": "Bolded text \"healed\" not found in ULT verse",
      "details": { "bolded": "healed", "ult_verse": "He is healing..." }
    }
  ]
}
```

### SKILL.md workflow

1. Run `check_tn_quality.py` with all inputs (fast mode stops here)
2. Read findings JSON, report counts
3. (Deep mode) Claude reads findings + TSV + prepared_notes.json
4. Claude performs semantic checks, appending to findings
5. Write final report to `output/quality/`

### Dependencies

- `verify_at_fit.py` substitute logic (import or duplicate the key function)
- Door43 fetch for master TN (use existing fetch_door43.py pattern, or curl)
- ULT/UST USFM parsing (reuse from prepare_notes.py)
