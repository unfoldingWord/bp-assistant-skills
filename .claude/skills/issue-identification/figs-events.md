# figs-events

## Purpose
Identify when events are narrated out of chronological order.

## Definition
The biblical text sometimes describes events in a different order than they actually occurred. The author may mention a later event before an earlier one, often for literary emphasis, thematic grouping, or Hebrew narrative style. This can confuse readers who assume events happened in the order they are told.

## Key Distinction from Related Issues

**figs-events** focuses on events narrated OUT OF ORDER - the author describes Event B before Event A, but Event A happened first.

**grammar-connect-time-sequential** focuses on CONNECTING WORDS (then, after, before, when, and) showing one event happened AFTER another - the issue is whether readers understand the sequence.

**grammar-connect-time-simultaneous** focuses on CONNECTING WORDS (while, as, during, and) showing events happened AT THE SAME TIME - not one after the other.

| Issue | Core Question | Typical Solution |
|-------|---------------|------------------|
| figs-events | Are events told in wrong order? | Reorder events chronologically |
| grammar-connect-time-sequential | Is the sequence clear? | Clarify connecting word (then, after) |
| grammar-connect-time-simultaneous | Is simultaneity clear? | Clarify connecting word (while, as) |

## Recognition Criteria

1. **Two or more events mentioned** - there must be multiple actions/events
2. **Logical or chronological inversion** - the natural order would be A then B, but text says B then A
3. **Context reveals the correct order** - reader can determine actual sequence from narrative logic

Common patterns:
- "After X, Y happened" when Y logically precedes X
- "He did X and Y" when Y must have preceded X
- Compound actions where second action must happen first (break seals BEFORE open scroll)
- Summary followed by details that occurred earlier

## Examples from Published Notes

### Event described before its prerequisite
**Rev 5:2** "Who is worthy to open the scroll and break its seals?"
- Seals must be broken BEFORE the scroll can be opened
- Physical logic requires reordering

**Luke 3:20-21** Herod locked John in prison (v20), then John baptized Jesus (v21)
- But John baptized Jesus BEFORE being imprisoned

### Verb pairs out of logical order
**1 Sam 17:24** "they fled from his face and feared greatly"
- They feared FIRST, then fled
- AT: "they feared greatly and fled from his face"

**1 Sam 19:2** "stay in a secret place and hide yourself"
- Must hide FIRST, then stay
- AT: "hide yourself and stay in that secret place"

**Job 16:9** "he has torn me and he has attacked me"
- Must attack BEFORE tearing
- AT: "he has attacked me and he has torn me"

### Actions described then explained
**Judges 8:11** "And he struck the camp, and the camp was in security"
- Camp was secure BEFORE the attack
- AT: "the soldiers were feeling secure, but he attacked their camp"

### Question pairs
**Judges 19:17** "Where are you going and from where are you coming?"
- Must first ask where coming from, then where going

## NOT This Issue

### grammar-connect-time-sequential (NOT figs-events)
When events are in correct order but connector needs clarification:
- "And Jesus was born... And wise men came" - need "then" to show sequence
- "Having seen the crowd, he commanded" - participle shows prior action

### grammar-connect-time-simultaneous (NOT figs-events)
When events happen at the same time:
- "while praying... he saw a vision" - simultaneous, not out of order
- "as he was walking" - ongoing action, not sequencing

### figs-infostructure
When information could be reordered for clarity but isn't about event sequence:
- Rearranging subject/object for emphasis
- Moving modifiers for natural expression

## Decision Process

```
Are multiple events/actions described?
  |
  +-- No --> Not figs-events
  |
  +-- Yes
        |
        Does the logical/chronological order differ from text order?
          |
          +-- No --> Not figs-events (may be sequential/simultaneous)
          |
          +-- Yes
                |
                Would reordering make the sequence clearer?
                  |
                  +-- Yes --> figs-events
                  |
                  +-- No (connecting words would help instead)
                        |
                        --> grammar-connect-time-sequential
```

