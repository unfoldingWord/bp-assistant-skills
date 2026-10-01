# figs-activepassive

## Purpose
Identify ALL passive voice constructions in English ULT so translators whose languages lack passive voice can convert them to active.

## Definition
- **Active**: Subject performs action ("God created the world")
- **Passive**: Subject receives action ("The world was created")

Note: stative verbs are active, not passive.
- "his name alone is exalted" (passive -- subject receives the action of exalting)
- "his name is above all others" (stative = active -- describes a state)
- "he alone is truly great" (stative = active)

## Detection Instructions

Identify ALL passive voice constructions in the English ULT text. Every instance of passive voice needs a note -- over-detect rather than miss.

### Method 1: Identify by Form (Most Reliable)

English has two participles:
- Present participle: calling, seeing, trying, teaching
- Past participle: called, seen, tried, taught

The helping verb determines whether a past participle is active or passive:

| Pattern | Voice | Examples |
|---------|-------|---------|
| "have/has/had" + past participle | **Active** | "I have hidden", "she has seen", "they had tried" |
| "be/is/are/was/were/been/being" + past participle | **Passive** | "I am called", "she was seen", "they have been tried" |

So: **helping verb "be" + past participle = passive verb**

**Past participle indicators**:
- Regular: verbs ending in -ed (called, created, established)
- Irregular: given, taken, made, shown, known, seen, done, gone, born, borne, worn, torn, sworn, chosen, frozen, spoken, broken, stolen, written, hidden, driven, risen, forgiven, forgotten, begotten, eaten, beaten, shaken, forsaken, struck, sung, begun, led, fed, bled, paid, laid

**Note**: Up to two adverbs may appear between the auxiliary and participle: "was **not yet** revealed", "has **already been** given"

### Method 2: The "By" Phrase Test

If you can supply an agent with a "by" phrase, the verb is passive:
- "The ball was kicked fifty yards" -- passive ("kicked by the placekicker")
- "That ball looks as if it has been kicked around" -- passive ("kicked by the children")

If a "by" phrase makes no sense, the construction may be stative rather than passive.

### What to EXCLUDE (Not Passive)

**"Have" + past participle is ACTIVE**, not passive:
- "I have hidden your word in my heart" -- ACTIVE (subject performs the hiding)
- "they have hidden a trap for me" -- ACTIVE (subject performs the hiding)

**Stative adjectives** following "be" describe a state, not an action received:

ashamed, afraid, alone, afflicted, angry, anxious, aware, alive, asleep, awake, absent, able,
blessed, blameless, clean, certain, content, dead, drunk, empty, evil, full, faithful, free,
glad, good, great, guilty, gracious, holy, humble, hungry, happy, innocent, ill, jealous, just,
joyful, kind, like, lost, low, merciful, mighty, naked, near, obedient, old, perfect, pleasant,
poor, present, proud, pure, quick, quiet, ready, rich, righteous, right, sad, safe, sick, silent,
sinful, sorry, strong, sure, still, true, troubled, unclean, unworthy, upright, weary, weak,
well, whole, wicked, wise, worthy, wrong, young

**Linking verbs**: "was a man", "is the message" (identity, not action)

### Tricky Cases: Past Participles as Adjectives

A past participle may appear without a helping verb, functioning as an adjective.

**Before the noun -- treat as passive** (the ULT is reflecting a Hebrew passive participle):
- "this cursed woman" = "woman who has been cursed" (passive)
- "a highly regarded performance" = "performance that was regarded highly" (passive)
- "our hidden sin" = "sin that has been hidden" (passive)

**After the noun -- ambiguous, lean toward passive for ULT**:
- "another opportunity missed" could be passive or active
- In ULT context, assume passive unless Hebrew morphology says otherwise

**Predicate adjective with stative verb -- often active**:
- "The door is closed" -- this describes the door's state, not the action of closing
- "The house of Baal was filled mouth to mouth" -- could be stative ("was full") or passive ("was filled by people"). Check Hebrew morphology to decide.

When English is ambiguous, use the Hebrew morphology cross-reference below.

### Hebrew Morphology Cross-Reference

The Hebrew source marks verb stems that distinguish active from passive. When you read the Hebrew for context, check the `x-morph` attribute on verbs.

**Passive stems** -- English rendering should be flagged as passive:

| Morph code | Stem | Example |
|-----------|------|---------|
| `He,VN...` | Niphal | `x-morph="He,VNi3mp"` (passive when no reflexive meaning) |
| `He,VP...` | Pual | `x-morph="He,VPsmsa"` (always passive) |
| `He,VH...` | Hophal | `x-morph="He,VHi3mp"` (always passive) |
| `He,Vt...` | Hithpael | `x-morph="He,Vti3mp"` (passive when no reflexive meaning) |

Pual and Hophal are always passive. Niphal and Hithpael are passive when the meaning is not reflexive ("he hid himself" = reflexive/active; "he was hidden" = passive).

**Active stems** -- if English looks passive but Hebrew stem is active, double-check:

| Morph code | Stem |
|-----------|------|
| `He,Vq...` | Qal (active) |
| `He,VD...` | Piel (active) |
| `He,Vh...` | Hiphil (active) |

**Cross-reference rule**: When the English is ambiguous (could be passive or stative), the Hebrew morph is the tiebreaker. If the Hebrew verb is Pual, Hophal, or Niphal, flag as passive even if the English reads like an adjective or stative.

Example: "the house of Baal was filled" -- if Hebrew morph is `He,VNp3ms` (Niphal), this is passive. If morph is `He,Vqp3ms` (Qal), it may be stative.

Example: "our hidden sin" (Ps 90:8) -- English versions translate as "secret sins" (adjective), but if the Hebrew participle is in a passive stem, flag it as figs-activepassive.

### Worked Examples

| Construction | Passive? | Reason |
|-------------|----------|--------|
| "was called" | YES | be + past participle |
| "is written" | YES | be + past participle |
| "were sent" | YES | be + past participle |
| "has been given" | YES | be + been + past participle |
| "be fulfilled" | YES | be + past participle |
| "I have hidden your word" | NO | have + past participle = active |
| "they have hidden a trap" | NO | have + past participle = active |
| "my frame was not hidden from you" | YES | be + past participle |
| "my groanings are not hidden from you" | YES | be + past participle |
| "this cursed woman" | YES | participle adjective before noun |
| "was ashamed" | NO | stative adjective |
| "is afraid" | NO | stative adjective |
| "was a prophet" | NO | linking verb (identity) |
| "were righteous" | NO | stative adjective |
| "his name is above all others" | NO | stative (describes state, not received action) |

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
