# Prompt Templates Reference

These are the legacy prompt templates used when `prepare_notes.py` assembles a rendered `prompt` field. The preferred contract is now the per-item `writer_packet`, which already carries the selected template, AT policy, parsed directives, and style rules.

## writes_at_prompt

Used when no alternate translation is provided and the templates contain AT sections.

```
Return only the note.

Create a note to help Bible translators understand and address the issue identified `{sref}`.
Here is the text where the issue occurs: `{gl_quote}`.
Here is the full text of the verse: `{ult_verse}`.
Here is {book} {ref} in its context: `{ult_context}`

Here is where you are in the Bible (standard 3-character abbreviation): `{book} {ref}`.

The following input may or may not occur:

- Here is an explanation of the issue that will help you write the note. Information which must be included will be prefixed with `i:`. Information about which template to use will be prefixed with `t:`. If there are no prefixes, consider whether the text indicates a template type, something to include in the note, or context to help you understand the issue: `{explanation}`

{info}

If there is any data here, it is a previous note written by AI that the human editor did not find sufficient. Attempt to analyze the issue and return a different note: `{ai_tn}`

When you make the alternate translation, it should fit seamlessly back into the ULT such that if you remove the GLQuote `{gl_quote}` and replace it with the alternate translation it reads correctly. Here is the ULT for this verse: `{ult_verse}`

Check the UST for the same verse to make sure that your alternate translation is not the same as the UST. If it is, come up with another alternate translation idea. Here is the UST for that verse: `{ust_verse}`

Use the selected template provided below. Do not choose a different template variant unless the prepared packet explicitly left the template unresolved.

{templates}

Return only the note.
```

## given_at_prompt

Used when an alternate translation is already provided, or when templates have no AT section.

```
Create a note to help Bible translators understand and address the issue identified `{sref}`.
Here is the text where the issue occurs: `{gl_quote}`. Return only the note, without an alternate translation.

Here is where you are in the Bible (standard 3-character abbreviation): `{book} {ref}`.
Here is the verse in context in a literal translation: `{ult_context}`.
Here is the verse in context in a simplified/amplified translation: `{ust_context}`

Here is an alternate translation that will help you identify the issue: `{at}`

The following input may or may not occur:
- Here is an explanation of the issue that will help you write the note. Information which must be included will be prefixed with `i:`. Information about which template to use will be prefixed with `t:`. If there are no prefixes, consider whether the text indicates a template type, something to include, or context: `{explanation}`

{info}

- If there is any data here, it is a previous note written by AI that the human editor did not find sufficient: `{ai_tn}`

Use the selected template provided below. Do not choose a different template variant unless the prepared packet explicitly left the template unresolved.

{templates}

Return only the note.
```

## see_how_at_prompt

Used for "see how" reference notes that need alternate translations generated.

```
I need you to make an alternate translation, it should fit seamlessly back into the ULT (`{ult_verse}`) such that if you remove the GLQuote `{gl_quote}` and replace it with the alternate translation it reads correctly.

Here is where you are in the Bible (standard 3-character abbreviation): `{book} {ref}`.
Here is the verse in context in a literal translation: `{ult_context}`.
Here is the verse in context in a simplified/amplified translation: `{ust_context}`

Check the UST for the same verse to make sure that your alternate translation is not the same as the UST. If it is, come up with another alternate translation idea. Here is the UST for that verse: `{ust_verse}`

For reference here is a hint at the type of translation issue that we are addressing as well as a blank template:
issue type: {sref}

blank template: {template}

Do not include final punctuation in the alternate translation. Do not end the AT text with a period, question mark, exclamation mark, or comma — even if the ULT text being replaced ends with one. The AT replaces the *words*, not the surrounding punctuation. The only exception is a `figs-rquestion` note, where changing `?` to `.` or `!` is the explicit point of the note.

Return only the text of the generated alternate translation.
```

## writing-foreground ("behold")

`data/templates.csv` is fetched from the TN Templates sheet and may not carry a `writing-foreground` row. When the packet arrives with no template for `writing-foreground`, use this one. It follows published phrasing for hinneh / "behold" (MAL 1:13, NAM 1:15) and matches `.claude/skills/issue-identification/writing-foreground.md`:

```
SPEAKER is using the term **MARKER** to focus his readers' attention on what he is about to say. Your language may have a comparable expression that you can use in your translation. Alternate translation: [Listen] or [See]
```

- Replace SPEAKER with the author or the speaker in the verse (see "Author References" in `note-style-guide.md`), and MARKER with the ULT's wording (**Behold**, **behold**, **and behold**). Use "listeners' attention" when the speaker is addressing people within the narrative.
- Each occurrence gets its own note; published notes do not consolidate repeated "behold" markers.
- When the marker could also be an invitation to look at something actually in view, present both readings in TCM form, as the published NAM 1:15 note does.

## TCM Instruction

Prepended to the templates section when TCM (This Could Mean) mode is detected:

```
IMPORTANT: This note should present multiple interpretations.

- Order the options by preference: the reading you judge most likely is option (1). Keep the order the identification row's `i:` field gives; do not reorder by source order or by length.
- Write as many ATs as there are options — one per option, tuned to that option's meaning. Two options means two ATs.
- Each AT closes its own option, immediately before the next option begins. Never pool the ATs at the end of the note.

Format as: "This could mean: (1) [first interpretation]. Alternate translation: [AT for option 1] or (2) [second interpretation]. Alternate translation: [AT for option 2]" — extend the same shape for a third or further option.

Use the template below for context on what aspect needs explanation, but structure the note as a "this could mean" with numbered options.
```
