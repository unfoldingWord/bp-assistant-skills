---
name: translate-tn
description: Translate a batch of translationNotes rows into a gateway language. Invoked by the translate pipeline with a task JSON path. Translates ONLY the Note column; every other column is copied byte-identical. Use when asked to run /translate-tn with a task file.
---

# translate-tn — gateway-language translation of tN rows

You are translating unfoldingWord **translationNotes** into a gateway
language so that gateway-language translation teams can use them to check
their Bible translations. You translate **only the Note column**. Everything
else is protected structure.

## Input

The invocation argument is the path to a **task JSON** file:

```json
{
  "task": "translate-tn-batch",
  "book": "OBA",
  "targetLang": "ar",
  "targetLangName": "Arabic",
  "direction": "rtl",
  "rowCount": 12,
  "batchFile": "…/batch-03.tsv",
  "packFile": "…/batch-03-pack.md",
  "outputFile": "…/batch-03-out.tsv"
}
```

Steps:

1. **Read the task JSON** at the given path.
2. **Read `packFile`** — the translation context: brief, standing
   instructions, optional quality standards, terminology constraints
   (`preferred` = HARD; honor `forbidden`/`do_not_translate`/`admitted`),
   note templates for this batch's note types, and validated example
   translations. Follow it. Preferred terminology renderings are HARD
   constraints.
3. **Read `batchFile`** — a 7-column tN TSV
   (`Reference	ID	Tags	SupportReference	Quote	Occurrence	Note`).
4. **Write `outputFile`** — the same TSV, same header, same rows in the
   same order, with only the Note column translated into
   {targetLangName}.

## The iron rules (deterministic checks WILL reject violations)

1. **One output row per input row. Same order. No additions, no omissions.**
2. **`Reference`, `ID`, `Tags`, `SupportReference`, `Quote`, `Occurrence`
   are copied byte-for-byte.** The Quote column is Hebrew/Greek/Aramaic
   source text — it must NEVER be translated, transliterated, reordered, or
   "corrected", even when the target language is right-to-left.
3. **Every `rc://` link in the source Note appears verbatim in the
   translated Note** (e.g. `[[rc://*/ta/man/translate/figs-metaphor]]`).
   Link paths are never localized. Text around them is.
4. **Newlines inside a Note are the literal two characters `\n`** (backslash
   + n) — copy that convention; never emit a real line break inside a row.
   Never emit a real tab inside any field.
5. Markdown structure carries meaning — preserve it:
   - `**bold**` marks quoted ULT words: keep the bold markers around the
     corresponding translated words.
   - `[bracketed]` segments after "Alternate translation:" are alternate
     renderings: translate their contents, keep the bracket structure and
     count.
   - Verse links like `[1:5](../01/05.md)` keep their targets untouched;
     translate only display text where it is prose.
6. Numbers (verse/chapter references) in the source Note appear in the
   translation using Western digits as in the source.

## Translation guidance

- Translate the **meaning naturally** into {targetLangName} at the register
  the brief specifies — these notes are read by translators, not scholars.
  Do not translate word-for-word if it produces stilted text.
- Where the pack provides a **template** for a note's SupportReference type,
  follow the template's phrasing pattern. Where it explicitly says no
  template exists, mirror the English note's structure.
- Imitate the **validated examples** — they are human-approved style ground
  truth.
- English technical terms of the unfoldingWord ecosystem that have a
  preferred terminology entry use it; otherwise translate descriptively.
- Bible names and terms: use the pack's terminology; absent that, use the
  conventional target-language Bible spelling (e.g. for Arabic, Van Dyke
  conventions).

## Repair mode

If the prompt lists validation violations from a previous attempt, read your
existing `outputFile`, fix exactly the violated rows/aspects, and rewrite
the complete file. Do not change rows that passed.

## Output discipline

Write the output TSV with the Write tool in one shot (assemble the full
content first). Do not narrate row-by-row. When done, reply with one line:
`done: <rowCount> rows → <outputFile>`.
