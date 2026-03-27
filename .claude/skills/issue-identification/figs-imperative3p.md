# figs-imperative3p

## Purpose
Identify third-person imperatives ("Let X do Y"), which many languages lack and translators need guidance to express naturally.

## Definition
A third-person imperative is a command directed at or about a third person (someone other than the speaker or direct addressee). In English, these are typically expressed with "Let" + third-person subject + verb:
- "Let there be light"
- "Let him hear"
- "Let no one boast"

Greek and Hebrew have specific grammatical forms for third-person imperatives that many languages lack.

---

## CONFIRMED figs-imperative3p Classifications

From Issues Resolved and processed translation notes:

| Type | Example | Classification | Notes |
|------|---------|----------------|-------|
| Divine creation | "Let there be light" | figs-imperative3p | God creating by command |
| Prayer/Wish | "Let your name be made holy" | figs-imperative3p | Lord's Prayer |
| Prayer/Wish | "Let your kingdom come" | figs-imperative3p | Lord's Prayer |
| Instruction | "Let each one be careful" | figs-imperative3p | Paul's teaching |
| Prohibition | "Let no one boast" | figs-imperative3p | Negative 3rd person |
| Prohibition | "Let no one despise your youth" | figs-imperative3p | 1 Timothy 4:12 |
| Permission | "Let them marry" | figs-imperative3p | Paul on marriage |
| Obligation | "Let a woman learn" | figs-imperative3p | 1 Timothy 2:11 |
| Obligation | "Let deacons be husbands of one wife" | figs-imperative3p | Church leadership |

---

## NOT figs-imperative3p (Use These Instead)

### Use figs-imperative for:
| Expression | Reason |
|------------|--------|
| "Give us our bread" | Second-person imperative (direct addressee) |
| "Do not be afraid" | Second-person imperative |
| Regular commands to "you" | Not third-person |

### Use figs-declarative for:
| Expression | Reason |
|------------|--------|
| "You will love your neighbor" | Statement (indicative), not imperative |
| "Blessed is the God and Father" | Declarative statement as exhortation |

### Key distinction:
- **figs-imperative3p**: "Let HIM/HER/IT/THEM do X" (third person is subject)
- **figs-imperative**: "Do X" or "You do X" (second person is subject)

---

## Categories with Examples

### 1. Divine Creation Commands
When God commands something into existence.

**Markers:**
- Speaker is God
- Command causes creation or change
- Often "Let there be..." or "Let it be done"

**Examples from processed notes:**
- "Let there be light" (Gen 1:3)
- "Let there be an expanse" (Gen 1:6)
- "Let it be done to you according to your faith" (Matt 8:13, 9:29)

### 2. Prayers and Wishes (Lord's Prayer Pattern)
When expressing a desire that something happen.

**Markers:**
- Often in prayer context
- "Let your..." or "May your..."
- Expresses wish for God's action

**Examples from processed notes:**
- "Let your name be made holy" (Matt 6:9)
- "Let your kingdom come" (Matt 6:10)
- "Let your will be done" (Matt 6:10)

### 3. Instructions to Third Parties (Epistles Pattern)
When giving instructions about what third parties should do.

**Markers:**
- Teaching or instructional context
- "Let him/her/them..." or "Let each one..."
- Speaker giving guidance for behavior

**Examples from processed notes:**
- "Let each one be careful how he builds" (1 Cor 3:10)
- "Let a man regard us as servants" (1 Cor 4:1)
- "Let a woman learn in silence" (1 Tim 2:11)
- "Let the husband give to the wife her due" (1 Cor 7:3)
- "Let them serve as deacons" (1 Tim 3:10)
- "Let the elders be considered worthy" (1 Tim 5:17)
- "Let brotherly love continue" (Heb 13:1)

### 4. Prohibitions (Negative Third-Person Imperatives)
When prohibiting something in the third person.

**Markers:**
- Negative particle + third-person imperative
- "Let no one..." or "Let not..."
- Often in teaching context

**Examples from processed notes:**
- "Let no one boast in men" (1 Cor 3:21)
- "Let no one despise your youth" (1 Tim 4:12)
- "Do not let anyone judge you" (Col 2:16)
- "Let not the sun go down on your anger" (Eph 4:26)
- "Let him not divorce her" (1 Cor 7:12)
- "Let her not divorce the husband" (1 Cor 7:13)

### 5. Permission
When granting permission for third parties to do something.

**Markers:**
- Context suggests allowance rather than command
- "Let them..."
- Speaker giving permission

**Examples from processed notes:**
- "Let them marry" (1 Cor 7:9, 7:36)
- "Let him go" (1 Cor 7:15) - allowing unbelieving spouse to leave

---

## Recognition Process

1. **Identify the form**: Is there a "Let + third-person subject + verb" construction?

2. **Confirm it's third-person**: Is the subject someone other than "you" (the addressee)?
   - If it's "Let us..." that's first-person plural, often hortatory
   - If it's "You let..." that's second-person
   - If it's "Let him/her/it/them/each one/no one..." that's third-person

3. **Determine the function**:

   | Question | If YES | Type |
   |----------|--------|------|
   | Is God causing creation by command? | Divine creation | figs-imperative3p |
   | Is it a prayer or wish? | Prayer/Wish | figs-imperative3p |
   | Is it an instruction about behavior? | Instruction | figs-imperative3p |
   | Is it prohibiting something? | Prohibition | figs-imperative3p |
   | Is it giving permission? | Permission | figs-imperative3p |

4. **First instance only**: Flag only the first third-person imperative in each chapter. Add `t: first instance` to its explanation. Do not flag subsequent jussives in the same chapter — the first-instance note directs translators to establish a team-wide approach that covers all later occurrences.

---

## Distribution by Genre

Based on 98 examples in processed notes:

| Genre | Count | Common Types |
|-------|-------|--------------|
| 1 Corinthians | 41 | Instructions, permissions, prohibitions |
| Matthew | 24 | Divine commands, Lord's Prayer, healing |
| 1 Timothy | 11 | Church order instructions |
| Other Epistles (Col, Heb, Rev, 2Ti, 2Co) | 13 | Various instructions |
| Mark | 9 | Divine commands, "Let him hear" |

**Key observations:**
- Third-person imperatives are predominantly NT Greek
- 1 Corinthians has the highest concentration (Paul's teaching on church order and conduct)
- Lord's Prayer accounts for several Matthew examples
- Rare in OT Hebrew (different construction)

---

## Critical Distinctions

### figs-imperative3p vs. figs-imperative:
- "Let no one boast" (3rd person subject) -> **figs-imperative3p**
- "Do not boast" (2nd person implied) -> **figs-imperative** (if non-standard use) or **NO NOTE** (if regular)

### figs-imperative3p vs. figs-declarative:
- "Let him be silent" (imperative form) -> **figs-imperative3p**
- "He will be silent" (indicative form as command) -> **figs-declarative**

### When to write a note:
- Write a note only for the **first** third-person imperative in each chapter
- Add `t: first instance` to its explanation so the note writer uses the team-decision template
- Do not flag subsequent jussives — the first-instance note covers the pattern for the whole chapter

---

## Relationship to figs-imperative

The main figs-imperative skill covers second-person imperatives used for non-command purposes (requests, conditions, etc.). This skill (figs-imperative3p) focuses specifically on third-person imperatives, which are a grammatical form issue rather than a function issue.

See also: [figs-imperative.md](figs-imperative.md)

