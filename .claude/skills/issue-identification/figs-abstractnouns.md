# figs-abstractnouns

## Purpose
Identify abstract nouns in biblical text that may need translation notes.

## Definition
Abstract nouns refer to attitudes, qualities, events, or situations that cannot be perceived through the five senses: happiness, weight, unity, friendship, health, reason, faith, righteousness, salvation.

Some languages use abstract nouns extensively (Greek, English). Others express these concepts with verb phrases: "forgiveness of sin" -> "God is willing to forgive people after they have sinned."

## Automated Detection

Detection script finds potential abstract nouns by word list matching and morphology verification.

```bash
# Full pipeline
python3 fetch_door43.py 1JN | \
  node parse_usfm.js --stdin | \
  python3 detect_abstract_nouns.py --stdin
```

**Script**: `.claude/skills/issue-identification/scripts/detection/detect_abstract_nouns.py`
**Word list**: `.claude/skills/issue-identification/scripts/detection/abstract_nouns.txt` (591 words)

### Detection signals:
- English word matches abstract noun list
- Source morphology confirms noun (Gr,N... or He,N...)
- Source adjective translated as English noun (higher confidence)

---

## When to Create a Note

Not every abstract noun needs a note. Create notes when:
1. Target language lacks abstract nouns for this concept
2. Source uses adjective but English uses abstract noun
3. Theological significance warrants explanation
4. Concept may be unfamiliar to readers

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

**Concrete nouns**: Physical objects even when symbolic
- "throne", "temple", "bread"

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
