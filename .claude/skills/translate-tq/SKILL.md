---
name: translate-tq
description: Translate a batch of translationQuestions rows into a gateway language. Invoked by the translate pipeline with a task JSON path. Translates ONLY the Question and Response columns; every other column is copied byte-identical. Use when asked to run /translate-tq with a task file.
---

# translate-tq — gateway-language translation of tQ rows

You are translating unfoldingWord **translationQuestions** into a gateway
language so that gateway-language translation teams can use them to check
their Bible translations. You translate **only the Question and Response
columns**. Everything else is protected structure.

## Input

The invocation argument is the path to a **task JSON** file:

```json
{
  "task": "translate-tsv-batch",
  "resourceType": "tq",
  "passThroughColumns": ["Reference", "ID", "Tags", "Quote", "Occurrence"],
  "translateColumns": ["Question", "Response"],
  "book": "OBA",
  "targetLang": "ar",
  "targetLangName": "Arabic",
  "sourceLangName": "English",
  "direction": "rtl",
  "rowCount": 12,
  "batchFile": "…/batch-03.tsv",
  "packFile": "…/batch-03-pack.md",
  "outputFile": "…/batch-03-out.tsv"
}
```

Steps:

1. **Read the task JSON** at the given path. Note `translateColumns` and
   `passThroughColumns` — they tell you exactly which columns to touch.
2. **Read `packFile`** — the translation context: brief, standing
   instructions, quality standards, terminology constraints, and validated
   example translations. Follow it. Approved terminology renderings are HARD
   constraints.
3. **Read `batchFile`** — a 7-column tQ TSV
   (`Reference	ID	Tags	Quote	Occurrence	Question	Response`).
4. **Write `outputFile`** — the same TSV, same header, same rows in the same
   order, with only the **Question** and **Response** columns translated into
   {targetLangName}.

## The iron rules (deterministic checks WILL reject violations)

1. **One output row per input row. Same order. No additions, no omissions.**
2. **`Reference`, `ID`, `Tags`, `Quote`, `Occurrence` are copied
   byte-for-byte.** The Quote column is source-language scripture text — it
   must NEVER be translated, transliterated, reordered, or "corrected", even
   when the target language is right-to-left. (tQ Quote is often empty; keep
   it exactly as-is either way.)
3. **Every `rc://` link in a source cell appears verbatim in the translated
   cell.** Link paths are never localized. Text around them is.
4. **Newlines inside a cell are the literal two characters `\n`** (backslash
   + n) — copy that convention; never emit a real line break inside a row.
   Never emit a real tab inside any field.
5. Preserve any markdown structure (`**bold**`, `[bracketed]` alternatives)
   and its count.
6. Numbers (verse/chapter references) in the source appear in the translation
   using Western digits as in the source.

## Translation guidance

- Translate the **meaning naturally** into {targetLangName} at the register
  the brief specifies. The Question asks about the passage; the Response is
  the expected answer — keep the question/answer relationship intact and
  natural in the target language.
- Use the pack's approved terminology; absent an entry, use the conventional
  target-language Bible spelling for names and terms.
- Imitate the **validated examples** — they are human-approved style ground
  truth.

## Repair mode

If the prompt lists validation violations from a previous attempt, read your
existing `outputFile`, fix exactly the violated rows/columns, and rewrite the
complete file. Do not change rows or columns that passed.

## Output discipline

Write the output TSV with the Write tool in one shot (assemble the full
content first). Do not narrate row-by-row. When done, reply with one line:
`done: <rowCount> rows -> <outputFile>`.
