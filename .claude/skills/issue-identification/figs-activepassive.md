# figs-activepassive

## Purpose
Identify ALL passive voice constructions in English ULT so translators whose languages lack passive voice can convert them to active.

## Definition
- **Active**: Subject performs action ("God created the world")
- **Passive**: Subject receives action ("The world was created")

## Detection Instructions

Identify ALL passive voice constructions in the English ULT text. Every instance of passive voice needs a note -- over-detect rather than miss.

### English Passive Voice Pattern
A passive construction consists of an **auxiliary form of "be"** followed by a **past participle**:

**Auxiliary verbs**: be, is, are, am, was, were, been, being

**Past participle indicators**:
- Regular: verbs ending in -ed (called, written, created, established)
- Irregular: given, taken, made, shown, known, seen, done, gone, born, borne, worn, torn, sworn, chosen, frozen, spoken, broken, stolen, written, hidden, driven, risen, forgiven, forgotten, begotten, eaten, beaten, shaken, forsaken, struck, sung, begun, led, fed, bled, paid, laid

**Note**: Up to two adverbs may appear between the auxiliary and participle: "was **not yet** revealed", "has **already been** given"

### What to EXCLUDE (Not Passive)

**Stative adjectives** following "be" describe a state, not an action received. These are NOT passive voice:

ashamed, afraid, alone, afflicted, angry, anxious, aware, alive, asleep, awake, absent, able,
blessed, blameless, clean, certain, content, dead, drunk, empty, evil, full, faithful, free,
glad, good, great, guilty, gracious, holy, humble, hungry, happy, innocent, ill, jealous, just,
joyful, kind, like, lost, low, merciful, mighty, naked, near, obedient, old, perfect, pleasant,
poor, present, proud, pure, quick, quiet, ready, rich, righteous, right, sad, safe, sick, silent,
sinful, sorry, strong, sure, still, true, troubled, unclean, unworthy, upright, weary, weak,
well, whole, wicked, wise, worthy, wrong, young

**Linking verbs**: "was a man", "is the message" (identity, not action)

### Worked Examples

| Construction | Passive? | Reason |
|-------------|----------|--------|
| "was called" | YES | auxiliary + past participle |
| "is written" | YES | auxiliary + past participle |
| "were sent" | YES | auxiliary + past participle |
| "has been given" | YES | compound auxiliary + past participle |
| "be fulfilled" | YES | auxiliary + past participle |
| "was ashamed" | NO | stative adjective |
| "is afraid" | NO | stative adjective |
| "was a prophet" | NO | linking verb (identity) |
| "were righteous" | NO | stative adjective |
| "is good" | NO | stative adjective (no action) |

### Divine Passive

When passive avoids naming God as agent, the active form names God:
- "Your sins are forgiven" -> "God has forgiven your sins"
- "It was given to him" -> "God gave it to him"
- "was revealed" -> "God revealed"

The divine passive is very common in biblical text. When you detect a passive where the agent is not stated, consider whether God is the implied agent.

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
