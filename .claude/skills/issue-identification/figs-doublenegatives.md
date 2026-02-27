# figs-doublenegatives

## Purpose
Identify double negatives - clauses with two negative words/elements where the negatives interact grammatically.

## Definition
A double negative occurs when a clause has two words that each express "not." This includes:
- Negative particles (not, no, never, nor, neither)
- Negative verbs (reject, despise, refuse, stop, lack, cease)
- Negative prefixes/suffixes (un-, im-, -less, without)
- Negative pronouns/adverbs (nothing, no one, nowhere, never)

## Key Decision (Issues Resolved Oct 29, 2025)
Use figs-doublenegatives for BOTH:
1. **Grammatical double negatives** - Two negative particles (Greek ou me)
2. **Negated antonyms** - Negative + negative verb ("have not forsaken" = keep)

## Categories

### 1. Greek Emphatic Double Negative (ou me)
Two negative particles used together for emphasis.
- "he must never drink" (ou me pie) - emphatic prohibition
- "nothing will harm you at all" (ouden humas ou me adikese)
- "certainly not" (me ouk)

Result: Creates emphatic negation (stronger "never" or "certainly not")

### 2. Negative + Negative Verb
Negative particle combined with a verb that has negative meaning.
- "did not waver" (ou diekrithe) = remained steady
- "not refuse" (ouk ethelesen athetesai) = allowed
- "not stopped" (ou dielipen) = continued
- "do not despise" (al-tim'as / lo bazah) = accept
- "will not reject" (lo yim'as) = accept
- "does not forget" / "do not forget" (lo shakach) = remembers
- "did not rebel" (lo maru) = obeyed
- "is not silent" (al-yecherash) = speaks

Result: Creates positive meaning (continued, allowed, appreciate, accept, remembers).
The positive restatement is the plain opposite -- no intensifier needed.

This is the most common pattern in Psalms. See "NOT This Issue" for how to distinguish from litotes.

### 3. Negative + "Without"
- "not without honor" (ouk estin atimos)
- "not without swearing an oath" (ou choris horkomosias)
- "not without blood" (ou choris haimatos)

Result: Creates positive meaning with emphasis (has honor, with oath, with blood)

### 4. Negative + Prefix Word (un-, im-, -less)
- "not impossible" (ouk adunateo)
- "not useless" (ouk akenos) - see litotes if emphatic
- "without hypocrisy" (anupokritos)
- "not ignorant" (ouk agnoeo)

Result: Creates positive meaning (possible, sincere, informed)

### 5. Two Negative Terms in Same Clause
- "told no one anything" (oudeni apeggeilan ouden)
- "owe nothing to no one" (medeni meden opheilete)
- "nothing hidden that will not be revealed"
- "there was not a house where there was not someone dead"

Result: Emphatic negative or positive depending on construction

### 6. Hebrew Negative + Negative Noun
- "let injustice not be" (al-tehi 'awlah) = let there be justice
- "not emptily" (lo reqam) = with many things/fully

## NOT This Issue

### Use figs-litotes instead when:
- The positive restatement needs an intensifier (very, great, completely) to capture the meaning
- "no small disturbance" = GREAT disturbance (not just "some disturbance")
- "I will lack nothing" = I will have EVERYTHING I need (goes beyond "enough")
- "does not wither" = strong and green (goes beyond "stays alive")

### Other issues:
- Simple negative statements (no double element) - no note needed
- "neither...nor" lists - may be parallelism or doublet if synonymous
- Conditional "if not" - usually grammar-connect-condition-hypothetical

## Recognition Process

```
Is there a clause with two negative elements?
  |
  +-- Are there two Greek negative particles (ou me, me ouk)?
  |     --> figs-doublenegatives (emphatic negation)
  |
  +-- Is there negative + negative verb (not + refuse/reject/despise/forget/rebel)?
  |     --> Apply the intensifier test: restate as positive.
  |           |
  |           +-- Plain opposite suffices ("does not despise" = accepts)
  |           |     --> figs-doublenegatives
  |           +-- Needs intensifier ("did not delight" = hated, "does not wither" = very green)
  |                 --> figs-litotes
  |
  +-- Is there "not without" or "not + un-/im-/-less"?
  |     --> Apply the intensifier test (same as above)
  |
  +-- Are there two negative pronouns/adverbs (no one...nothing)?
        --> figs-doublenegatives
```

## Examples from Published Notes

**Psalms - negative + negative verb (most common pattern):**
- PSA 9:12 "he does not forget" = he surely remembers
- PSA 15:5 "will not be shaken" = will remain secure
- PSA 16:8 "I will not be shaken" = he makes me live securely
- PSA 50:3 "he is not silent" = he is going to speak
- PSA 92:15 "no unrighteousness in him" = he is always righteous
- PSA 102:17 "he does not despise their prayer" = he accepts their prayer
- PSA 103:2 "do not forget" = remember
- PSA 105:28 "they did not rebel" = they obeyed

**Greek emphatic (ou me):**
- Luke 1:15 "he must never drink" - emphatic prohibition
- Luke 10:19 "nothing will harm you at all" - emphatic assurance

**Other negative + negative verb:**
- Romans 4:20 "did not waver in unbelief" = remained believing
- Mark 6:26 "did not want to refuse her" = had to allow
- Job 5:17 "do not despise" = appreciate

**Not + without:**
- Mark 6:4 "is not without honor" = is honored
- Hebrews 7:20 "not without swearing an oath" = with an oath
- Hebrews 9:7 "not without blood" = always with blood

**Two negatives in clause:**
- Luke 9:36 "told no one anything" - emphatic silence
- Romans 13:8 "owe nothing to no one" = pay all debts
- Exodus 12:30 "not a house where there was not someone dead" = every house had death
