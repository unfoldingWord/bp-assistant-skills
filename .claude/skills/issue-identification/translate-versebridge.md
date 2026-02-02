# translate-versebridge

## Purpose
Identify when combining verses would help present information in a more logical order for readers.

## Definition
A verse bridge combines two or more verses when information needs to be rearranged for clarity. This typically happens when:
- A reason is given AFTER its result (but should come before)
- Events are described in a different order than they occurred
- Related information is split across verses but belongs together

The UST often models verse bridges; notes help translators decide whether to create them.

**CRITICAL: Verse bridges always involve MORE THAN ONE VERSE.** The reference field must contain a range (e.g., 1:1-2). A single verse cannot be a verse bridge.

## Key Decision from Issues Resolved

> "The convention for verse-bridge notes is to put the range in the Reference field (e.g. 1:1-2), put the relevant material from both verses in the Quote field, Occurrence = 1, and have an AT that models what the note suggests saying in the combined material."

## Recognition Criteria

1. **Information spans multiple verses** - content from verse X relates to content in verse Y
2. **Order would be clearer if rearranged** - reader understanding improves with different sequence
3. **UST often provides a model** - check if UST combines these verses

Common triggers:
- "For" at start of verse (gives reason for previous verse)
- Result-before-reason ordering
- Interrupted thought completed in next verse
- Comparison parts split across verses ("just as... so" spanning verses)
- Background information explaining the previous action

## Examples from Published Notes

### Reason-after-result (most common)

**Luke 22:18** "For I say to you that I will not drink from the fruit of the vine..."
- "For" gives reason why disciples should share wine (told in v17)
- AT combines verses to put reason before result

**Luke 22:22** "For the Son of Man goes..."
- Explains why one disciple will betray Jesus (stated in v21)
- Reason should precede result

**1 John 2:16** "For all that is in the world..."
- Gives reason why "if anyone loves the world, the love of the Father is not in him"
- Combine verses putting reason first

### Events out of order

**Mark 3:9-10** Jesus tells disciples to ready a boat... For he healed many
- The healing explains WHY he needs the boat
- Reorder: healing -> crowds press -> need boat

**Mark 5:27-28** She touched his cloak... For she was saying "If I touch..."
- Her thought preceded her action
- Reorder: thought -> then touch

**Mark 6:17-18** Herod seized John... For John was saying
- John's words caused the arrest
- Reorder: John spoke -> Herod arrested

### Comparison split across verses

**Job 14:11-12** "As waters disappear... so a man lies down"
- Sentence begins v11, completes v12
- AT: "Just as waters disappear from a lake and a river dwindles and dries up, so a man lies down and does not arise"

**Job 14:18-19** "Just as a falling mountain crumbles... so you destroy hope"
- Comparison spans both verses
- Create verse bridge to keep comparison together

### Order of information

**Mark 5:3-4** "No one was able to bind him... for he had often been bound"
- Evidence (often bound, broke chains) should precede claim (no one can bind)
- Reorder to put basis before assertion

**Mark 6:8-9** "Take nothing... but sandals"
- Positive and negative commands scattered
- Combine to group negatives together, positives together

### Long opening sentence

**1 John 1:1-3**
- Greek sentence runs from v1 to middle of v3
- Subject/verb come late; object comes first with long digression
- Verse bridge allows natural reordering

### Keeping related information together

**Luke 1:54-55**
- Information about Israel split across verses
- Combine to keep it together

**Genesis 3:2-3**
- Exception clause would naturally come first in some languages
- "Only the tree in the middle... we may not eat from"

## NOT This Issue

### figs-events (NOT translate-versebridge)
When events within a SINGLE verse are out of order:
- "they fled and feared" (single verse) -> figs-events
- Verse bridges require MULTIPLE verses

### grammar-connect-logic-result (NOT translate-versebridge)
When reason/result within one verse needs connector clarification:
- "He died, for he was wounded" -> clarify "for" meaning
- Verse bridge notes suggest COMBINING verses

### figs-infostructure
When information order within one verse could improve:
- Moving phrases for natural expression
- Not about combining verses

## Decision Process

```
Is information split across multiple verses?
  |
  +-- No --> Not translate-versebridge
  |
  +-- Yes
        |
        Would combining verses improve clarity?
          |
          +-- No --> Not translate-versebridge
          |
          +-- Yes
                |
                Is there a reason-after-result pattern?
                  |
                  +-- Yes --> translate-versebridge (result-reason subtype)
                  |
                  +-- No
                        |
                        Is a thought/comparison split across verses?
                          |
                          +-- Yes --> translate-versebridge (split thought)
                          |
                          +-- No
                                |
                                Would reordering events help?
                                  |
                                  +-- Yes --> translate-versebridge (reorder)
                                  |
                                  +-- No --> Probably not translate-versebridge
```

## Note Format Requirements

Per Issues Resolved convention:
- **Reference field**: Must be a RANGE (e.g., "5:3-4" not "5:3")
- **Quote field**: Include relevant material from BOTH/ALL verses
- **Occurrence**: Always 1
- **AT**: Model the combined, reordered text
