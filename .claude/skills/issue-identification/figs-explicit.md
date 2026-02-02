# figs-explicit

## Purpose
Identify when a text contains assumed knowledge or implicit information that modern readers may not understand and which could be made explicit to aid comprehension.

## Definition
**Assumed knowledge** is whatever a speaker assumes his audience knows before he speaks. **Implicit information** is information the speaker does not state directly because he expects the audience to learn it from context or from combining assumed knowledge with explicit statements.

This issue addresses cases where translators may need to **ADD** information that the original author left unstated because original readers would have understood it.

## Key Differentiator: Direction of Information Flow
- **figs-explicit**: Implicit -> Explicit (ADD information for reader comprehension)
- **figs-explicitinfo**: Explicit -> Implicit (REMOVE redundant information)
- **figs-extrainfo**: Keep Implicit (DON'T add information; author was intentionally vague)

## Confirmed Classifications (from Issues Resolved)

### IS figs-explicit:
1. **"struck" meaning "defeated" or "killed"** - explaining the implied outcome
2. **Musical instructions** (e.g., "On Sheminith") - explaining what these mean with "see how" notes
3. **Clarifying referents** - when pronouns or descriptions refer to someone/something not named
   - "the one having called you" -> "God who called you"
   - "the one judging justly" -> "God, who judges justly"
4. **Explaining theological concepts** - when phrases have meanings readers may not know
   - "the last time" -> "when Jesus returns"
   - "in Christ" -> "in union with Christ through faith"
5. **Clarifying ambiguous phrases** - when multiple interpretations exist and clarity helps
6. **"answered and said" responding to situations** - when "answered" responds to a situation, not spoken words, a separate figs-explicit note explains this

### NOT figs-explicit (use these instead):
- **Redundant information that sounds unnatural** -> figs-explicitinfo
- **Author intentionally vague, original audience also didn't understand** -> figs-extrainfo
- **Idiomatic expressions** -> figs-idiom
- **Metaphorical language** -> figs-metaphor
- **Metonymy** ("name" representing "reputation") -> figs-metonymy

## Categories/Subtypes

### 1. Assumed Knowledge Notes
Reader needs background knowledge the original audience had:
- Cultural practices ("wash their hands" = ritual cleanliness, not hygiene)
- Historical facts (Tyre and Sidon were wicked cities)
- Theological concepts (day of judgment, the covenant)
- Geographical knowledge

**Pattern**: "SPEAKER assumes that readers will know KNOWLEDGE. You could say that explicitly if that would be helpful to your readers."

### 2. Implicit Meaning Notes
The text implies something that can be stated:
- Unstated referents ("the one having called you" = God)
- Implied outcomes ("struck" = defeated/killed)
- Implied agents (who does the action in a passive construction)

**Pattern**: "By **PHRASE**, SPEAKER means EXPLANATION. You could indicate this explicitly in your translation if that would be helpful to your readers."

### 3. Generic Implication Notes
Something is implied that readers should understand:
- Logical conclusions
- Unstated purposes or reasons
- Implied results

**Pattern**: "The implication is that IMPLIED. You could include this information if that would be helpful to your readers."

### 4. "See How" Notes
Referring back to earlier occurrences for consistency:
- Musical instructions in Psalms
- Repeated phrases with established meanings

**Pattern**: "See how you translated the similar expression in [reference]."

## Recognition Process

```
START: Does the text contain information the reader might not understand?
  |
  +--NO--> Not figs-explicit (no comprehension issue)
  |
  +--YES--> Was the original audience also confused/meant to be confused?
              |
              +--YES--> Use figs-extrainfo (preserve intentional ambiguity)
              |
              +--NO--> Is the "missing" information:
                        |
                        +-- Background knowledge original readers had? --> figs-explicit (assumed knowledge)
                        +-- Something implied that can be inferred? --> figs-explicit (implicit meaning)
                        +-- Redundant/extra wording in the source? --> figs-explicitinfo (opposite issue)
```

## Key Test Questions

1. **Would the original audience have understood this?** (Yes = potential figs-explicit if modern readers won't)
2. **Did the author want this to be unclear?** (Yes = figs-extrainfo instead)
3. **Is there extra information to remove, or missing information to add?** (Remove = figs-explicitinfo; Add = figs-explicit)
4. **Is this a cultural practice, historical fact, or theological concept readers may not know?** (Yes = figs-explicit)

## Common Patterns in Examples

### Clarifying Referents
- "the one having sent me" -> "God who sent me"
- "his ears are toward their request" -> "he listens to and grants their request"
- "the Chief Shepherd" -> "Jesus, the Chief Shepherd"

### Explaining Theological Terms
- "in the last time" -> "in the last time, when Jesus returns"
- "the revelation of his glory" -> "when he returns to earth"
- "disobeying the word" -> "refusing to believe the gospel"

### Making Actions Clear
- "struck" -> "defeated" or "killed"
- "judging impartially" -> "God, who judges impartially"

### Clarifying Ambiguous Phrases
Often presented as "this could mean" notes with multiple options:
- "foreknowledge" could mean: (1) God determined what would happen; (2) God knew what would happen

## Relationship to Other Issues

| If you see... | Use... | Because... |
|---------------|--------|------------|
| Reader needs background info | figs-explicit | Adding implicit -> explicit |
| Text has redundant wording | figs-explicitinfo | Removing explicit -> implicit |
| Author was intentionally vague | figs-extrainfo | Keep implicit; don't add |
| Common expression with fixed meaning | figs-idiom | It's an idiom, not missing info |
| Word represents something else | figs-metonymy | Association, not missing info |
