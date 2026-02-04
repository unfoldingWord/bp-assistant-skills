# Ambiguity Patterns Reference

This document provides examples of genuine ambiguity in biblical text - passages where meaning is unclear or scholars disagree. These patterns help identify when a "this could mean" style note is appropriate.

## 1. Pronoun Reference Ambiguity

When multiple possible antecedents exist for a pronoun.

**Tag:** `writing-pronouns`

### Examples from Published Notes

**Job 9:3** - "he" with multiple possible referents
```
If he wished to contend with him, he could not answer him once in a thousand times.
```
Note: "The pronoun **he** could refer to (1) God or (2) a person who wanted to contend with God."

**Job 9:20** - "it" with multiple possibilities
```
Though I am righteous, my own mouth would condemn me; though I am blameless, it would declare me guilty.
```
Note: "The pronoun **it** could refer to (1) Job's own mouth or (2) God declaring Job guilty."

### Detection Signals
- "he/him/his" appears in context with multiple male figures
- "they/them/their" could refer to different groups
- "this/that" points back to multiple possible referents
- Possessive pronouns ("his hand") where ownership is unclear

## 2. Lexical Polysemy

Words with established multiple meanings in the source language.

**Tag:** `figs-explicit` (or existing figure type if applicable)

### Common Polysemous Terms

| Term | Possible Meanings |
|------|------------------|
| world (kosmos) | earth/created order, people, sinful value system |
| love (agape) | God's love, human love, love as action |
| know | cognitive knowledge, relational intimacy, experiential |
| spirit | Holy Spirit, human spirit, wind/breath, attitude |
| flesh | physical body, sinful nature, humanity |
| from God | sent by, belonging to, originating from |

### Examples from Published Notes

**1 John 4:3** - "from God"
```
every spirit that does not confess Jesus is not from God
```
Note: "**from God** could mean (1) sent by God or (2) having God as its source."

**1 John 4:6** - "spirit of truth / spirit of error"
```
By this we know the spirit of truth and the spirit of error.
```
Note: "**the spirit of truth** could refer to (1) the Holy Spirit or (2) an attitude of truthfulness."

**1 John 4:18** - "fear"
```
There is no fear in love, but perfect love casts out fear.
```
Note: "**fear** here could mean (1) terror of punishment or (2) reverent fear of God."

### Detection Signals
- English versions differ significantly on translation of the term
- Commentaries discuss multiple meanings
- The same Greek/Hebrew word is translated differently in nearby verses

## 3. Idiomatic Uncertainty

Fixed expressions where meaning is disputed among scholars.

**Tag:** `figs-idiom`

### Examples from Published Notes

**Job 9:35** - "I am not so with myself"
```
for I am not so with myself
```
Note: "The phrase **I am not so with myself** could mean (1) 'I do not consider myself guilty' or (2) 'I am not in my right mind from fear.'"

### Detection Signals
- A phrase that doesn't translate literally into clear meaning
- Commentaries offer different interpretations of the idiom
- The expression appears rarely in Scripture

## 4. Ellipsis with Multiple Resolutions

Missing elements that could be filled multiple ways.

**Tag:** `figs-ellipsis` or `figs-explicit`

### Examples

**Poetry with incomplete parallel:**
```
His heart is established; he will not be afraid...
```
When the second clause omits "his heart," it could be filled as:
- "his heart will not be afraid" (emotional response)
- "he himself will not be afraid" (the person's response)

### Detection Signals
- Parallel structure where second element is abbreviated
- Missing subject/object that could logically be multiple things
- Context provides more than one reasonable completion

## 5. Note Format for Ambiguity

When genuine ambiguity is identified, notes should:

1. **State both/all options clearly:**
   - "This could mean (1) [interpretation A] or (2) [interpretation B]."

2. **Keep options concise** - usually one phrase each

3. **Order options** - put the more likely interpretation first when there is scholarly consensus

4. **Avoid false precision** - don't claim certainty where none exists

### Example Note Formats

**Two-option format:**
```
The phrase **[quoted text]** could mean (1) [first interpretation] or (2) [second interpretation].
```

**With explanation:**
```
The word **[term]** here could refer to (1) [meaning A], emphasizing [aspect], or (2) [meaning B], focusing on [different aspect].
```

## 6. TCM (This Could Mean) Trigger Format

When identifying ambiguity in issue-identification output, use the `TCM` trigger to signal that the note writer should format the note as "This could mean (1)... or (2)...".

### Format

```
TCM i:(1) [interpretation A] (2) [interpretation B]
```

The `TCM` keyword goes at the start of the explanation field, followed by `i:` with numbered options.

### Examples from Published Notes

**Job 9:35** - Idiomatic uncertainty
```
job	9:35	figs-idiom	I am not so with myself			TCM i:(1) I do not consider myself guilty (2) I am not in my right mind from fear
```

**Job 9:3** - Pronoun reference ambiguity
```
job	9:3	writing-pronouns	he wished to contend			TCM i:(1) God (2) a person who wanted to contend with God
```

**1 John 4:3** - Lexical polysemy
```
1jn	4:3	figs-explicit	is not from God			TCM i:(1) sent by God (2) having God as its source
```

### How It Works

1. The `TCM` keyword tells the tnwriter-dev pipeline to use a special prompt
2. The numbered options in `i:` provide the interpretations to include
3. The issue type (figs-idiom, writing-pronouns, etc.) provides template context
4. The generated note uses "This could mean: (1)... or (2)..." structure

### When to Use TCM

Use TCM when:
- English versions differ significantly on translation
- Commentaries acknowledge scholarly disagreement
- The text has genuine semantic ambiguity (not just translation difficulty)
- Multiple interpretations are equally valid

Do NOT use TCM when:
- There's a clear preferred interpretation
- The issue is translation difficulty, not semantic ambiguity
- The "options" are really just rephrasing the same meaning

## 7. Web Search Verification

When internal resources don't clarify, search for scholarly discussion:

**Search patterns:**
- `"[book] [chapter]:[verse] interpretation"`
- `"[Greek/Hebrew term] meaning [context]"`
- `"[book] [verse] commentary"`

**Look for:**
- Multiple commentaries offering different interpretations
- Phrases like "scholars disagree," "interpreters are divided"
- Different English translations handling the passage differently

**Confirmation of genuine ambiguity:**
- If sources consistently agree, it's not ambiguous
- If sources differ, include a "this could mean" note with the options found
