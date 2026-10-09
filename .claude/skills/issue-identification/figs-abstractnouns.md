# figs-abstractnouns

## Purpose
Identify abstract nouns in biblical text that may need translation notes.

## Definition
Abstract nouns refer to attitudes, qualities, events, or situations that cannot be perceived through the five senses: happiness, weight, unity, friendship, health, reason, faith, righteousness, salvation.

Some languages use abstract nouns extensively (Greek, English). Others express these concepts with verb phrases: "forgiveness of sin" -> "God is willing to forgive people after they have sinned."

## Base the Decision on the ULT's English

Whether a note is needed depends on the ULT's English word, not on the Hebrew. If the ULT uses an English abstract noun, it can get a note even when the Hebrew is an adjective, verb, or concrete noun. If the ULT already uses a verb, adjective, or concrete noun, there is no abstract-noun note even when the Hebrew noun is abstract.

- JER 12:4 "the **wickedness** of those who dwell in it" (רָעָה): the ULT's English is abstract, so the note stands.
- JER 30:5 "**dread**" (פַּחַד) and JER 30:3 "**captivity**" (שְׁבוּת): editors kept these bot notes and only reworded them.

## Detection

- **Word list**: `data/abstract_nouns.txt` is the team's list. Check the ULT's nouns against it during verse-by-verse analysis.
- **Review table**: `data/abstract_nouns_review.csv` shows, for each English word, how often en_tn tags it, the Hebrew/Greek lemma behind it, and what editors did with bot notes. Rows marked `borderline`, `hold`, or `conflict` are waiting on a team ruling (`team_decision` column). Don't flag or drop those words on your own authority; follow the published notes for the book.
- **`detect_abstract_nouns` tool**: it currently matches English suffixes only (-ness, -tion/-sion, -ment, -ity, -ance/-ence, -dom, -ship, -hood, -ure, -ism) and does not read the word list (bp-assistant#465). Treat its output as candidates. It misses list words without those suffixes (fear, anger, pride, evil, wrath) and flags concrete -ure/-ment words (treasure, garment).

If you find a word with one of these suffixes, or a word on the list, and it names an attitude, quality, event, or situation rather than a concrete thing, flag it.

---

## When to Create a Note

Not every abstract noun needs a note. Create notes when:
1. Target language lacks abstract nouns for this concept
2. Source uses adjective but English uses abstract noun
3. Theological significance warrants explanation
4. Concept may be unfamiliar to readers

### Note Scope for Multiple Abstract Nouns

Create a separate issue for each abstract noun occurrence that needs a note. Do not combine abstract nouns from different poetic lines, parallel phrases, or other adjacent clauses into a single issue. For example, if one line contains "justice" and the parallel line contains "righteousness," create two issues so each line can receive its own note and its own alternate translation.

Only keep abstract nouns together when they function as a single fixed expression that must be reworded as one unit. Otherwise, prefer one issue per abstract noun.

---

## Common Categories

### Theological
faith, grace, righteousness, salvation, redemption, sanctification, justification

### Emotional/Relational
love, joy, peace, hope, fear, fellowship

### Moral/Ethical
sin, evil, truth, wisdom, knowledge, obedience

---

## NOT figs-abstractnouns

**Use figs-nominaladj for**: Adjectives functioning as nouns
- "the righteous" (adjective as noun for "righteous people")

**Hebrew infinitive constructs with a direct object**: When a Hebrew infinitive construct functions verbally (takes a direct object), it is not an abstract noun. For example, לָ⁠דַעַת אֶת־כְּבוֹד יְהוָה "knowing the glory of Yahweh" — "knowing" here is verbal, not abstract. Flag the direct object if it is abstract (e.g., "glory"), not the infinitive.

**Concrete nouns**: Physical objects even when symbolic
- "throne", "temple", "bread"

**Words for spoken or written communication**: Terms that refer to things people say, write, or enact are not abstract nouns -- they denote concrete communicative acts or their written/spoken products. Do not flag these:
- "commandment(s)", "statute(s)", "precept(s)", "ordinance(s)", "decree(s)"
- "testimony/testimonies", "law(s)", "rule(s)", "regulation(s)"
- "word(s)" (when referring to what someone said or wrote), "saying(s)", "promise(s)", "declaration(s)"
- "instruction(s)", "charge", "covenant", "oath"

These words may appear in doublets (figs-doublet) or parallelism but should not receive figs-abstractnouns notes. Even though some end in abstract-looking suffixes (-ment, -tion), they refer to concrete things that people speak, write, or establish.

---

## Examples from Published TNs

| Ref | Abstract Noun | Note Pattern |
|-----|---------------|--------------|
| ROM 1:4 | resurrection | "by being resurrected from the dead ones" |
| ROM 1:5 | grace, apostleship | "he who acted kindly toward us and made us his apostles" |
| ROM 1:5 | obedience, faith | "for people to faithfully obey Jesus" |
| 1JN 1:3 | fellowship | "share together" |
| 2TIM 3:15 | childhood | "when you were a child" |

---

## Translation Strategies

Reword using verb, adverb, or adjective:
- "salvation" -> "how God saves people"
- "faith" -> "trusting God"
- "his love" -> "how much he loves us"
- "godliness with contentment" -> "being godly and content"

The alternate translation must actually resolve the abstract noun into a non-abstract form (verb, adjective, adverb, or clause). Do not replace one abstract noun with another abstract noun. For example:
- BAD: "obedience" -> "faithful obedience" (still abstract)
- BAD: "salvation" -> "deliverance" (still abstract)
- BAD: "covenant faithfulness" -> "faithful love" ("love" is still abstract)
- BAD: "covenant faithfulness" -> "loyal love" ("love" is still abstract)
- GOOD: "obedience" -> "obeying him"
- GOOD: "salvation" -> "how God saves people"
- GOOD: "covenant faithfulness" -> "being faithful to his covenant"
- GOOD: "covenant faithfulness" -> "always faithfully keeping his promises"

Note: "covenant faithfulness" (chesed) is itself an abstract noun. When writing ATs for it, the result must not contain "love" or any other abstract noun. Verbalize it: "being faithful," "always keeping his promises," "faithfully doing what he promised," etc.
