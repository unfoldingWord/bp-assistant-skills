# translate-alternativereadings

## Purpose
Identify places in the Hebrew Old Testament where the written text (Ketiv) has a marginal correction (Qere) or where the Hebrew text is problematic and an alternative reading may be preferable.

## Definition
Alternative readings address situations in the Hebrew Bible where:
1. **Qere/Ketiv**: Later scribes put marginal notes recommending readers speak a different word than what is written
2. **Problematic Text**: The written Hebrew seems to have errors or makes no sense, and alternative readings (from LXX, other versions, or scholarly emendation) may better represent the original

This is distinct from textual variants (which involve different manuscript copies). Alternative readings concern decisions about how to interpret/read a single Hebrew manuscript tradition.

---

## Related Issue: Textual Variants

**Alternative Readings** (this skill) and **Textual Variants** (`translate-textvariants`) are connected but distinct:

| Aspect | Alternative Readings | Textual Variants |
|--------|---------------------|------------------|
| **Scope** | Hebrew OT only | Greek NT and Hebrew OT |
| **Issue** | How to read the Hebrew text | Different manuscripts have different words |
| **Types** | Qere/Ketiv, LXX corrections, emendations | Manuscript family differences |
| **Question** | "Which reading of Hebrew to follow?" | "Which manuscript copy to follow?" |

Use **translate-alternativereadings** when:
- Masoretic scribes marked a marginal reading (Qere)
- Hebrew text seems corrupted or nonsensical
- LXX or other versions preserve a better reading

Use **translate-textvariants** when:
- Different manuscript copies have different words
- Both readings are valid traditions across manuscripts

---

## Types of Alternative Readings

### 1. Qere/Ketiv (Marginal Corrections)
The Masoretes (Hebrew scribes) preserved the written text (Ketiv) but recommended speaking a different word (Qere) in the margin.

**Reasons for Qere readings:**
- **Updating archaic spelling**: Older forms modernized for pronunciation
- **Euphemism**: Replacing vulgar or offensive words for public reading
- **Grammar correction**: Fixing perceived errors
- **Theological sensitivity**: Avoiding anthropomorphisms about God

**Example (Ruth 3:3-4)**:
- Written (Ketiv): "I will go down...and I will lie down"
- Marginal (Qere): "go down...and lie down"
- Reason: Naomi's 1st-person speech was changed to 2nd-person instructions

**Example (Esther 3:4)**:
- Written: "when they spoke..."
- Marginal: "as they spoke..."

### 2. Corrupted Text Requiring Emendation
Sometimes the Hebrew text appears to have copying errors that neither the written nor marginal text corrects.

**Example (1 Samuel 13:1)**:
- Hebrew: "Saul was a son of a year in his becoming king"
- LXX: "Saul was a son of thirty years in his becoming king"
- Issue: A number appears to have been lost in transmission

**Example (Psalm 103:5)**:
- Hebrew: "satisfying your ornaments with good"
- Proposed: "satisfying your existence with good"
- Issue: Similar-looking Hebrew words (scribal confusion)

### 3. LXX Preserves Better Reading
The Septuagint (Greek translation from ~250 BC) sometimes preserves readings that seem more original than the Masoretic Text.

---

## Recognition Process

1. **Check ULT footnotes**: Major alternative readings are often noted

2. **Hebrew text seems problematic**: Numbers missing, grammar breaks down, or meaning is unclear

3. **LXX differs significantly**: Greek translation has coherent reading where Hebrew does not

4. **Scholarly apparatus notes Qere**: Critical editions mark Qere/Ketiv distinctions

5. **Compare translations**: Some translations follow Qere, others Ketiv

---

## Examples by Category

### Qere for Euphemism
Scribes recommended polite alternatives for crude expressions in public reading.

### Qere for Person/Number
Changes from 1st to 2nd person, singular to plural, etc. (as in Ruth 3:3-4).

### Numeric Corruption
Missing or garbled numbers, especially in regnal formulas (1 Samuel 13:1).

### Lexical Confusion
Similar-looking Hebrew words confused by copyists (Psalm 103:5).

---

## NOT translate-alternativereadings

### Use translate-textvariants when:
- Different manuscripts have different words
- The issue is Greek NT manuscript traditions
- Multiple manuscript families attest different readings

### Use figs-euphemism when:
- The biblical author used euphemism (not later scribes)
- The figure of speech is part of the original composition

---

