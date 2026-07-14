---
name: translate-article
description: Translate one markdown article file (translationWords term or translationAcademy article file) into a gateway language. Invoked by the translate pipeline with a task JSON path. Translates the prose while preserving markdown structure and every link byte-for-byte. Use when asked to run /translate-article with a task file.
---

# translate-article — gateway-language translation of tW / tA markdown

You are translating one unfoldingWord **markdown article file** into a gateway
language:

- **translationWords (tW)** — a dictionary entry for one biblical term
  (definition, translation suggestions, references).
- **translationAcademy (tA)** — one file of a translation-training article
  (`title.md` is a short title, `sub-title.md` is a question, `01.md` is the
  body).

You translate the **prose meaning** into {targetLangName} while preserving the
markdown structure and every link exactly.

## Input

The invocation argument is the path to a **task JSON** file:

```json
{
  "task": "translate-article",
  "articleId": "kt/god",
  "filePath": "bible/kt/god.md",
  "targetLang": "ar",
  "targetLangName": "Arabic",
  "sourceLangName": "English",
  "direction": "rtl",
  "sourceFile": "…/article-01.md",
  "packFile": "…/article-01-pack.md",
  "outputFile": "…/article-01-out.md"
}
```

Steps:

1. **Read the task JSON** at the given path.
2. **Read `packFile`** — brief, standing instructions, terminology
   constraints (`preferred` = HARD; honor `forbidden`/`do_not_translate`/
   `admitted`), and validated examples. Preferred terminology renderings
   are HARD constraints.
3. **Read `sourceFile`** — the {sourceLangName} markdown body.
4. **Write `outputFile`** — the same document translated into
   {targetLangName}, structure and links preserved (see iron rules).

## The iron rules (deterministic checks WILL reject violations)

1. **Preserve every link target byte-for-byte:**
   - `rc://…` links (e.g. `rc://en/ta/man/translate/translate-names`) — the
     whole URI is copied unchanged. Do NOT localize the language code inside
     it (leave `rc://en/...` as-is unless the pack says otherwise).
   - Markdown link targets — the `(…)` part of `[text](target)`, including
     relative links like `(../kt/god.md)` and `(../other/creation.md)`. The
     link **text** may be translated; the target must not change.
   - `[[double-bracket]]` links — contents copied unchanged.
   The count and exact spelling of every link must match the source.
2. **Preserve the heading structure.** Keep the same number of `#`, `##`,
   `###` … headings, in the same order and at the same levels. Translate the
   heading text.
3. **Preserve inline structure:** `**bold**` markers, blockquotes (`>`),
   list markers (`*`, `-`, `1.`), and the paragraph/line-break layout.
4. **Do NOT translate the "Word Data" / Strong's line** (e.g.
   `* Strong's: H0430, G23160`) — copy it verbatim.
5. **Never leave the body empty** when the source is non-empty. If a file is
   only a heading or a single short phrase (tA `title.md` / `sub-title.md`),
   translate that phrase and keep it as one line.

## Translation guidance

- Translate the **meaning naturally** into {targetLangName} at the register
  the brief specifies — these articles are read by translators and church
  leaders, not scholars.
- Use the pack's preferred terminology for biblical terms and names; absent an
  entry, use the conventional target-language Bible spelling.
- Imitate the **validated examples** — they are human-approved style ground
  truth. Where the pack gives a phrasing template for this article, follow it.
- Bible reference lists (e.g. `[Genesis 1:2](rc://…)`): translate the visible
  book/reference text into the target-language convention, but keep the
  `rc://` target unchanged.

## Repair mode

If the prompt lists validation violations from a previous attempt, read your
existing `outputFile`, fix exactly the violated aspects (usually a
dropped/changed link or a missing heading), and rewrite the complete file.

## Output discipline

Write the output markdown with the Write tool in one shot (assemble the full
content first). Do not narrate section-by-section. When done, reply with one
line: `done: <filePath> -> <outputFile>`.
