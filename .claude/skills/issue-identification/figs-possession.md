# figs-possession

## Purpose
Identify when a possessive form expresses a relationship other than simple ownership, but only when the meaning is unclear without a note—especially when the relationship isn't already clarified by nearby issues like abstract nouns.

## Definition (from Translation Academy)
In English, grammatical possession (using "of," "'s," or possessive pronouns) indicates various relationships between nouns, not just ownership. Biblical Hebrew and Greek similarly use possessive forms for many relationship types that may not translate directly into other languages.

## Categories of Possession

### 1. Characterization
One noun characterizes or describes the other.
- "passions **of dishonor**" = dishonorable passions
- "Spirit **of holiness**" = the Holy Spirit (characterized by holiness)
- "man **of violence**" = violent man
- "word **of truth**" = true message
- "crown **of splendor**" = splendorous crown
- "curse **of Yahweh**" = curse that comes from Yahweh
- "path **of righteousness**" = righteous path
- "tongue **of falsehood**" = lying tongue

### 2. Source/Origin
The second noun is the source of the first.
- "gospel **of God**" = gospel from God
- "power **of God**" = power from God
- "wisdom **of God**" = wisdom from God
- "righteousness **of God**" = righteousness from God
- "sayings **of God**" = sayings from God

### 3. Content/Subject Matter
The first noun is about the second.
- "gospel **of the kingdom**" = gospel about the kingdom
- "news **of him**" = news about him
- "knowledge **of God**" = knowledge about God
- "testimony **of Christ**" = testimony about Christ

### 4. Object (second noun receives action)
The second noun is what the first acts upon.
- "fear **of Yahweh**" = fear directed toward Yahweh
- "love **of money**" = love directed at money
- "gifts **of Yahweh**" = gifts given TO Yahweh (not by Yahweh)
- "dread **of evil**" = dread of/about evil

### 5. Subject (second noun performs action)
The second noun performs the action named by the first.
- "the judgment **of God**" = God's judging
- "the baptism **of John**" = John's baptizing
- "love **of Christ**" = Christ loving us

### 6. Location/Association
The second noun indicates where the first is found or what it is associated with.
- "Bethlehem **of Judea**" = Bethlehem in Judea
- "birds **of the sky**" = birds in the sky
- "lilies **of the field**" = lilies in the field
- "blood **of his cross**" = blood shed on his cross
- "fire **of the altar**" = fire on the altar

### 7. Result/Outcome
The first noun results in or leads to the second.
- "way **of pleasantness**" = way resulting in pleasantness
- "tree **of life**" = tree giving life
- "hope **of glory**" = hope expecting glory

### 8. Composition/Material
The second noun describes what the first is made of or contains.
- "flames **of fire**" = fiery flames
- "containers **of wood**" = wooden containers
- "cup **of water**" = cup containing water

### 9. Social Relationship
The possessive indicates a social relationship, not ownership.
- "**my** God" = the God I worship (NOT: God whom I own)
- "priest **of Midian**" = priest who serves Midianites
- "companion **of her youth**" = companion she married in youth
- "daughters **of Jerusalem**" = women who live in Jerusalem

### 10. Part-Whole
One noun is part of the other.
- "Holy **of Holies**" = Most Holy (superlative - holiest of the holy)
- "Song **of Songs**" = Best Song (superlative)
- "doors **of my womb**" = doors of the womb that bore me (mother's womb)

### 11. Time-Related
The second noun specifies when.
- "day **of testing**" = day when testing occurred
- "time **of the appearing**" = time when appearing happened
- "wife **of your youth**" = wife you married in youth

## Confirmed Classifications (from Issues Resolved)

### IS figs-possession:
1. **"hand" suggesting power and possession** - use figs-possession when territory/possession is primary meaning ("I have made you the owner of X")

### NOT figs-possession (use these instead):
- **"hand" = power over people** - use figs-metonymy ("I have given you the power to conquer X")
- **"from their face" = because of them** - use figs-idiom
- **"from their face" = from their presence** - use figs-metonymy

## Recognition Process

```
START: Is there a possessive form (X of Y, Y's X, his/her/their X)?
  |
  +--NO--> Not figs-possession
  |
  +--YES--> Does the possessive form express simple ownership?
              |
              +--YES--> Probably not figs-possession (natural in most languages)
              |
              +--NO--> Is there an abstract noun in this phrase?
                        |
                        +--YES--> Flag figs-abstractnouns instead
                        |         Don't add figs-possession (suppressed)
                        |
                        +--NO--> Would the literal translation be unclear or misleading
                                 AND is the meaning not already clarified by the UST?
                                  |
                                  +--NO--> Don't flag (meaning is clear)
                                  |
                                  +--YES--> IDENTIFY THE RELATIONSHIP TYPE:
                                            |
                                            +-- Y characterizes X? --> Characterization
                                            +-- Y is source of X? --> Source/Origin
                                            +-- X is about Y? --> Content/Subject Matter
                                            +-- Y receives action of X? --> Object
                                            +-- Y performs action of X? --> Subject
                                            +-- Y is location of X? --> Location/Association
                                            +-- X results in Y? --> Result/Outcome
                                            +-- X is made of Y? --> Composition/Material
                                            +-- Social connection? --> Social Relationship
                                            +-- X part of Y or superlative? --> Part-Whole
                                            +-- Y specifies time? --> Time-Related
```

## Key Test Questions

1. **Would "X of Y" or "Y's X" sound unnatural if translated literally?**
2. **Is Y the owner, or is there another relationship (source, subject, object, characteristic)?**
3. **Can the relationship be clarified with "from," "about," "for," "characterized by," or a relative clause?**
4. **Is this an abstract noun as possessor (fear, wrath, judgment)?** - Check first if it needs a note

## Always Flag: "my/our/your God"

Flag every instance of "my God," "our God," and "your God" as `figs-possession` with `t:our God`. Use this template regardless of whether the UST seems to make the meaning clear.

The reason: in many languages, the possessive pronoun + "God" implies ownership or control, which is theologically misleading. The worship-relationship reading is non-obvious enough that a note is always warranted. Do not suppress based on UST clarity for this specific pattern.

Always use `t:our God` as the template hint regardless of pronoun (my/our/your). The tn-writer will adapt the speaker reference from context.

## When to Suppress figs-possession

Do NOT flag figs-possession when:

### Abstract Noun in Same Phrase
When the same phrase contains an abstract noun AND transforming that abstract noun would clarify the possession relationship, suppress the possession note. The abstract noun note will handle the clarification.

**Examples:**
- "fear of God" - flagging figs-abstractnouns (fear → being afraid) already clarifies the relationship. Don't add figs-possession.
- "power of God" - flagging figs-abstractnouns (power → powerful/to have power) already clarifies whether it's "power from God" or "God's power." Don't add figs-possession.
- "righteousness of God" - flagging figs-abstractnouns already indicates whether it's "to be righteous" or "righteous character," clarifying the relationship. Don't add figs-possession.

### Meaning Already Clear from UST
Check the UST version. If the UST makes the possession relationship clear without ambiguity, suppress the note. The simplification itself handles the translation challenge.

**Example:**
- ULT: "the judgment of God"
- UST: "when God judges"
- The UST already clarifies this is "God's judging" (subject possession). Don't add figs-possession.

### Simple Possessive Ownership
Natural possessives in most languages don't need notes. Only flag when the relationship is genuinely non-obvious or would be misleading if translated literally.

## Common Patterns by Genre

### Epistles (especially Paul)
Heavy use of theological possessives:
- "righteousness of God" (from/characterizing God)
- "gospel of God/Christ" (from/about God/Christ)
- "Spirit of holiness" (characterized by holiness)
- "obedience of faith" (characterized by faith OR resulting from faith)

### Proverbs/Wisdom Literature
Characterization possessives common:
- "fear of Yahweh" (fear directed toward Yahweh)
- "way of righteousness" (righteous way)
- "man of violence" (violent man)
- "words of understanding" (wise words)

### Leviticus/Law
Technical possessives:
- "holy of holies" (most holy - superlative)
- "gifts of Yahweh" (gifts TO Yahweh - object)
- "law of the burnt offering" (concerning burnt offerings)

### Narratives
Location and social relationship:
- "Bethlehem of Judea" (in Judea)
- "priest of Midian" (serves Midianites)
- "daughters of Jerusalem" (women from Jerusalem)

## Ambiguous Possessives

Some possessives have multiple possible meanings. Common ambiguous patterns:

| Phrase | Possible Meanings |
|--------|------------------|
| "love of Christ" | Christ's love for us OR our love for Christ |
| "word of God" | message FROM God OR message ABOUT God |
| "righteousness of God" | righteousness FROM God OR God's own righteousness |
| "faith of Christ" | faith IN Christ OR Christ's faithfulness |
| "hope of glory" | hope FOR glory OR glorious hope |

For ambiguous cases, notes may present both options: "This could refer to: (1) ... Alternate translation: [...] or (2) ... Alternate translation: [...]"

## Template Hints in Explanation

When outputting a figs-possession issue, include a `t:` prefix in the explanation to indicate which template the note-writer should use. There are three templates:

- `t:characterization` -- when one noun characterizes or describes the other (e.g., "crown of splendor," "man of violence," "path of righteousness")
- `t:general` -- for other non-ownership relationships (source, subject, object, location, composition, time, etc.)
- `t:our God` -- only for the specific "my/our God" worship-relationship pattern

Examples:
```
psa	61:3	figs-possession	a strong tower	 	 	t:characterization
gen	2:9	figs-possession	tree of life	 	 	t:general Result/Outcome: tree that gives life
deu	1:6	figs-possession	our God	 	 	t:our God
```

Most characterization cases should use `t:characterization`. When the relationship is not characterization and not the "our God" pattern, use `t:general` and briefly state the relationship type after it (e.g., "t:general Source: message from God").

## Relationship to Other Issues

| If you see... | Use... | Because... |
|---------------|--------|------------|
| Possessive expressing relationship | figs-possession | Non-ownership possessive (only if not clarified by abstract noun in same phrase) |
| "hand" = power (people context) | figs-metonymy | Association with power |
| "face" = presence | figs-metonymy | Association with presence |
| "from the face of" = because of | figs-idiom | Fixed cultural expression |
| Abstract noun needing verbal form | figs-abstractnouns | Abstract -> concrete (supersedes possession note if same phrase) |

### Key Decision Point
When a phrase contains both an abstract noun AND a possessive form (like "fear of God," "power of God," "righteousness of God"):
1. **Always** flag the abstract noun for figs-abstractnouns
2. **Suppress** figs-possession because transforming the abstract noun clarifies the relationship
3. Example: "fear of God" only needs figs-abstractnouns. The abstract noun note explains whether it's "fear toward God" or contextual fear. Don't add a separate possession note.

