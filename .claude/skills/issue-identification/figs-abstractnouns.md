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
**Word list**: `.claude/skills/issue-identification/scripts/detection/abstract_nouns.txt` (577 words)

### Detection signals:
- English word matches abstract noun list
- Source morphology confirms noun (Gr,N... or He,N...)
- Source adjective translated as English noun (higher confidence)

### Supplementary: Catching Abstract Nouns Not in the Word List

The 591-word list provides a deterministic baseline but cannot be exhaustive. During your verse-by-verse analysis, also watch for words with these common abstract noun suffixes that may not be in the list:

- **-ness** (righteousness, faithfulness, kindness, wickedness)
- **-tion / -sion** (salvation, redemption, sanctification, justification, destruction)
- **-ment** (judgment, amazement, resentment, atonement)
- **-ity / -ety** (integrity, purity, prosperity, anxiety)
- **-ance / -ence** (obedience, endurance, repentance, reverence)

If you encounter a word with one of these suffixes that expresses an attitude, quality, event, or situation (not a concrete thing), flag it as a potential abstract noun even if the detection script didn't catch it.

---

## When to Create a Note

Not every abstract noun needs a note. Create notes when:
1. Target language lacks abstract nouns for this concept
2. Source uses adjective but English uses abstract noun
3. Theological significance warrants explanation
4. Concept may be unfamiliar to readers

### Combining Adjacent Abstract Nouns

When two or more abstract nouns appear in the same verse or adjacent phrases, combine them into a single issue rather than creating separate notes. For example, if a verse contains both "justice" and "righteousness" as abstract nouns, create one issue that covers both. This avoids cluttering the notes with repetitive "If your language does not use an abstract noun..." text. The single note can address both nouns with a combined AT.

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

**Words for spoken or written communication**: Terms that refer to things people say, write, or enact are not abstract nouns -- they denote concrete communicative acts or their written/spoken products. Do not flag these:
- "commandment(s)", "statute(s)", "precept(s)", "ordinance(s)", "decree(s)"
- "testimony/testimonies", "law(s)", "rule(s)", "regulation(s)"
- "word(s)" (when referring to what someone said or wrote), "saying(s)", "promise(s)"
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
