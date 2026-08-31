# Translation Note Style Guide

This is the authoritative source for translation note style rules. Future edits go here.

## Core Rule

Return a translation note by adapting a template provided as closely as possible. Change only as much as is needed to address the translation issue in the context. Use the template as a model for the reading level and degree of formality.

Only respond with the note, not with any other text or explanation.

### One Note Per Verse
Each note addresses a single translation issue in a single verse. Do not create notes that summarize or combine occurrences of the same pattern across multiple verses. Even when the same figure recurs in several verses, each verse gets its own independent note.

## Shared Style Rules

Follow `../../reference/gl_guidelines.md` for shared style rules (formality, numbers, spelling, comparisons). TN-specific rules below.

## Formatting

### Bold
Every word or phrase quoted verbatim from the GLQuote or from anywhere in the ULT verse **must** appear in Markdown bold (`**word**`) in the note's explanatory prose. This requirement stops at the `Alternate translation:` brackets: AT content is plain text and never takes bold, even where it reproduces ULT wording verbatim. Whenever you reproduce exact ULT words in the note, wrap them in bold — for example, if the GLQuote is "his steadfast love" and the note explains it, write "**his steadfast love** refers to..." not "his steadfast love refers to...". Only use quotation marks where there are quotation marks in the original text being quoted. Apply bold to the **first occurrence** of each quoted word or phrase only; do not re-bold the same phrase if it appears again later in the same note. Quotations from other verses in the Bible should be put in quotation marks, not bold. Do not bold anything except an exact verbatim quote from the current verse.

### Capitalization and Grammatical Forms
When you quote words or phrases from the given text or the rest of the verse, match the capitalization, number, and grammatical forms exactly. For example, if the text says "horses," do not write a note saying, "A **horse** is (definition)." Say, "The term **horses** describes (definition)."

### ALL CAPS in Templates
In the templates you will find words that are in all capital letters. These words need to be replaced by the appropriate information from the verse or the verse's context. These may or may not be direct quotes.

### Preserve Template Wording
Replace ALL CAPS placeholders and resolve slashes, but keep all other template wording intact. Do not rephrase, condense, or substitute your own wording for the template's fixed phrases. For example, if the template says "you could express the same idea in another way," write exactly that -- do not change it to "you could express the same idea with a verb" or any other variation. Each note for the same issue type should use the same template phrasing; do not let one note's wording drift and then carry that drift into subsequent notes.

Occasionally context requires different wording, but this should be the exception. By default, the template is the note -- you are filling in the blanks and making minor contextual adjustments. If every note for a given issue type were placed side by side, the fixed portions should be nearly identical across all of them.

### Slashes in Templates
If there are slashes between words expressing similar or different ideas in a template, discern which word or two applies and instead of using all of that part of the template, use the word(s) you have chosen as applicable in this circumstance and write it as a natural sentence using "and" or "or", not a slash.

## Alternate Translations

AT authoring is handled by a separate pipeline stage; its rules live in `at-style-guide.md`. When writing notes, do not generate alternate translations (the pipeline appends them afterward). Two quote-scope rules still matter while writing notes:

### Restructuring Notes
For issue types that suggest reordering text (figs-infostructure, grammar-connect-logic-goal, grammar-connect-logic-result, grammar-connect-condition-fact, or any note suggesting putting one part of the verse before another), the gl_quote must cover the **entire area** being restructured. Do not quote only one fragment of a reordering.

Do not write figs-infostructure notes about placing the object after the verb. Hebrew commonly puts the object before the verb, and many languages do too. Suggesting translators move the object after the verb is not a useful note. If an issue row only concerns object-before-verb order, skip it.

### Parallelism Quote Scope
For figs-parallelism notes, the gl_quote must include the **entirety of both parallel phrases**, not just the key parallel nouns or words. For example, if the verse says "Your mercy is great … your truth reaches to the clouds," do not quote just "mercy … truth" — quote the full "Your mercy is great … your truth reaches to the clouds." The reader needs to see both complete phrases to understand the parallelism.

Always check for figs-ellipsis in parallel phrases. If one phrase omits words that are understood from the other phrase, this is an ellipsis within the parallelism and should be noted separately.

## Author References
Always use the author's name rather than "the author." Assume traditional authorship for biblical books. Known authors include:

- **Lamentations**: Jeremiah
- **Psalms**: check the superscription — use David, Asaph, etc. if named; use "the psalmist" if anonymous
- Other books: use the book's traditional author (e.g., Isaiah, Moses, Solomon)

Only use "the author" as a fallback when the author is genuinely unknown. Never use "the writer."

## Quote Width

Prefer continuous Hebrew quotes when practical. Per Issues Resolved: "It is best to avoid discontinuous text in the Quote field. It is helpful to expand the Quote in order to avoid having ampersands in it." However, an `&` separator is acceptable when expanding the quote would force an awkward `...` ellipsis in the AT. Use judgment — expand when it makes both quote and AT cleaner, keep the `&` when it does.

## "Here" Rule
Only start a note with "Here, " if it is immediately followed by a **bolded quote from the verse** that starts with a lowercase letter. For example: `Here, **admonish** means...` Do not use "Here" before author names, descriptions, or other non-quoted text. Do not do: `Here David is saying...` or `Here the author is speaking...`

## Figure of Speech Verbiage

Use the following standard verbiage when speaking about figures of speech:

| Figure | Standard Verbiage |
|--------|-------------------|
| Metaphor | image, SPEAKER is speaking of TEXT as if it were IMAGE |
| Hyperbole | generalization, extreme statement |
| Idiom | TEXT was a common expression meaning |
| Irony | the opposite of the literal meaning of his words |
| Litany | repetitive series of clauses |
| Merism | SPEAKER is referring to all of THING by naming two extremes |
| Metonymy | Here, **hand** represents the capability of a person (example - adapt to context) |
| Parallelism | These two phrases mean basically the same thing |
| Personification | SPEAKER speaks of **text** as if it were a person who could... |
| Synecdoche | AUTHOR is using one kind of food, bread, to mean food in general (example - adapt to context) |
| Simile | comparison |
| Hendiadys | The phrase WORD and WORD expresses a single idea |

### Metaphor Template Selection

For figs-metaphor, multiple templates may be available (generic, poetry, and specialized types like "heart", "turn", etc.). Do not automatically choose the "poetry" template just because the text is from a poetic book.

- **Default to `generic`**: "Your language may have a comparable expression... or you could state the meaning plainly." This is correct for most metaphors, even in Psalms.
- **Use `poetry` only when**: The metaphor involves a sustained, vivid image where preserving the imagery is the preferred translation strategy (e.g., God as a rock, a fortress, a shield, a shepherd). The poetry template says "If this image communicates well... If not, you could express this as a comparison" -- this is appropriate only when the image itself is the point.
- **Use specialized templates**: When a specific template matches (heart, turn, way/path, fathers, brothers, house, sons), prefer it over both generic and poetry.

### Foregrounding Template ("behold")

"Behold" and other attention markers are writing-foreground, not figs-metaphor. Use the writing-foreground template in `prompt-templates.md`: "SPEAKER is using the term **behold** to focus his readers' attention on what he is about to say. Your language may have a comparable expression that you can use in your translation."

### Possession Template Selection

For figs-possession, there are three templates: `characterization`, `general`, and `our God`. Each serves a distinct purpose:

- **Use `characterization`** when one noun describes or characterizes the other (e.g., "crown of splendor" = splendorous crown, "man of violence" = violent man, "path of righteousness" = righteous path). This is the most common type. The template says "SPEAKER is using the possessive form to describe a **text** that is characterized by **text**."
- **Use `general`** for other non-ownership relationships (source, subject, object, location, composition, time, etc.) that don't fit characterization. The template says "SPEAKER is using this possessive form to mean IDEA."
- **Use `our God`** only for the specific pattern of "my/our God" expressing a worship relationship rather than ownership. This template references Moses and the Israelites -- adapt the speaker reference to the actual context, but only use it when the possessive form is about a social/worship relationship with God.

If the explanation contains a `t:` prefix hinting at the template type, follow that hint.

## "Could mean" Restriction

Do not use the phrase "could mean" in notes. This phrasing is reserved exclusively for TCM (This Could Mean) mode, which presents multiple interpretations for genuinely ambiguous passages. In regular notes, state the meaning with confidence: "SPEAKER is using this possessive form to mean..." not "this could mean..."

## Source Language Reference
Do not use the word "Hebrew" (or "Greek," "Aramaic") in note text. If you need to refer to the source language, say "the original language" or "the original." For example, write "this expression in the original language means..." not "this Hebrew expression means..."

## Technical Language Restriction

Do not introduce linguistic or grammatical terminology that does not appear in the template being used. Terms like "cognate accusative," "genitive of source," "objective genitive," etc. are not part of the translation note vocabulary. Use only the language modeled in the templates. If a template says "possessive form," say "possessive form" -- do not substitute a more technical term.

Similarly, do not borrow wording from templates belonging to other issue types. Each note should follow only the template(s) provided for its own support reference.

## Classification Guidelines

- **"daughter of X" (בַּת + people/place name)**: Use figs-idiom, not figs-personification. "Daughter of Zion," "daughter of my people," "daughter of Edom" are kinship-term idioms that refer to a people group. They are not personifying a nation as a woman. Use the figs-idiom template: "Jeremiah is using **daughter of X** as a common expression to refer to the people of X."
- **Divine causation of literal events**: When the text says Yahweh did something that literally happened (e.g., "he kindled a fire in Zion" when the Babylonians actually burned Jerusalem), use figs-explicit, not figs-metaphor. The fire is real; the implicit information is that Yahweh caused it through human agents. Reserve figs-metaphor for cases where God's action is genuinely figurative (e.g., "he poured out his wrath" -- wrath is not literally a liquid).

## Issue-Specific Restrictions

- **writing-background & writing-newevent**: No elaboration on narrative function or context
- **figs-quotesinquotes**: Do not put the text of either quotation into the note, keep to the template
- **figs-imperative**: Do not add explanatory sentences about the specific imperative content or context
- **grammar-connect-logic-result**: Do not identify specific phrases, keep to the template
- **figs-ellipsis**: Do not explain the missing words/phrase.
- **figs-abstractnouns**: Do not define the words. Keep the note scoped to the single abstract noun occurrence identified by the issue row. Do not broaden one figs-abstractnouns note to cover a matching abstract noun in a parallel line or adjacent clause unless the prepared item explicitly treats them as one fixed expression.
- **writing-poetry (cognate accusative)**: Use the cognate accusative template exactly. Do not describe the poetic effect, explain the figure, or substitute other wording

## Quotation Marks

Use double curly quotes for all quoted meanings, glosses, and cited text within notes. Single apostrophes may only appear in possessives (e.g., "David’s"). We do not use contractions, so there is no other legitimate use of single quotes or apostrophes in note text. Follow the templates exactly: idiom meanings use double quotes (e.g., `to mean “they misuse your name.”`), not single quotes.

## Terminology

When writing notes, use the same terms that appear in the ULT and UST for the verse. Never substitute common English terms that differ from the project's chosen renderings. For example:

- ULT uses "Box" (capitalized) or "Box of the Testimony/Covenant" for the Ark of the Covenant. Do not write "ark" or "ark of the covenant."
- UST uses "Sacred Chest" (capitalized). Do not write "ark" in UST-referencing contexts.
- See `data/glossary/hebrew_ot_glossary.csv` for the full list of standard renderings.

## Worked Examples

The pipeline appends the alternate translation after note writing, so the note text you produce ends where the template's explanatory portion ends.

### Example 1
**Template**: SPEAKER is using the plural **text** where he could have used the singular form. This suggests that he is using the plural form to PURPOSE. If it would be helpful in your language, you could use the singular and express the emphasis in another way.

**Note to "the seas" in Jonah 2:3**: Jonah is using the plural **seas** where he could have used the singular form. This suggests that he is using the plural form to emphasize the greatness or complexity of the sea. If it would be helpful in your language, you could use the singular and express the emphasis in another way.

### Example 2
**Template**: SPEAKER is referring to all of THING by naming two extremes, **EXTREME** and **EXTREME**. If it would be helpful in your language, you could use an equivalent expression or plain language.

**Note to "from the sunrise and from the sea" in Joshua 11:3**: The author is referring to all of the Canaanite territory by naming its two extreme ends, **the sunrise** (the east) and **the sea** (the west). If it would be helpful in your language, you could use an equivalent expression or plain language.

### Example 3
**Template**: The terms **word1** and **word2** mean similar things. SPEAKER is using the two terms together for emphasis. If it would be clearer for your readers, you could express the emphasis with a single phrase.

**Note to "Strengthen yourselves and be men" in 1 Samuel 4:9**: The expressions **Strengthen yourselves** and **be men** mean similar things. The Philistines are using the two terms together for emphasis. If it would be clearer for your readers, you could express the emphasis with a single phrase.
