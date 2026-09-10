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
   constraints. The pack may also include a "Scripture for these verses"
   section giving the source (ULT/UST) and, when available, the
   target-language literal/simplified verse text for each verse in the
   batch — use it per the bold/alternate-translation guidance below.
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
   - `**bold**` marks words quoted from the literal Bible. In the
     translation, keep the bold markers, and make the bold words **match
     the wording of the Target literal (GLT/AVD/etc.) verse text** shown in
     the pack's "Scripture for these verses" section for that verse, when
     it is provided. Only when no target literal text is available,
     translate the source bold words naturally.
   - `[bracketed]` segments after "Alternate translation:" are alternate
     renderings: translate their contents, keep the bracket structure and
     count, and phrase them so they read naturally in the target language
     and are **consistent with the Target simplified (GST/NAV/etc.) verse
     text** in the scripture section when provided.
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
- When the pack's "Scripture for these verses" section provides target
  literal/simplified verse text, prefer that actual wording for bold quotes
  and alternate translations over a fresh word-for-word translation of the
  English — the whole point is that translators recognize their own
  Bible's wording. This never applies to the `Quote` column (iron rule 2
  stands: it is Hebrew/Greek/Aramaic and is never touched).

## Adapt the note to the target Bible text — do not just translate it

The readers of your output are translators who see the **target-language
literal Bible** (the pack's "Scripture for these verses" section), not the
English ULT. A note that describes an English feature the reader cannot see
in their own Bible text is noise, however well translated. Before translating
each note, decide which case applies:

1. **Same phenomenon, visible in the target text.** Translate the note; the
   bold words must be the target text's own words for that phrase.
2. **Same phenomenon, carried by a different word or form.** Rebuild the note
   around the target text: point the bold quote at the target word that
   carries it (a verb whose subject pronoun is implied, a word with an
   attached connector, a construct phrase), and explain it as the reader
   sees it. Do not write about a separate word "he" or "and" that does not
   exist as a separate word in the target sentence.
3. **Phenomenon absent from the target text** (the target Bible already made
   it active, explicit, or unambiguous). Do not describe an English feature
   the reader cannot see. Rewrite the note so it still helps: state briefly
   what the source text does and how the target text rendered it, so the
   reader knows the choice was made and can make their own. If nothing
   useful remains, translate a one-sentence version of the note. Never drop
   the row (iron rule 1) and always keep the `rc://` link (iron rule 3).

Alternate translations follow iron rule 5 in every case, including rebuilt
notes: the rebuilt note has exactly as many `[bracketed]` alternate
translations as the source, each rewritten in terms of the target wording
rather than as a re-translation of the English brackets. Never add a bracket
the source did not have and never drop one. When the source lists numbered
options `(1) … (2) …`, keep the numbering and each option's alternate
translation — those options are about the meaning of the source text, not
about English grammar, and the reader still needs them.

Case 1 is the default. A note whose bold phrase has a direct counterpart in
the target text (the same idiom, the same metaphor, the same name) is case 1
even if you would phrase the explanation differently; adaptation is for
grammar the target text does not show, not for restyling.

When you apply case 2 or 3, begin the note with the marker `(adapted) `
rendered in the target language (Arabic: `(مُكيَّف) `) so the human reviewer
can find rebuilt notes quickly; the reviewer removes it on approval. Case 1
notes carry no marker. If the pack's standing instructions give
language-specific rules for particular note types (pronouns, connectors,
voice, number marking), those rules decide the case.

If no target-language scripture is provided for the verse, treat every note
as case 1.

## Repair mode

If the prompt lists validation violations from a previous attempt, read your
existing `outputFile`, fix exactly the violated rows/aspects, and rewrite
the complete file. Do not change rows that passed.

## Output discipline

Write the output TSV with the Write tool in one shot (assemble the full
content first). Do not narrate row-by-row. When done, reply with one line:
`done: <rowCount> rows → <outputFile>`.
