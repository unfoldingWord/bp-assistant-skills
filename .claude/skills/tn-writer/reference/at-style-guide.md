# Alternate Translation Style Guide

Rules for authoring alternate translations (ATs). The pipeline's AT-generation
stage loads this guide; the note-writing stage does not write ATs and does not
need it. Note-writing rules live in `note-style-guide.md`.

## When to Generate

Generate an alternate translation when the matched templates contain "Alternate translation:" sections. Place AT(s) at the end of the note, as modeled in the template. Enclose each in square brackets. When providing two options, separate with `or`.

## Seamless Replacement

An alternate translation should be a seamless replacement for the text in which the translation issue occurs. If you remove the GLQuote from the ULT verse and replace it with the AT, it should read correctly as natural English.

## Conjunction and Preposition Handling

This rule applies only when the gl_quote is a **contiguous** span of text. Hebrew
prefixes (waw = "and", bet = "in", lamed = "to", mem = "from") are attached
to the Hebrew word but correspond to separate English words. When a gl_quote boundary
does not include an adjacent conjunction or preposition in the ULT, your AT must
account for this:

- If the ULT reads "And in my distress" and gl_quote is "in my distress", your AT
  should start with the preposition: [in my suffering] not just [my suffering]
- If the ULT reads "And he went" and gl_quote is "And he went", your AT must include
  "And": [And he traveled] not just [he traveled]
- If the ULT reads "the one causing his neighbor to drink" for a Hebrew participle,
  the AT must keep "the one": [the one overpowering his neighbor] not just [overpowering his neighbor]

**Do not apply this rule to discontinuous quotes.** If the gl_quote contains `…`, the
AT must use `…` between parts — not "and". See "Discontinuous ATs" below.

## Capitalization in ATs

Match the sentence position of the gl_quote:
- Verse/sentence start: capitalize first word → [He traveled to the city]
- Mid-sentence: lowercase → [he traveled to the city]
- The first word of the AT must match the capitalization of the first word of the gl_quote in the ULT. If the gl_quote starts with a lowercase word like "for", the AT must also start with a lowercase word — don't substitute a different word with different casing (e.g., don't replace "for" with "So").

## Quotation Marks in ATs

Do not use quotation marks in the alternate translation(s) unless that text contains opening or closing quotation marks or both. In that case, reproduce the quotation mark(s) in the corresponding location(s).

## AT Should Differ from UST

Check the UST for the same verse. Make sure your alternate translation is not the same as the UST phrasing. If it is, come up with another alternate translation idea.

**Exception — obscure or textually uncertain passages**: When the passage is so difficult that any plain-meaning AT would inevitably echo the UST, omit the AT bracket and instead direct translators to the UST with the phrase "as the UST does." End the sentence with that phrase rather than providing an AT. Example: "If it would be helpful in your language, you could state the meaning plainly, as the UST does."

## Minimal Adjustment

The AT should be the smallest change to the ULT text that resolves the translation issue. Keep ULT wording where possible, change only what is needed. For figures of speech (metaphors, idioms, etc.), more substantial rewording may be needed to express the plain meaning -- this is expected.

## Resolve the Figure

When a note offers a plain-meaning AT, the AT must not reuse the same figure it is explaining. If the note identifies a metaphor, the AT should not use that metaphor; if it identifies personification, the AT should not give the non-living thing an action verb — use a stative description instead (e.g., "the deep waters were loud" not "the deep waters roared"); and so on.

## Supply Words in ATs

Do not include the curly brace characters `{` or `}` in AT text. The words inside them are implied English words and may appear in the AT as plain text when needed. For example, if the ULT has `{am} poor and needy`, the AT may use "am" but must write it without braces: [am very poor].

## Punctuation in ATs

Do not include punctuation at the start or end of the AT brackets unless the note is specifically proposing a change to the ULT's punctuation. If the gl_quote does not start with a comma or other punctuation, the AT should not either. Similarly, do not add ending punctuation (period, comma, question mark) even if the ULT text being replaced ends with one. The AT replaces the *words*, not the surrounding punctuation.

**Exception**: `figs-rquestion` ATs must include ending punctuation (`.` or `!`) since the `?` -> statement change is the point of the note.

## Discontinuous ATs

When an AT covers non-adjacent text, use a single pair of brackets with a true ellipsis character between the parts: `[I desire peace … they desire war]` (spaces around the ellipsis).

The trigger is whether the **English gl_quote** spans non-adjacent ULT text (contains `…`), regardless of whether the Hebrew OrigQuote uses `&`. Four scenarios:

| gl_quote | AT |
|---|---|
| Contiguous (no `…`) | Normal replacement — no ellipsis needed |
| Contiguous (no `…`), Hebrew has `&` | AT is still a normal replacement — no ellipsis |
| Discontinuous (`…`), Hebrew has `&` | AT **must** use `…` between the parts |
| Discontinuous (`…`), Hebrew is one span | AT **must** use `…` between the parts |

Never use "and" to join non-adjacent AT fragments.

## Restructuring Notes

For issue types that suggest reordering text (figs-infostructure, grammar-connect-logic-goal, grammar-connect-logic-result, grammar-connect-condition-fact, or any note suggesting putting one part of the verse before another), the gl_quote must cover the **entire area** being restructured, and the AT must show the full restructured result. For example, if the note says "put the second half of the verse before the first half," the gl_quote should be approximately the whole verse and the AT should be the whole verse reordered. Do not quote only one fragment of a reordering — the reader needs to see both the original order and the proposed new order.

## Parallelism Quote Scope

For figs-parallelism notes, the gl_quote must include the **entirety of both parallel phrases**, not just the key parallel nouns or words. If the AT covers a parallelism, it must span both complete phrases.

## Issue-Specific AT Requirements

- **figs-ellipsis**: The AT must actually supply the elided words from context — if the omitted subject, verb, or object comes from a prior verse, pull it into the AT so the result is a complete clause. An AT that merely rephrases the existing words without filling in the gap is useless.
- **figs-abstractnouns**: The AT must resolve the abstract noun into a non-abstract form (verb, adjective, clause) -- do not replace one abstract noun with another (e.g., "obedience" -> "faithful obedience" is wrong; "obedience" -> "obeying him" is correct; "covenant faithfulness" -> "faithful love" is wrong because "love" is abstract; "covenant faithfulness" -> "being faithful to his covenant" is correct).
- **figs-activepassive**: The AT must show the idea expressed with an active verb, not a passive verb with an agent added. "God drives them back" is correct; "be driven back by God" is wrong -- that is still passive. Identify the actor from context (usually God) and make them the grammatical subject of an active clause.
- **figs-personification**: Check that the AT does not still include personification. The non-living thing should not be given any verb that implies agency or living action.

## Worked Examples

### Example 1
**Template**: SPEAKER is using the plural **text** where he could have used the singular form. This suggests that he is using the plural form to PURPOSE. If it would be helpful in your language, you could use the singular and express the emphasis in another way.

**Note to "the seas" in Jonah 2:3**: Jonah is using the plural **seas** where he could have used the singular form. This suggests that he is using the plural form to emphasize the greatness or complexity of the sea. If it would be helpful in your language, you could use the singular and express the emphasis in another way. Alternate translation: [the vast sea] or [the raging sea]

### Example 2
**Template**: SPEAKER is referring to all of THING by naming two extremes, **EXTREME** and **EXTREME**. If it would be helpful in your language, you could use an equivalent expression or plain language.

**Note to "from the sunrise and from the sea" in Joshua 11:3**: The author is referring to all of the Canaanite territory by naming its two extreme ends, **the sunrise** (the east) and **the sea** (the west). If it would be helpful in your language, you could use an equivalent expression or plain language. Alternate translation: [from all over their territory]

### Example 3
**Template**: The terms **word1** and **word2** mean similar things. SPEAKER is using the two terms together for emphasis. If it would be clearer for your readers, you could express the emphasis with a single phrase.

**Note to "Strengthen yourselves and be men" in 1 Samuel 4:9**: The expressions **Strengthen yourselves** and **be men** mean similar things. The Philistines are using the two terms together for emphasis. If it would be clearer for your readers, you could express the emphasis with a single phrase. Alternate translation: [Be very courageous]
