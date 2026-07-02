# grammar-connect-logic-contrast

## Purpose
Identify logical contrast relationships where one event, idea, or action is in opposition to another.

## Definition
A contrast relationship shows one event or item is in contrast or opposition to another. The speaker uses contrast to highlight differences, unexpected outcomes, or opposing ideas. In Scripture, many events did not happen as the people involved intended or expected.

---

## Categories

All categories below assume the English ULT does **not** already begin with "but" / "however" / "yet" / "nevertheless" / "instead" / "rather". If it does, the contrast is already explicit and no note is written (see "Hard rule" above). The examples below show implicit-contrast cases — usually clauses joined by "and" or by no connector at all.

### 1. Contrast Between Behaviors or Beliefs
Comparing how different groups think or act, where the ULT connector is "and" or absent.

| Expression | Contrast |
|------------|----------|
| "He has brought down rulers... **and** has exalted the lowly" (Luke 1:52) | "and" links opposite actions toward different groups — the contrast must be made explicit |

### 2. Contrast Between Expectation and Reality
What happened vs. what would normally be expected, where the ULT uses "and" rather than "but".

| Expression | Contrast |
|------------|----------|
| "They claimed to be wise, **and** they became foolish" (Rom 1:22, paraphrased pattern) | Connector "and" hides the surprise; the underlying meaning is contrastive |
| "Joseph her husband was a righteous man, **and** he did not want to expose her" (Matt 1:19 pattern) | "and" joins a description with what would be an unexpected reaction; implicit contrast |

### 3. Contrast Between Times (Past vs. Present)
**Markers**: implicit "now" where the contrast with a past state is left to the reader to infer

| Expression | Contrast |
|------------|----------|
| "**Now** the righteousness of God has been revealed" (when ULT uses bare "now") | Under the law (before) vs. revealed righteousness (now) — bare "now" without a contrastive marker may need a note |

### 4. Contrast Between Sources/Authorities (when not already signaled)

Only flag when the contrast between sources is not already carried by an explicit contrastive connective. If the ULT already reads "not I, but the Lord", the contrast is explicit and no note is needed.

### 5. Contrast to Introduce a New Point (when implicit)

Only flag when the introduction of the contrasting group is **not** already marked by "but"/"however". For example, a bare "the natural person…" following a description of "the spiritual person…" without any connector may need a note; "But the natural person…" does not.

### 6. Contrast Between Actions (Do This, Not That)

| Expression | Contrast |
|------------|----------|
| "He has brought down... **and** exalted the lowly" (Luke 1:52-53) | Opposite actions toward different groups, joined only by "and" |

Do NOT flag the parallel "Don't make provision for the flesh, **but** put on the Lord Jesus Christ" (Rom 13:14) — the "but" already makes the contrast explicit.

### 7. "Neither...Nor" Contrast
**Pattern**: "neither X if condition, nor Y if opposite condition"

| Expression | Contrast |
|------------|----------|
| "**neither** are we made to lack **if** we do not eat, **nor** do we abound **if** we eat" (1 Cor 8:8) | Both have same result |

The "neither…nor" construction itself is the contrastive scaffolding; this is flaggable even though the surface words include "nor", because the contrast structure may not survive translation in all languages.

NOTE: This verse has TWO issues: grammar-connect-logic-contrast (for neither...nor) AND grammar-connect-condition-hypothetical (for the if clauses).

---

## Common Contrast Words

### Greek Markers
| Greek | Translation | Usage |
|-------|-------------|-------|
| de | but, now, however | Mild contrast or transition |
| alla | but, instead, rather | Strong contrast |
| plen | nevertheless, yet, however | Introduces qualification |
| ou...alla | not...but | Direct opposition |
| oute...oute | neither...nor | Contrasting opposite statements |

### English Markers
but, yet, however, instead, rather, on the contrary, by contrast, nevertheless, nonetheless, despite, in spite of, although, even though, neither...nor

---

## When to Flag

**FLAG** if:
- The English ULT clause begins with **"and"** (or is asyndetic / has no connector) but the underlying contrast still needs to be made explicit for the translator
- The contrast is IMPLICIT or UNCLEAR
- The translator might miss the relationship between the ideas
- Different languages need different words to make the contrast clear

**Do NOT flag** if:
- The English ULT clause already begins with **"but"** — "but" is itself an explicit contrast marker, so the relationship is already clear and no `grammar-connect-logic-contrast` note is needed
- The clause begins with any other explicit contrast marker that already makes the relationship plain (e.g., "however", "yet", "nevertheless", "instead", "rather", "on the contrary")
- The contrast is already EXPLICIT and CLEAR

### Hard rule: do not write a `grammar-connect-logic-contrast` note for a clause that starts with "but"

The purpose of this note is to alert the translator that two ideas are in contrast when the English wording would not otherwise signal it. When the ULT already says "but", the signal is in the text. Writing a contrast note in that situation is redundant and is the bug this rule is designed to prevent.

If the only thing you would say is "**But** here marks a contrast between X and Y", drop the note. The note belongs on the "and"/asyndetic case, not on the "but" case.

If a clause beginning with "but" needs commentary for a *different* reason (e.g., "but" is functioning as a development marker rather than a contrast, or it introduces an exception), use the appropriate other issue type (see `grammar-connect-words-phrases` for non-contrastive "but", or `grammar-connect-exceptions` for exceptive "but").

---

## NOT grammar-connect-logic-contrast

### Use grammar-connect-exceptions for:
| Feature | This Issue | grammar-connect-exceptions |
|---------|------------|---------------------------|
| Pattern | Two things COMPARED as different | One item EXCLUDED from a group |
| "But" means | "however" / "in contrast" | "except" / "other than" |

**Quick Test**:
- Are two things being SET AGAINST each other? --> grammar-connect-logic-contrast
- Is one item being CARVED OUT from a group? --> grammar-connect-exceptions

| Expression | Why NOT contrast |
|------------|-----------------|
| "no one except the Father" | Exception from group "no one" |
| "nothing but leaves" | Exception from group "nothing" |
| "every sin... but sexual immorality" | Exception carved out from "every sin" |

### Use grammar-connect-condition-contrary for:
| Expression | Why NOT contrast |
|------------|-----------------|
| "If you had known... you would not have" | Counterfactual condition |
| "as if being present" | Contrary-to-fact condition |

### Use figs-parallelism for:
| Expression | Why NOT contrast |
|------------|-----------------|
| Parallel poetic lines | Parallelism, not logical contrast |

---

## Recognition Process

1. **Check the English connector first**:
   - Does the clause begin with **"but"**, "however", "yet", "nevertheless", "instead", "rather", or "on the contrary"? → **STOP. Do not write a `grammar-connect-logic-contrast` note.** The contrast is already explicit. Consider `grammar-connect-words-phrases` only if the connector is functioning non-contrastively, or `grammar-connect-exceptions` if it is functioning as "except".
   - Does the clause begin with **"and"**, with no connector at all, or with a neutral marker like "now"? → Continue.
2. **Identify what is being contrasted**: Two groups? Expectation vs. reality? Past vs. present?
3. **Check if contrast is clear despite the neutral connector**: Would the translator/reader catch the contrast without help? If yes, no note. If no, write the note.

**Key Test**: Two things are being compared as opposites or one is unexpected, **and** the English wording does not already say "but"/"however"/etc.

---

## Restraint Principle

The hard rule above (no note when the clause already begins with "but"/"however"/"yet"/etc.) does most of the restraint work here. Beyond it, flag only where a neutral connector genuinely hides a contrast a translator could miss.

Do not flag when:
- The clause already carries an explicit contrastive marker (the hard rule)
- The contrast is obvious from context despite the neutral connector
- The relation is really an exception (grammar-connect-exceptions) or parallelism (figs-parallelism)

Target: published narrative averages about 0.4 notes per 100 verses -- roughly one every two or three chapters. Poetry is a little higher (about 1.1), prophecy lower. This is a rare note; zero in a given chapter is normal.
