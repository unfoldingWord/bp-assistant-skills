---
name: tn-quick
description: Quick scratchpad translation note writing. Use when asked to write a note on a phrase, add a note to scratch, or do quick TN work outside the full pipeline.
---

# Quick Translation Note Writer

Write individual translation notes to `output/scratch.txt` without running the full tn-writer pipeline.

## Workflow

1. User says "note on X in BOOK C:V" (optionally specifying the issue type)
2. Read the ULT verse from `data/door43_repos/en_ult/` (strip alignment markup mentally)
3. Read the UST verse from `data/door43_repos/en_ust/` for AT comparison
4. Look up the template: `grep '<issue_type>' data/templates.csv`
5. Write the note following the template and style rules below
6. Append to `output/scratch.txt` in this format — each field on its own line for easy copying in a web GUI:

```
--- BOOK C:V ISSUE_TYPE ---
rc://*/ta/man/translate/ISSUE_TYPE
HEBREW_QUOTE
NOTE_TEXT
```

Use a placeholder ID (abc1, abc2, etc., incrementing from what's already in the file). Leave Hebrew quote blank if not readily available.

7. After appending, run the fix_quotes script to convert any straight quotes to curly quotes:
   ```
   python3 .claude/skills/tn-quick/fix_quotes.py output/scratch.txt
   ```

## Style Rules

### Templates
- Use the template from `data/templates.csv` as closely as possible
- Replace ALL CAPS placeholders with context from the verse
- Resolve slashes by picking the appropriate word
- Do not rephrase or condense template wording

### Alternate Translations
- Enclose in square brackets: `Alternate translation: [text here]`
- Must fit seamlessly: removing the quoted phrase from the ULT and inserting the AT should read as natural English
- Must differ from UST phrasing for the same verse
- Minimal change to ULT wording -- only change what the issue requires
- No punctuation at start/end of brackets unless the note is about punctuation
- Match capitalization to sentence position of the quoted phrase

### Bold and Quoting
- Bold words/phrases quoted from the verse: `**quoted words**`
- Only bold the first occurrence
- Match capitalization and grammatical forms exactly from the ULT

### Quotation Marks
- Use Unicode curly quotes in note body text: " " (U+201C/U+201D) and ' ' (U+2018/U+2019)
- Never use straight quotes (" or ') in prose — curly quotes only
- Alternate translation brackets `[]` are unaffected

### Author References
- Always use the author's name, never "the author." Replace the SPEAKER placeholder in templates with the name (e.g., Habakkuk, Isaiah, Moses)
- For Psalms, check the superscription: use David, Asaph, etc. if named; use "the psalmist" if anonymous

### "Here" Rule
- Only start with "Here, " if immediately followed by a **bolded lowercase quote**: `Here, **admonish** means...`
- Never: `Here the author is speaking...` or `Here Habakkuk is saying...`

### Restrictions
- No source language names (Hebrew, Greek, Aramaic) in note text
- No linguistic jargon not present in the template (no "cognate accusative," "genitive," etc.)
- No "could mean" (reserved for TCM multi-interpretation notes)
- No extra explanation beyond what the template models
- Do not define words for figs-abstractnouns -- just resolve the abstract noun
- For figs-activepassive, the AT must use an active verb, not passive with agent added

### Figure of Speech Verbiage

| Figure | Standard Verbiage |
|--------|-------------------|
| Metaphor | speaking of X as if it were Y |
| Hyperbole | generalization, extreme statement |
| Idiom | was a common expression meaning |
| Merism | referring to all of X by naming two extremes |
| Metonymy | X represents Y |
| Parallelism | These two phrases mean basically the same thing |
| Personification | speaks of X as if it were a person who could... |
| Synecdoche | using one kind to mean the general category |
| Hendiadys | The phrase X and Y expresses a single idea |
| Reduplication | repeating forms of the word X to intensify |
