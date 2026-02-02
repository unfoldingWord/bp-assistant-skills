# figs-simile

## Purpose
Identify similes (explicit comparisons using "like," "as," or "than") in biblical text for translation note tagging.

## Definition
A simile is a comparison of two things that are not normally thought to be similar. The simile focuses on a particular trait the two items have in common, and it **includes explicit comparison words**: "like," "as," or "than."

---

## Simile vs Metaphor: The Key Distinction

| Simile | Metaphor |
|--------|----------|
| **Explicit** comparison using "like," "as," "than" | **Implicit** - speaks of X as if it WERE Y |
| "Your teeth are **like** a flock of sheep" | "You are my rock" |
| "He will shine **as** the sun" | "The girl I love is a red rose" |
| "Sharper **than** any two-edged sword" | "I am the bread of life" |

**Recognition test**: If you can remove "like/as/than" and the sentence still describes X as Y, it becomes a metaphor. If comparison words are present, it's a simile.

---

## Simile Components

For each identified simile, extract:
1. **Subject**: The item being compared (Topic)
2. **Comparison word**: "like," "as," "than"
3. **Image**: The physical item used for comparison
4. **Point of comparison**: The shared trait (often implied)

Example: "My days are swifter **than** a shuttle" (Job 7:6)
- Subject: my days
- Comparison word: than
- Image: a shuttle (weaving tool)
- Point: speed/how quickly they pass

---

## Simile Categories

### Appearance Comparisons
Physical appearance likened to something else:
- "Your teeth like a flock of shorn sheep" (Song 4:2)
- "His face shone as the sun" (Matt 17:2)
- "His eyes like a flame of fire" (Rev 1:14)

### Quality/Characteristic Comparisons
Abstract qualities compared to tangible things:
- "Bitter as wormwood" (Prov 5:4) - disgust/bitterness
- "Like little" = has little value (Prov 10:20)
- "Like a man of shield" = complete, forceful (Prov 6:11)

### Action/Manner Comparisons
How something is done:
- "They run like warriors" (Joel 2:7)
- "I will come like a thief" (Rev 3:3) - unexpectedly
- "Like an ox to slaughter he goes" (Prov 7:22) - unknowingly

### Condition/State Comparisons
States of being:
- "We were like straying sheep" (1 Pet 2:25) - aimless
- "Like a dead man" (Rev 1:17) - lifeless/overcome
- "Like the grass" = numerous (Job 5:25)

### Speed/Intensity Comparisons
Using "than" for degree:
- "Sharper than any two-edged sword" (Heb 4:12)
- "My days are swifter than a shuttle" (Job 7:6)
- "As loud as a trumpet" (Rev 1:10)

---

## Hebrew/Greek Comparison Markers

| Language | Markers | Examples |
|----------|---------|----------|
| Hebrew | ke- (prefix), kemo | "like," "as" |
| Greek | hos, hosei, hosper, homoios | "like," "as," "similar to" |

---

## Recognition Process

1. **Look for comparison words**: "like," "as," "than," or their Hebrew/Greek equivalents

2. **Verify two distinct things being compared**: The subject and image should be genuinely different things (not just descriptive)

3. **Identify the point of comparison**: What trait do they share?

4. **Check if it's NOT simile**:
   - No comparison word = likely metaphor
   - Same category comparison (literal) = not figurative
   - Fixed idiom = use figs-idiom instead

---

## NOT figs-simile

### Literal comparisons (no figure of speech)
- "He was taller than his brothers" - factual comparison, not figurative

### Metaphors without comparison words
- "You are my rock" - no "like/as/than" = figs-metaphor
- "The Lord is my shepherd" - direct equation = figs-metaphor

### Expressions that became idioms
- Some simile-origin phrases have become fixed expressions - evaluate if still an active comparison or now idiom