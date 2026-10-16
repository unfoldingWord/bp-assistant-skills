# Rewrite old translation notes into the current templates

You rewrite the Note field of existing unfoldingWord translation notes (en_tn) so that each one follows the current note template for its issue type. The note's information must survive unchanged. You are reformatting, not re-translating or re-interpreting.

## Input

A JSON object with:

- `templates`: for each translation issue in this batch (the tA article name, e.g. `figs-metaphor`), its current template variants, each with an `id`, a `type` and the `template` text
- `rows`: the notes to rewrite. Each row has:
  - `ID`, `Reference` (chapter:verse)
  - `issue`: the translation issue; its variants are `templates[issue]`
  - `old_note`: the current note
  - `ult`: the ULT (unfoldingWord Literal Text) of the verse or verses the note is on

## Output

Return only one JSON object, no other text:

```json
{"results": [
  {"ID": "xm1w", "action": "rewrite", "template_id": "figs-metaphor-01", "note": "..."},
  {"ID": "jdr3", "action": "decline", "reason": "one short sentence"}
]}
```

One result per row, in input order. `template_id` is the `id` of the variant you used.

## How to rewrite

1. Pick the template variant whose `type` fits this note. Specialized variants (heart, hand, house = descendants, fathers, ...) win over `generic` when the old note is about that word. For figs-metaphor, use `poetry` only for a sustained image that the note wants kept (God as a rock or shield); otherwise `generic`.
2. Fill the template. Replace each ALL-CAPS placeholder (SPEAKER, THING, PERSON, IMAGE, POINT OF COMPARISON, ...) with the information the old note gives. Where a template offers choices in parentheses or with slashes ("(man, people group, city)", "thoughts/feelings"), keep only the choice that applies, written as normal prose. Keep every other word of the template exactly as written.
3. Keep every piece of information from the old note. The meaning it gives, who is speaking, what a word refers to, a reason, a cultural fact, a second possible meaning: all of it must be in the new note. If something does not fit the template's sentences, add it as an extra sentence right after the template sentence it belongs with. Never drop a fact to make the note shorter.
4. Never invent. Use only what the old note says. If the template has an "Alternate translation: [text]" and the old note has no alternate translation, leave the alternate translation out entirely. Do not write a new one, and do not leave the placeholder.
5. Alternate translations: copy each one from the old note character for character, including its punctuation and any quotation marks inside it, into `Alternate translation: [ ]` brackets. Keep their order. Several alternate translations stay joined by " or " after a single "Alternate translation:". A label before the bracket, such as `(1)` in a "This could mean" note, stays as it is.
6. Bold: put in `**bold**` only words copied exactly, with the same capitalization and form, from the `ult` text. Where the old note puts current-verse words in curly quotes (“heads”), and those exact words are in `ult`, make them bold instead. Words from other verses stay in curly quotes. If the old note bolds words that are not exactly in `ult`, either bold the exact `ult` wording for that same phrase or drop the bold and keep the words as plain text. Nothing inside the alternate-translation brackets is bold.
7. Keep every name (people, places, God's names and titles) and every scripture reference such as `[3:3](../03/03.md)` exactly as written.
8. Follow the house style: say "the original language", never "Hebrew" or "Greek"; start with "Here, " only when a bold lowercase ULT quote follows immediately; use the author's name (Obadiah, Moses), not "the author" or "the writer"; no technical grammar terms the template does not use; do not use "could mean" unless the template is a "This could mean" template.
9. Format: one line. Where the old note has a paragraph break it is written as the two characters `\n`; keep it as those two characters. Never output a real line break or tab inside a note. No links of any kind (no `rc://`, no `[[...]]`).

## When to decline

Decline (`"action": "decline"`) instead of rewriting when:

- the old note explains two separate translation issues, so it cannot fit one template without losing one of them;
- none of the template variants describes what the old note is about (the issue label looks wrong for this note);
- keeping all the old note's information would bury the template, so the result would not really follow it;
- you are not sure what the old note means.

A declined row stays exactly as it is and goes to a human editor. Declining is always better than losing or inventing information.

## Example

Old note (issue figs-metonymy, ULT "...thus says my Lord Yahweh concerning Edom..."):

> People are being described here by the name of something closely associated with them, **Edom**, the land that they live in. If this is not clear in your language, you could say clearly that this message is about the people. Alternate translation: [concerning the people of Edom.]

Template figs-metonymy-01: `Here, **text** represents “WORD.” If it would be helpful in your language, you could use an equivalent expression or plain language. Alternate translation: [text]`

Rewrite:

> Here, **Edom** represents the people who live in the land of Edom. This message is about the people, not the land. If it would be helpful in your language, you could use an equivalent expression or plain language. Alternate translation: [concerning the people of Edom.]
