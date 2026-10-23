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
  {"ID": "ab12", "action": "rewrite", "template_id": "figs-metaphor-01", "note": "..."},
  {"ID": "cd34", "action": "decline", "reason": "one short sentence"},
  {"ID": "ef56", "action": "rewrite", "template_id": "translate-unknown-01", "note": "...", "review": "one short sentence"}
]}
```

One result per row, in input order. `template_id` is the `id` of the variant you used. Add `review` to either kind of result when a person should look at the row (see "Asking for a person" below); leave it out otherwise.

## How to rewrite

1. Pick the template variant whose `type` fits this note. A variant with an empty `type` is the issue's default. Specialized variants (heart, hand, house = descendants, fathers, ...) win over the default or `generic` when the old note is about that word and gives it the meaning the variant states. For figs-metaphor, use `poetry` only for a sustained image that the note wants kept; otherwise `generic`.
2. Fill the template from the old note and the `ult` text only. Placeholders are the ALL-CAPS words (SPEAKER, THING, PERSON, IMAGE, POINT OF COMPARISON, ACTION_DESCRIPTION_NOT_QUOTE, ...), `X` and `Y`, `[text]` and any other bracket that stands for the verse's words (fill it with those `ult` words in **bold**, without the brackets), and also the example content some templates carry: names and words such as David, Yahweh, the Israelites, Ehud, the Messiah, Person, **rock** or **brothers** that only show how a filled note looks. Replace each placeholder with what the old note or the `ult` says. Where a template offers choices in parentheses or with slashes ("(man, people group, city)", "thoughts/feelings"), keep the choice or choices that apply, joined with "and" or "or" as normal prose. Keep every other word of the template exactly as written, including the words around a placeholder: "SPEAKER is using the question form for PURPOSE" becomes "the speaker is using the question form for emphasis" or "Ruth is using ...", not "... to emphasize". Pronouns and verbs in the fixed wording agree with what fills the placeholder: "is speaking of himself" becomes "is speaking of herself" for Ruth, and "is using" becomes "are using" for the women. That is not a reason to decline. In the same way, "the word **...**" becomes "the phrase **...**" when the bold text is more than one word ("the phrase translated as **Now it happened**").
   - Measurement templates (translate-bvolume, translate-bweight, translate-bdistance, translate-bmoney, ...) open with a worked example ("This **ephah** was equivalent to 22 liters or nearly two thirds of a bushel"). Its figures are example content: keep the old note's own figures and alternate translations, and add the template's advice sentence ("If it would be helpful to your readers, you could express this in terms of modern measurements, either in the text or in a footnote").
3. Who is speaking. Name a speaker, author or addressee only when the old note or the `ult` text names them. Otherwise use the old note's own wording ("the speaker", "the author", "the people") in the placeholder. Do not work out the speaker from your own knowledge of the book.
4. Keep every piece of information the old note gives about the Bible text: the meaning it gives, who is speaking, what a word refers to, a reason, a cultural fact, a second possible meaning, and how certain the note is ("may", "probably", "could"). All of it must be in the new note, with the same certainty. Information means this content, not the old note's phrasing: a sentence whose point the template's own wording already makes (the old note's version of "this is a metaphor", "use a natural form in your language", "you could call attention to it in another way", "the original readers knew this") is dropped, not added next to the template's sentence. Never drop a fact to make the note shorter, and never keep a sentence only because the old note had it.
   - Work the old note's facts into the template's sentences where they fit (as the filled placeholder, or as a clause), rather than adding a sentence that repeats what a template sentence just said. After `represents “...”` or `to mean “...”` has given the meaning, do not restate that meaning in another sentence.
   - A fact that needs its own sentence goes after the template's sentence that names the issue and before the template's advice sentence (the one that starts "If it would be...", "If this phrase...", "If your language...", "You may have..." or "Your language may..."). Explanation first, then how to translate it.
   - When the old note gives two possible meanings, keep them as two: to mean “to be approved of” or “to be found to be pleasing”, not one quotation holding both.
   - If keeping an old sentence would make the new note wrong or confusing in its new place (it now seems to say the opposite, or to explain the wrong word), leave it out and ask for a person (`review`).
   - figs-hendiadys: the template says which word tells more about the other. When the old note does not say, work it out from the old note's alternate translation (in [Please let me glean by gathering], **gather** tells how she will **glean**), write it in, and add `review` saying you inferred it. Decline only if the alternate translation does not show it either.
5. Never invent. Add nothing the old note and the `ult` do not say: no new meaning, reason, contrast, speaker or alternate translation. If the template has an "Alternate translation:" and the old note has none, leave the alternate translation out entirely (the row is tagged for an editor to add one; do not decline for this). The other way round, if the old note has an alternate translation and the template has none, keep it: put it at the end of the note as "Alternate translation: [...]". An old alternate translation is never dropped. Alternate-translation text written into a template (`[power]`, `[ancestors]`, `[other_metaphor] or [non-metaphor]`) is a placeholder too: use only the old note's alternate translations, as many as it has.
6. Alternate translations: copy each one from the old note character for character, including its punctuation and any quotation marks inside it, into `Alternate translation: [ ]` brackets. Keep their order. Several alternate translations stay joined by " or " after a single "Alternate translation:". A label before the bracket, such as `(1)` in a "This could mean" note, stays as it is.
7. Bold: put in `**bold**` only words copied exactly, with the same capitalization and form, from the `ult` text. Where the old note puts current-verse words in curly quotes (“heads”), and those exact words are in `ult`, make them bold instead. Words from other verses stay in curly quotes. If the old note bolds words that are not exactly in `ult`, either bold the exact `ult` wording for that same phrase or drop the bold and keep the words as plain text. Nothing inside the alternate-translation brackets is bold.
8. Keep every name (people, places, God's names and titles) and every scripture link such as `[3:3](../03/03.md)` or `[verse 16](../01/16.md)` exactly as written, and every pointer such as "See how you translated this in the previous verse".
9. House style: say "the original language" instead of "Hebrew" or "Greek", unless the old note is contrasting Hebrew with Aramaic or uses the word for a people ("a Hebrew slave"); no technical grammar terms beyond what the template or the old note uses; do not add "could mean" wording unless the old note already gives more than one meaning.
10. Format: one line, no real line breaks or tabs. Where the old note has a paragraph break it shows as the two characters `\n`. Your reply is JSON, so inside the JSON string write that break as `\\n` (backslash, backslash, n); it then reads back as the two characters `\n`. No `rc://` links and no `[[...]]` links; scripture links of the form `[3:3](../03/03.md)` stay.

## When to decline

Decline (`"action": "decline"`) instead of rewriting when:

- the old note explains two separate translation issues, so it cannot fit one template without losing one of them;
- none of the template variants describes what the old note is about (the issue label looks wrong for this note). Add `review` naming the issue that fits better. One the team has ruled on: “answered … and said” and similar pairs are now writing-quotations, not figs-hendiadys or figs-doublet (Issues Resolved, Jun 25, 2025);
- keeping all the old note's information would bury the template, so the result would not really follow it;
- you are not sure what the old note means;
- a placeholder needs information (a speaker, a meaning, a purpose) that neither the old note nor the `ult` gives;
- the template's fixed wording states a meaning, referent or kind of expression that differs from what the old note says (a "house = household" template for a note where house means descendants);
- the old note gives several possible meanings and no variant has room for them;
- no choice in a template's choice list fits (the translate-names list has no "woman" or "region").

A declined row stays exactly as it is and goes to a human editor. Declining is always better than losing or inventing information.

## Asking for a person

Add `"review": "one short sentence"` when an editor should look at the row, and say what they should check. The row is tagged `human review` in the Tags column. Use it when:

- you rewrote the note but are unsure a reader would understand it, or a judgement call remains (a template that assumes readers do not know a thing, such as a **house**, for a word they may well know);
- the old note describes a form the `ult` does not have (it explains a repeated verb, but the `ult` shows the verb once): decline, with `review` saying what does not match;
- you left out an old sentence because keeping it would make the note wrong or confusing (rule 4).

Do not add `review` for ordinary rewrites you are confident in, or only because the template wanted an alternate translation the old note lacks.

## Example

Old note (issue figs-metonymy, ULT "...thus says my Lord Yahweh concerning Edom..."):

> People are being described here by the name of something closely associated with them, **Edom**, the land that they live in. If this is not clear in your language, you could say clearly that this message is about the people. Alternate translation: [concerning the people of Edom.]

Template figs-metonymy-01: `Here, **text** represents “WORD.” If it would be helpful in your language, you could use an equivalent expression or plain language. Alternate translation: [text]`

Rewrite:

> Here, **Edom** represents “the people who live in the land of Edom.” If it would be helpful in your language, you could use an equivalent expression or plain language. Alternate translation: [concerning the people of Edom.]

The old note's "you could say clearly that this message is about the people" is dropped: the template's advice sentence already says that.

Old note (issue figs-idiom, ULT "...Have you a husband? ..."), with an extra fact:

> This appears to be an idiom that probably asks about her current status. In other words, it is likely that Naomi is asking if Ruth is now betrothed to be married.

Rewrite (template figs-idiom-01): the fact goes before the "If this phrase" advice, and the first old sentence is dropped because the template sentence says the same:

> Naomi is using **...** as a common expression of the culture to mean “...” In other words, it is likely that Naomi is asking if Ruth is now betrothed to be married. If this phrase does not have that meaning for your readers, ...
