# grammar-connect-time-sequential

## Purpose
Identify when connecting words show that one event happened after another and the sequence may be unclear.

## Definition
A sequential clause connects two events where one happens and THEN the other happens. Languages indicate sequences differently - some use ordering, some use connecting words (then, after, before, when, and), some use relative tense. Translators need to communicate the order of events naturally in their language.

## Key Distinction from Related Issues

| Issue | Core Question | Key Signal |
|-------|---------------|------------|
| figs-events | Events told in wrong order? | Reorder needed |
| grammar-connect-time-sequential | Is sequence clear? | Connector clarification needed |
| grammar-connect-time-simultaneous | Events at same time? | "while/as/during" words |

**figs-events**: Text says "B then A" but A happened first - reorder events
**grammar-connect-time-sequential**: Text says "A and B" where B follows A - clarify the connector

## Recognition Criteria

1. **Two or more events/actions** described
2. **Events happen in sequence** - one AFTER the other
3. **Connecting word may be ambiguous** - "and," "then," or temporal word might not clearly show sequence
4. **Events ARE in correct order** - no reordering needed, just clarification

Common connecting words needing attention:
- **"And" (kai, waw-consecutive)** - may need "then" for clarity
- **"When" / "After"** - shows sequence but may need explicit connection
- **"Before"** - indicates sequence but reverses expected order
- **Participle + main verb** - "having done X, he did Y"

## Examples from Published Notes

### Greek "and" (kai) needing sequence clarification
**Luke 1:24** "And Elizabeth conceived"
- After the previous events, Elizabeth conceived
- AT: "Then"

**Luke 1:56-57** "and Mary returned... And Elizabeth's time came"
- Sequential events - Mary left, THEN Elizabeth gave birth
- AT: "then Mary returned... Then Elizabeth's time came"

### Hebrew "then" showing clear sequence
**Ezra 3:1** "Then came"
- "Then" indicates these events came after previous ones
- AT: "After this group had returned to Judah"

**Ezra 3:2** "Then arose Jeshua"
- Sequential to previous gathering
- AT: "Once everyone had gathered, arose"

### Participle constructions (Greek)
**Matt 2:1** "Jesus having been born... wise men arrived"
- Birth happened BEFORE wise men came
- AT: "after Jesus had been born"

**Heb 1:1** "having spoken... he spoke"
- Speaking to fathers BEFORE speaking through Son
- AT: "after speaking"

**Heb 5:9** "having been made perfect... he became"
- Perfection BEFORE becoming source of salvation
- AT: "after having been made perfect"

### "Before" constructions
**Isaiah 7:16** "For before the child knows... the land will be desolate"
- Land desolate FIRST, then child knows
- May need reordering: "the land will be desolate before the child knows"

### Time indicators
**Ezra 3:5** "And after this"
- Shows temporal sequence
- AT: "And from that time on"

**Matt 21:29** "afterward"
- Shows later action
- AT: "later that day"

## NOT This Issue

### figs-events (NOT grammar-connect-time-sequential)
When events are told in wrong order and need reordering:
- "He fled and feared" (feared first) --> figs-events
- "Open scroll and break seals" (break first) --> figs-events

### grammar-connect-time-simultaneous (NOT sequential)
When events happen at the same time:
- "while they prayed" - simultaneous
- "as he was going" - ongoing during another event
- "during those days" - same time period

### writing-newevent
When introducing a completely new episode:
- "After these things" starting new section
- "Now it happened in those days" - narrative transition

### grammar-connect-time-background
When providing ongoing context for main event:
- "While he was teaching" (background for what happened)

## Decision Process

```
Are there two or more events described?
  |
  +-- No --> Not this issue
  |
  +-- Yes
        |
        Do they happen in sequence (one AFTER the other)?
          |
          +-- No (same time) --> grammar-connect-time-simultaneous
          |
          +-- Yes
                |
                Are events in wrong order? (B told before A)
                  |
                  +-- Yes --> figs-events
                  |
                  +-- No (correct order)
                        |
                        Is the sequence connection unclear?
                          |
                          +-- Yes --> grammar-connect-time-sequential
                          |
                          +-- No --> No note needed
```

