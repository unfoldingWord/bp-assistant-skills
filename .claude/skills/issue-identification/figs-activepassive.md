# figs-activepassive

## Purpose
Identify ALL passive voice constructions in English ULT so translators whose languages lack passive voice can convert them to active.

## Definition
- **Active**: Subject performs action ("God created the world")
- **Passive**: Subject receives action ("The world was created")

## Automated Detection

Detection script finds ALL English passive constructions (auxiliary + past participle):

```bash
# Full pipeline
python3 fetch_door43.py 1JN | \
  node parse_usfm.js --stdin | \
  python3 detect_activepassive.py --stdin
```

**Script**: `.claude/skills/issue-identification/scripts/detection/detect_activepassive.py`

### English passive patterns detected:
- be/is/are/am/was/were/been/being + past participle
- "was called", "is written", "were sent", "has been given", "be fulfilled"

## When to Create a Note

**EVERY English passive needs a note** (per Issues Resolved). The standard note pattern:
> "If your language does not use this passive form, you can express this with an active form."

Provide an alternate translation showing active form.

## Note Patterns from Published TNs

| Passive | Active Alternative |
|---------|-------------------|
| "was born" | "who gave birth to" |
| "called Christ" | "whom people call Christ" |
| "has been forgiven" | "God has forgiven" |
| "be fulfilled" | "we will be completely happy" |
| "been begotten" | "God is the father of" |
| "be put to shame" | "be ashamed" |

## Divine Passive

When passive avoids naming God as agent, the active form names God:
- "Your sins are forgiven" -> "God has forgiven your sins"
- "It was given to him" -> "God gave it to him"

## NOT figs-activepassive

**Stative constructions**: "is light", "is good" (no action)
**Linking verbs**: "was a man", "is the message" (identity, not action)
