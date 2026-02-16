# Translation Note Style Guide

This is the authoritative source for translation note style rules. Future edits go here.

## Core Rule

Return a translation note by adapting a template provided as closely as possible. Change only as much as is needed to address the translation issue in the context. Use the template as a model for the reading level and degree of formality.

Only respond with the note, not with any other text or explanation.

## Shared Style Rules

Follow `../../reference/gl_guidelines.md` for shared style rules (formality, numbers, spelling, comparisons). TN-specific rules below.

## Formatting

### Bold
In the note, put in markdown bold formatting any words or phrases that you quote from the given text or from the rest of the verse. Only use quotation marks where there may be quotation marks in the original text that you are quoting. Use markdown bold formatting only for the first occurrence of quoted words or phrases. Quotations from other verses in the Bible should be put in quotation marks. Do not bold anything except an exact quote from the verse.

### Capitalization and Grammatical Forms
When you quote words or phrases from the given text or the rest of the verse, match the capitalization, number, and grammatical forms exactly. For example, if the text says "horses," do not write a note saying, "A **horse** is (definition)." Say, "The term **horses** describes (definition)."

### ALL CAPS in Templates
In the templates you will find words that are in all capital letters. These words need to be replaced by the appropriate information from the verse or the verse's context. These may or may not be direct quotes.

### Slashes in Templates
If there are slashes between words expressing similar or different ideas in a template, discern which word or two applies and instead of using all of that part of the template, use the word(s) you have chosen as applicable in this circumstance and write it as a natural sentence using "and" or "or", not a slash.

## Alternate Translations

### When to Generate
Generate an alternate translation when the matched templates contain "Alternate translation:" sections. Place AT(s) at the end of the note, as modeled in the template. Enclose each in square brackets. When providing two options, separate with `or`.

### Seamless Replacement
An alternate translation should be a seamless replacement for the text in which the translation issue occurs. If you remove the GLQuote from the ULT verse and replace it with the AT, it should read correctly as natural English.

### Conjunction and Preposition Handling
Hebrew prefixes (waw = "and", bet = "in", lamed = "to", mem = "from") are attached
to the Hebrew word but correspond to separate English words. When a gl_quote boundary
does not include an adjacent conjunction or preposition in the ULT, your AT must
account for this:

- If the ULT reads "And in my distress" and gl_quote is "in my distress", your AT
  should start with the preposition: [in my suffering] not just [my suffering]
- If the ULT reads "And he went" and gl_quote is "And he went", your AT must include
  "And": [And he traveled] not just [he traveled]

### Capitalization in ATs
Match the sentence position of the gl_quote:
- Verse/sentence start: capitalize first word → [He traveled to the city]
- Mid-sentence: lowercase → [he traveled to the city]

### Quotation Marks in ATs
Do not use quotation marks in the alternate translation(s) unless that text contains opening or closing quotation marks or both. In that case, reproduce the quotation mark(s) in the corresponding location(s).

### AT Should Differ from UST
Check the UST for the same verse. Make sure your alternate translation is not the same as the UST phrasing. If it is, come up with another alternate translation idea.

### Minimal Adjustment
The AT should be the smallest change to the ULT text that resolves the translation issue. Keep ULT wording where possible, change only what is needed. For figures of speech (metaphors, idioms, etc.), more substantial rewording may be needed to express the plain meaning -- this is expected.

### Punctuation in ATs
Do not include closing punctuation (period, comma, question mark) in the AT brackets unless the note is specifically suggesting a punctuation change.

### Discontinuous ATs
When an AT covers non-adjacent text, use a single pair of brackets with a true ellipsis character between the parts: `[I desire peace … they desire war]` (spaces around the ellipsis).

## Author References
When referring to the author or writer of a biblical text, use "the author" instead of "the writer."

In the book of Psalms, refer to the chapter superscription for an author reference. If David, Asaph, etc. is mentioned as the author, use that name in notes in that psalm. If the psalm is anonymous, use "the psalmist."

Assume traditional authorship of Biblical books.

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
- **Use specialized templates**: When a specific template matches (heart, turn, way/path, fathers, brothers, house, sons, behold), prefer it over both generic and poetry.

## Issue-Specific Restrictions

- **writing-background & writing-newevent**: No elaboration on narrative function or context
- **figs-quotesinquotes**: Do not put the text of either quotation into the note, keep to the template
- **figs-imperative**: Do not add explanatory sentences about the specific imperative content or context
- **grammar-connect-logic-result**: Do not identify specific phrases, keep to the template
- **figs-ellipsis**: Do not explain the missing words/phrase
- **figs-abstractnouns**: Do not define the words

## Terminology

When writing notes, use the same terms that appear in the ULT and UST for the verse. Never substitute common English terms that differ from the project's chosen renderings. For example:

- ULT uses "Box" (capitalized) or "Box of the Testimony/Covenant" for the Ark of the Covenant. Do not write "ark" or "ark of the covenant."
- UST uses "Sacred Chest" (capitalized). Do not write "ark" in UST-referencing contexts.
- See `data/glossary/hebrew_ot_glossary.csv` for the full list of standard renderings.

## Worked Examples

### Example 1 (with AT)
**Template**: SPEAKER is using the plural **text** where he could have used the singular form. This suggests that he is using the plural form to PURPOSE. If it would be helpful in your language, you could use the singular and express the emphasis in another way.

**Note to "the seas" in Jonah 2:3**: Jonah is using the plural **seas** where he could have used the singular form. This suggests that he is using the plural form to emphasize the greatness or complexity of the sea. If it would be helpful in your language, you could use the singular and express the emphasis in another way. Alternate translation: [the vast sea] or [the raging sea]

### Example 2 (with AT)
**Template**: SPEAKER is referring to all of THING by naming two extremes, **EXTREME** and **EXTREME**. If it would be helpful in your language, you could use an equivalent expression or plain language.

**Note to "from the sunrise and from the sea" in Joshua 11:3**: The author is referring to all of the Canaanite territory by naming its two extreme ends, **the sunrise** (the east) and **the sea** (the west). If it would be helpful in your language, you could use an equivalent expression or plain language. Alternate translation: [from all over their territory]

### Example 3 (with AT)
**Template**: The terms **word1** and **word2** mean similar things. SPEAKER is using the two terms together for emphasis. If it would be clearer for your readers, you could express the emphasis with a single phrase.

**Note to "Strengthen yourselves and be men" in 1 Samuel 4:9**: The expressions **Strengthen yourselves** and **be men** mean similar things. The Philistines are using the two terms together for emphasis. If it would be clearer for your readers, you could express the emphasis with a single phrase. Alternate translation: [Be very courageous]
