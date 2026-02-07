# Translation Question Guidelines

Reference for updating Translation Questions (TQs) to align with current ULT/UST texts.

## Purpose

TQs are comprehension checks that accompany Bible translations. When ULT/UST texts are updated, existing TQs may fall out of sync -- terms change, verse references shift, and question/answer content no longer matches the source texts. The goal is to update existing TQs so they align with the current ULT/UST while preserving their essential function.

## Core Principle

TQ answers should capture the *idea* of the content so that any translation derived from ULT/UST can contain the answers. Questions are simple comprehension checks for ESL speakers.

## Content Rules

### Match Literal Translation
- Questions and responses must conceptually match the Literal Translation (ULT)
- Use terms and ideas present in the ULT text
- If the ULT uses "Yahweh," the TQ should use "Yahweh" (not "the LORD")
- If the ULT uses a specific phrase, the TQ answer should reflect that phrasing

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

### Capitalization
- Do not capitalize divine pronouns (use "he/him/his" not "He/Him/His" when referring to God)

### Voice
- Use active voice where possible
- Avoid passive constructions unless they match the ULT phrasing

### Quotes
- Use curly/smart quotes, not straight quotes
- The post-processing script handles this automatically

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
