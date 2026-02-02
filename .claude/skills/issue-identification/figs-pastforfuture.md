# figs-pastforfuture

## Purpose
Identify instances where past tense is used to describe future events, particularly in prophecy to emphasize certainty.

## Definition (from Translation Academy)
The **predictive past** (also called "prophetic perfect") is a figure of speech that uses the past tense to refer to things that will happen in the future. This is commonly done in prophecy to show that the event will certainly happen - as if it has already occurred because God has decreed it.

Key characteristics:
- Past tense verb forms describing future events
- Emphasizes certainty of the event
- Common in prophetic speech and divine promises
- The speaker treats the future as already accomplished

---

## CRITICAL: Relationship to translate-tense

### The Overlap Problem
Both `figs-pastforfuture` and `translate-tense` address irregular tense usage. Their relationship:

| Issue | Scope | Status |
|-------|-------|--------|
| figs-pastforfuture | Past for Future only | Active (41+ published examples) |
| translate-tense | All irregular tenses (past->future, present->past, present->future) | Broader category, fewer examples |

### Issues Resolved Decision (Oct 15, 2025)
> "Since the aspect (perfect vs. imperfect) varies in poetry, we do not need to represent perfects with the English past tense and then write **translate-tense** or **figs-pastforfuture** notes suggesting a future-tense or habitual-present-tense AT. We can use the appropriate English tense in the ULT to indicate what the writer is doing, for example, making a general statement."

**Implication**: In poetry, use the appropriate tense in ULT and SKIP these notes.

---

## When to Use figs-pastforfuture

### USE figs-pastforfuture for:
- Prophetic statements using past tense for future certainty
- Divine promises spoken as if already accomplished
- Prose passages (not poetry) with past-for-future usage

### DO NOT USE figs-pastforfuture for:
- Poetry where aspect naturally varies (per Issues Resolved)
- General/habitual statements (just use appropriate tense in ULT)
- Present-for-past (historical present) - use translate-tense
- Present-for-future (imminent future) - use translate-tense

---

## Examples from the Bible

### Classic Prophetic Past Examples:

**Joshua 6:2** (God speaking before conquest):
> "See, I **have delivered** Jericho, and its king, and its powerful soldiers into your hand."
- Jericho not yet conquered, but God speaks as if done
- Shows divine certainty
- AT: "I will deliver" or "I am about to deliver"

**Isaiah 9:6** (Messianic prophecy):
> "For to us a child **has been born**, to us a son **has been given**"
- Future birth spoken in past tense
- Prophetic certainty
- AT: "will be born... will be given"

**Isaiah 5:13** (Judgment prophecy):
> "Therefore my people **have gone** into captivity"
- Future exile spoken as already happened
- Shows inevitability
- AT: "will go into captivity"

**Jude 1:14** (Enoch's prophecy):
> "Look! The Lord **came** with thousands and thousands of his holy ones."
- Future coming described in past tense
- AT: "will come"

### From Published Notes (figs-pastforfuture):

**Zephaniah 2:15**:
> "How it **has become** a ruin"
- Future destruction spoken as past
- AT: "How it will become a ruin"

**Colossians 3:9**:
> "you **have stripped off** the old man"
- Completed action perspective on ongoing reality

---

## WARNING: Published Notes Inconsistency

In the published translation notes, there is inconsistency:

| Book | Usage | Note |
|------|-------|------|
| Zephaniah, Colossians | Past for future | Correct per TA |
| **John (41+ instances)** | **Present for past** | **CONTRADICTS TA definition** |

The John notes use figs-pastforfuture for "historical present" (present tense in past narration), which according to TA should be translate-tense "present for past."

Example from John 1:15:
> "John **testifies** about him" (present tense describing past)

This is technically translate-tense usage, not figs-pastforfuture per the TA article.

---

## Translation Strategies

From Translation Academy:

1. **Use future tense** to refer to future events
   - "has been born" -> "will be born"

2. **Use "about to" form** for immediate future
   - "I have delivered" -> "I am about to deliver"

3. **Use present tense** (some languages) for imminent events
   - "I have delivered" -> "I am delivering"

---

## Recognition Process

1. **Identify tense mismatch**: Is past tense used for a future event?

2. **Check context**:
   - Is this prophecy or divine speech?
   - Is the event clearly future from context?
   - Is this emphasizing certainty?

3. **Check if poetry**: If in poetic text with varying aspect:
   - Per Issues Resolved, use appropriate tense in ULT
   - No note needed

4. **Verify direction of mismatch**:
   - Past -> Future: figs-pastforfuture
   - Present -> Past: translate-tense (present for past)
   - Present -> Future: translate-tense (present for future)

---

## Distinguishing from translate-tense

| Criterion | figs-pastforfuture | translate-tense |
|-----------|-------------------|-----------------|
| Tense direction | Past for Future only | All directions |
| Primary use | Prophecy, divine certainty | Broader (narrative, general statements) |
| TA status | Active | Active |
| Templates | None in templates.csv | 3 templates available |

**Recommendation**: For past-for-future cases in prophecy, prefer figs-pastforfuture (more specific). For historical present (present-for-past) and other tense irregularities, use translate-tense.

---

