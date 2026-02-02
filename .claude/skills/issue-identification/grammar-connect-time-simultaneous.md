# grammar-connect-time-simultaneous

## Purpose
Identify when connecting words show that events occur at the same time and this may be unclear.

## Definition
A simultaneous clause connects events that occur at the same time. These are NOT cause-and-effect relationships - they simply happen together. Languages indicate simultaneity differently, using words like "while," "as," "during," or sometimes just "and." The issue is whether readers understand the events are concurrent.

## Key Distinction from Related Issues

| Issue | Core Question | Key Signal |
|-------|---------------|------------|
| figs-events | Events told in wrong order? | Reorder needed |
| grammar-connect-time-sequential | Events in sequence? | "then/after" words |
| grammar-connect-time-simultaneous | Events at same time? | "while/as/during" words |

**grammar-connect-time-sequential**: A happened, THEN B happened
**grammar-connect-time-simultaneous**: A and B happened AT THE SAME TIME

## Recognition Criteria

1. **Two or more events/actions** described
2. **Events occur simultaneously** - same time, not one after another
3. **No cause-effect relationship** - coincidence of timing, not reason-result
4. **Connecting word may need clarification** - "and" might not clearly show simultaneity

Common patterns:
- **"While/As/During"** - explicit simultaneity markers
- **"And... and"** - may indicate concurrent actions
- **Participle + main verb** - ongoing action during main event
- **Background + foreground** - ongoing state during punctual event

## Examples from Published Notes

### "And" showing simultaneous events
**Luke 1:21** "And the people were waiting... and they were wondering"
- Both actions at same time
- AT: "while the people were waiting... they were also wondering"

**OBS 8:4** "Joseph served his master well, and God blessed Joseph"
- Both happening during same period - no cause-effect implied
- Concurrent facts, not sequence

### "While/As" constructions
**Acts 1:10** "While they were looking intensely... as he was going up... two men stood"
- Three simultaneous events
- Disciples looking + Jesus ascending + men appearing

**Matt 26:7** "his head, he reclining to eat"
- Woman poured while Jesus was eating
- AT: "his head as he was reclining to eat"

### Participle showing ongoing action
**1 Cor 1:7** "gift, eagerly waiting for"
- Not lacking gift WHILE eagerly waiting
- AT: "gift while you eagerly wait for"

**1 Cor 11:4** "having something on his head"
- Covering head WHILE praying/prophesying
- AT: "while he has something on his head"

**Col 2:5** "rejoicing and seeing"
- Both happen during "being with them in spirit"
- AT: "When I think about you, I rejoice and see"

### Time indicators
**Luke 4:25** "during the days of Elijah"
- Widows existed AT THE SAME TIME AS Elijah's ministry
- Concurrent period, not sequence

**Neh 6:17** "Also, in those days"
- Introduces events happening at same time as previous events

**Neh 4:23** "And neither"
- Describes concurrent condition during rebuilding period
- AT: "At that time, neither"

### "Then/Meanwhile" showing concurrent events
**Matt 26:58** "But Peter followed"
- Happening WHILE Jesus was being led to Caiaphas
- AT: "Meanwhile" or "While that was happening"

**Matt 27:61** "Now Mary was sitting"
- Happening WHILE Joseph buried Jesus
- AT: "Meanwhile" or "While that was happening"

## NOT This Issue

### grammar-connect-time-sequential (NOT simultaneous)
When one event happens AFTER another:
- "Then Mary returned" - sequence, not simultaneous
- "After eating, he left" - sequence

### figs-events (NOT simultaneous)
When events are told in wrong chronological order:
- "He fled and feared" (feared first) - wrong order

### grammar-connect-logic-result (NOT simultaneous)
When one event CAUSES another:
- "He was angry, so he left" - cause-effect, not mere timing
- Result relationships have intentionality/causation

### grammar-connect-time-background
When providing narrative background context:
- Ongoing state setting scene for main action
- Background is specifically narrative framing

## Simultaneous vs. Result

Key test: Is there a CAUSAL connection?

| Type | Example | Relationship |
|------|---------|--------------|
| Simultaneous | "They waited AND wondered" | Just happening together |
| Result | "He saw AND therefore commanded" | Seeing CAUSED commanding |

Simultaneous: coincidence of timing
Result: one event explains/causes the other

## Decision Process

```
Are there two or more events described?
  |
  +-- No --> Not this issue
  |
  +-- Yes
        |
        Do events happen at the same time?
          |
          +-- No (sequence) --> grammar-connect-time-sequential or figs-events
          |
          +-- Yes
                |
                Is there a cause-effect relationship?
                  |
                  +-- Yes --> grammar-connect-logic-result
                  |
                  +-- No (just concurrent timing)
                        |
                        Is simultaneity unclear from connectors?
                          |
                          +-- Yes --> grammar-connect-time-simultaneous
                          |
                          +-- No --> No note needed
```

