# Translation Question Guidelines

Reference for updating Translation Questions (TQs) to align with current ULT/UST texts.

## Purpose

TQs are comprehension checks that accompany Bible translations. When ULT/UST texts are updated, existing TQs may fall out of sync -- terms change, verse references shift, and question/answer content no longer matches the source texts. The goal is to update existing TQs so they align with the current ULT/UST while preserving their essential function.

## Core Principle

TQ answers should capture the *idea* of the content so that any translation derived from ULT/UST can contain the answers. Questions are simple comprehension checks for ESL speakers.

## Content Rules

### Match the Content, Not the Form
- Questions and responses must match the *ideas* in the ULT, not its literal wording
- The ULT often preserves Hebrew idioms and structures that would confuse ESL readers -- express the same idea in plain, accessible English
- Use key terms from the ULT (proper nouns, theological terms like "covenant faithfulness") but restate Hebrew idioms in natural English
- If the ULT uses "Yahweh," the TQ should use "Yahweh" (not "the LORD")
- Example: ULT says "for length of days" -- the TQ answer should say "for as long as he lives," not repeat the Hebrew idiom
- Example: ULT says "waters of rest" -- the TQ answer should say "quiet waters" or "peaceful waters"
- The test: could an ESL reader understand the answer without needing to look up what the phrase means?

### Language Level
- Write in natural English suitable for ESL speakers (approximately 8th grade reading level)
- Avoid complex sentence structures, technical jargon, or obscure vocabulary
- Keep questions and answers concise and direct

### Perspective
- Use third-person perspective only
- Do not write from the reader's perspective ("you should...") or first-person
- Example: "What does David say about Yahweh?" not "What should you know about Yahweh?"

### Pronoun-Antecedent Agreement
- Ensure pronouns clearly refer to their antecedents
- When the antecedent is ambiguous, use the noun instead of a pronoun
- Example: "What does David say Yahweh does?" not "What does he say he does?"

### Neutral/Factual Questions
- Ask factual comprehension questions, not interpretive or judgment-based ones
- Do not ask questions that require the reader to make value judgments
- Good: "What does the psalmist say about the wicked?"
- Avoid: "Why is it wrong to follow the wicked?"

### Indirect Quotations
- Use indirect quotations rather than direct quotes from the text
- Good: "According to the psalmist, what does Yahweh do for him?"
- Avoid: "What does 'Yahweh is my shepherd' mean?"

### Tense
- Use present tense unless the ULT text is specifically past tense
- For narrative/historical content, match the tense of the ULT

### Verse References
- Verify that verse references in the Reference column match the actual content of the question and answer
- If a question spans multiple verses, use range notation (e.g., 150:3-5)
- **Preserve multi-verse reference spans exactly** — if the source row is `18:9-10` or `24:1-2`, the output must carry that same range. Never collapse a span to only the first verse number; a narrowed reference fails downstream merge/delete matching and produces duplicate rows.
- Ensure the answer can be found in the referenced verse(s)

## Update Rules

### Minimize Unnecessary Edits
- Only change what needs to change to align with the updated ULT/UST
- If the existing TQ already matches the current ULT/UST, leave it unchanged
- Preserve existing IDs -- do not regenerate IDs for unchanged or lightly edited rows

### What to Update
- **Terminology**: If the ULT changed a term (e.g., "blessed" -> "happy"), update TQ to match
- **Verse content**: If verse text changed substantially, update Q&A to reflect new content
- **Verse references**: If content moved between verses, update the Reference column
- **Factual accuracy**: If the Q&A no longer matches what the verse says, correct it

### What Not to Change
- Do not rewrite well-functioning questions just for style preference
- Do not add new questions unless existing coverage is clearly insufficient
- Do not remove questions unless they are clearly redundant or unanswerable from the text
- Do not change IDs on rows that are only lightly edited

## Formatting

Follow `../../reference/gl_guidelines.md` for shared style rules (formality, numbers, spelling, comparisons). TQ-specific rules below.

### Voice
- Use active voice where possible
- Avoid passive constructions unless they match the ULT phrasing

### Quotes
- The post-processing script handles curly quote conversion automatically

### Column Structure
TQ TSV files have 7 columns:
```
Reference	ID	Tags	Quote	Occurrence	Question	Response
```

- **Reference**: chapter:verse (e.g., "150:1" or "150:3-5")
- **ID**: 4-character alphanumeric identifier (preserve existing)
- **Tags**: Usually empty for TQs
- **Quote**: Usually empty for TQs
- **Occurrence**: Usually empty for TQs
- **Question**: The comprehension question
- **Response**: The expected answer
