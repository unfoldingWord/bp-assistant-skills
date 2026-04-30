---
name: chapter-intro
description: Write chapter introductions for biblical text chapters summarizing themes and key content. Use when asked to write a chapter introduction or after pipeline completes.
allowed-tools: Read, Grep, Glob, Write, Edit
---

# Chapter Introduction

Generate a brief chapter introduction that orients translators to the chapter's overall movement, key concepts, and any distinctive translation challenges. Target length: 300-600 characters. Run this after the pipeline has completed for a chapter.

## Arguments

When invoked as `/chapter-intro isa 51`:
- First argument: Book abbreviation (psa, gen, 2sa, etc.)
- Second argument: Chapter number
- Optional hint args from notes pipeline:
  - `--parallelism-signal high`
  - `--parallelism-count <N>`

Book abbreviations follow standard 3-letter codes or common variants:
- psa, ps -> PSA
- 2sam, 2sa -> 2SA
- gen -> GEN

## Pipeline Context

If `--context <path>` is provided, read the context.json file for authoritative source paths (`sources.ult`, `sources.ust`, `sources.issues`, `sources.hebrew`). Use these instead of searching for files.

If `artifacts.parallelism_signal` is present in context.json (or `--parallelism-signal high` is passed), treat it as a chapter-level hint only: mention recurring parallelism briefly in "Translation Issues in This Chapter" if that section is included, without adding verse-level detail.

## Workflow

### Step 1: Gather Inputs

Normalize arguments:
- Book code: uppercase 3-letter code (e.g., `PSA`)
- Chapter: zero-padded 3-digit for filenames (e.g., `061`), plain number for references (e.g., `61`)

Read the following files. Not all may exist; work with what's available.

**Pipeline output (preferred):**
- ULT: `output/AI-ULT/<BOOK>/<BOOK>-<CHAPTER_PAD>.usfm`
- Issues: `output/issues/<BOOK>/<BOOK>-<CHAPTER_PAD>.tsv`
- UST: `output/AI-UST/<BOOK>/<BOOK>-<CHAPTER_PAD>.usfm`

**Fallbacks if pipeline output doesn't exist:**
- Published ULT: `data/published_ult_english/` (find the book file, extract the chapter)
- Published UST: `data/published_ust_english/` (find the book file, extract the chapter)

**Always read:**
- Hebrew source: find the chapter in `data/hebrew_bible/` (search for the book's USFM file containing the chapter)

**Reference materials (consult as needed):**
- Published TN intros for style reference: published TN intro rows for the same book when available
- Translation Words for key terms: use `mcp__workspace-tools__check_tw_headwords` with `terms=["term1", "term2"]` or browse `data/en_tw/`
- Translation Academy articles relevant to the chapter's literary form or recurring translation issues

### Step 2: Read the Style Guide

Read `.claude/skills/reference/gl_guidelines.md` for spelling, punctuation, and register rules that apply to all generated content (American English spelling, Oxford comma, curly quotes, formal register, etc.).

### Step 3: Determine Chapter Function

Identify the chapter's role in the book and its dominant literary movement. Look for:
- speaker changes
- shifts between narration, poetry, prophecy, exhortation, or prayer
- repeated themes or key images
- distinctive translation challenges that affect the whole chapter rather than one verse

This feeds the 1-2 sentence overview in the Structure and Formatting section.

### Step 4: Draft the Introduction

Write a short intro using the template below. The entire intro should be 300-600 characters. Each section is 1-2 sentences. Only include the Translation Issues section when there is a genuinely distinctive challenge (speaker ambiguity, extended metaphor spanning multiple verses, abrupt shifts in audience, repeated legal or ritual terms, etc.).

When a high parallelism hint is present, keep the note brief (one short sentence) and chapter-level (for example, recurring synonymous parallel lines), without listing individual verses.

Use `[[rc://*/tw/dict/bible/kt/<term>]]` or `[[rc://*/tw/dict/bible/other/<term>]]` for Translation Word links. Use `[Book Chapter](../book/chapter/verse.md)` for cross-references.

#### Template

```
# <Book> <Chapter> Introduction

## Structure and Formatting

[1-2 sentences: chapter function, literary movement, and brief characterization. Include a tW or tA link when it materially helps translators.]

## Religious and Cultural Concepts in This Chapter

### [Concept Name]

[1-2 sentences explaining the concept.]

### [Optional second concept]

[1-2 sentences.]

## Translation Issues in This Chapter (optional)

### [Issue Name]

[1-2 sentences. Only include for distinctive challenges.]
```

#### Quality Checks

- Introduction matches the chapter's actual content and literary function
- tW links use correct `[[rc://...]]` format
- Content is translator-oriented, not devotional
- No verse-level detail that belongs in translation notes
- Total length stays in the 300-600 character range

### Step 5: Format and Insert into Issue File

**Format the intro for TSV storage:**
1. Escape actual newline characters as literal `\n` (two characters: backslash + n). **This is the ONLY escaping needed.** Do NOT escape Unicode characters — en-dashes (–), em-dashes (—), curly quotes (“ ” ‘ ’), apostrophes (’), or any other non-ASCII character — as `\u` sequences. Write all such characters as their actual Unicode characters.
2. The intro content goes in column 7 (the explanation/content column)

**Build the issue TSV row (7 tab-separated columns, matching issue TSV format):**
```
<book>\t<chapter>:intro\t\t\t\t\t<escaped intro content>
```

Example:
```
hab	3:intro					# Habakkuk 3 Introduction\n\n## Structure and Formatting\n\n...
```

Columns:
1. Book code (lowercase, e.g., `psa`)
2. Reference: `<chapter>:intro`
3. Issue type: (empty)
4. ULT quote: (empty)
5. Go? flag: (empty)
6. AT: (empty)
7. Content: the full intro with `\n` escapes

**Insert into the issue file:**
1. Read the existing issue file at `output/issues/<BOOK>/<BOOK>-<CHAPTER_PAD>.tsv`
2. Prepend the intro row as the first line
3. Write back to the same file

If the issue file already has an intro row (first line contains `:intro`), replace it rather than adding a duplicate.

**Confirm the result** by reading back the first 3 lines of the file to verify:
1. The intro row is correctly placed as the first data line
2. The intro is a **single TSV line** — no actual newline characters in the content. All markdown line breaks must be literal two-character `\n` sequences. If you see the intro spanning multiple lines in the file, fix it immediately.
3. There are no `\u` escape sequences in the content (e.g., `\u2013`, `\u201c`). If you see any, the file must be rewritten with the actual Unicode characters substituted in place of the escape sequences.
