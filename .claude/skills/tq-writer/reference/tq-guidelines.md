# Translation Question Guidelines

Reference for updating Translation Questions (TQs) to align with current ULT/UST texts.

## Purpose

TQs are comprehension checks that accompany Bible translations. When ULT/UST texts are updated, existing TQs may fall out of sync -- terms change, verse references shift, and question/answer content no longer matches the source texts. The goal is to update existing TQs so they align with the current ULT/UST while preserving their essential function.

## Core Principle

TQ answers should capture the *idea* of the content so that any translation derived from ULT/UST can contain the answers. Questions are simple comprehension checks for ESL speakers.

## Content Rules

### Match the Content, Not the Form
- Questions and responses must match the *ideas* in the content, using plain, non-figurative language
- **Prefer ULT language by default**: Use ULT phrasing for questions and responses whenever the ULT text is plain and accessible to ESL readers — this keeps TQ language close to the source translators are working from.
- **Fall back to UST for metaphor or complex text**: Switch to UST wording when the ULT rendering is metaphorical, uses Hebrew idioms, or is otherwise not plain/accessible English. Do not independently paraphrase ULT figures when the UST already provides a plain equivalent.
- This applies to both questions and responses — if the ULT says "the apple of his eye" and the UST says "the one he cares for most," both the question and response must use the UST's plain phrasing, not the ULT's figure
- The ULT often preserves Hebrew idioms and structures that would confuse ESL readers — in those cases the UST's rendering is the guide for expressing the same idea in plain, accessible English
- Always use key terms from the ULT (proper nouns, theological terms like "covenant faithfulness"); only substitute UST wording for figurative or complex ULT expressions
- If the ULT or UST uses "Yahweh" in a verse, both the question and the response for that verse must also use "Yahweh" — never substitute "God", "the LORD", or any other form for the divine name
- Example: ULT says "for length of days"; UST says "as long as he lives" — the TQ answer should say "as long as he lives," not repeat the Hebrew idiom
- Example: ULT says "waters of rest"; UST says "quiet streams of water" — the TQ answer should say "quiet water," following the UST's non-figurative rendering
- The test: could an ESL reader understand the answer without needing to look up what the phrase means?

### Language Level
- Write in natural English suitable for ESL speakers (approximately 8th grade reading level)
- Avoid complex sentence structures, technical jargon, or obscure vocabulary
- Keep questions and answers concise and direct

### Perspective
- Use third-person perspective only
- Do not write from the reader's perspective ("you should...") or first-person
- Example: "What does David say about Yahweh?" not "What should you know about Yahweh?"

### Author References in Psalms (PSA)
- When referring to the human author of a psalm, use **"the psalmist"** — never "the writer" or "the author"
- If the psalm's superscription attributes it to a named author (e.g., David, Asaph, the sons of Korah), use that name instead
- This applies consistently across all PSA TQ questions and responses
- Good: "What does the psalmist say Yahweh does for him?"
- Avoid: "What does the writer say about God?" or "What does the author claim?"

### Pronoun-Antecedent Agreement
- Ensure pronouns clearly refer to their antecedents
- When the antecedent is ambiguous, use the noun instead of a pronoun
- Example: "What does David say Yahweh does?" not "What does he say he does?"

### Neutral/Factual Questions
- Ask factual comprehension questions, not interpretive or judgment-based ones
- Do not ask questions that require the reader to make value judgments
- Good: "What does the psalmist say about the wicked?"
- Avoid: "Why is it wrong to follow the wicked?"

### Question Words
- Prefer "what / who / whom / where / when / how" for comprehension checks — these ask the reader to locate content in the verse
- Avoid introducing **new** "why" questions, even factual ones (e.g. "Why does Yahweh drive Ephraim out?"). A "why" question asks the reader to supply a reason or causal link, which is closer to interpretation than to plain comprehension, and tends to read as the wrong type
- An existing "why" question that already functions well and matches the verse should be left as-is — this rule restrains new ones, it does not call for purging inherited ones
- If the source row's question reflects a cause stated plainly in the verse, prefer a "what" framing: instead of "Why will Yahweh punish them?" use "What does Yahweh say he will do because of their sins?"

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
- **Edit wording in place; do not re-author.** Keep each existing question's subject and scope, and reword only the parts that the updated ULT/UST changed. Replacing a question with a different question on the same row is not an update — it discards a vetted comprehension check
- **Preserve the verse Reference; do not renumber.** A row's Reference moves only if the *specific content that question asks about* genuinely relocated to a different verse in the updated text. Do not re-sequence or compress a chapter's references to fit a fresh question order
- **One row in, one row out.** Each existing row produces exactly one updated row. Do not split one question into several, and do not fold several into one

### Fail Safe When You Cannot Match a Row
- If you cannot confidently line up an existing TQ row against a verse in `ult_by_verse` / `ust_by_verse` (for example, the verse numbering in the prepared data does not match the row's Reference), keep the row unchanged — same question, same Response, same Reference, same ID
- Do not respond to a matching gap by regenerating the chapter's questions from the source text. Wholesale regeneration is the failure mode this skill exists to avoid: it inflates the question count, introduces off-type questions, and re-anchors references to the wrong verses

### What to Update
- **Terminology**: If the ULT changed a term (e.g., "blessed" -> "happy"), update TQ to match
- **Verse content**: If verse text changed substantially, update Q&A to reflect new content
- **Verse references**: If content moved between verses, update the Reference column
- **Factual accuracy**: If the Q&A no longer matches what the verse says, correct it

### What Not to Change
- Do not rewrite well-functioning questions just for style preference
- **Hold the question count steady.** This is an update of an existing set, not a fresh authoring pass. Do not add questions to improve coverage or thoroughness. The output for a chapter should have the same number of rows as the input, save for the rare genuine exception below
- Adding a question is a rare exception, not a default: only when a verse the existing set already covers changed so much that its row no longer has any answerable content, and even then prefer reworking the existing row over adding a new one. If you add a row, it must carry the correct verse Reference and a fresh unique ID
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
- **ID**: 4-character alphanumeric identifier (`[a-z][a-z0-9]{3}`); preserve existing IDs on unchanged or lightly edited rows. IDs **must be globally unique within the entire book's TSV** — no two rows may share the same ID, even if they cover different verse references (e.g., `53:2` and `53:2-3` are separate rows and must have distinct IDs). When generating a new ID for a new row, verify it does not already appear in any other row in the current output before finalising it.
- **Tags**: Usually empty for TQs
- **Quote**: Usually empty for TQs
- **Occurrence**: Usually empty for TQs
- **Question**: The comprehension question
- **Response**: The expected answer
