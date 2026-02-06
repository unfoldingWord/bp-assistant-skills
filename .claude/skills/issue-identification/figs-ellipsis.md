# figs-ellipsis

## Purpose
Identify when a speaker or writer intentionally leaves out words that would normally be needed for a grammatically complete sentence, expecting the reader to supply them from context.

## Definition
An **ellipsis** occurs when words are omitted that the hearer/reader is expected to fill in mentally. Two types:
1. **Relative Ellipsis**: Omitted words can be supplied from the immediate context (usually the preceding clause)
2. **Absolute Ellipsis**: Omitted words must be supplied from common usage or cultural expectations (not stated in context)

## Ellipsis and Parallelism

In Hebrew poetry, ellipsis and parallelism frequently co-occur. The second line of a parallel structure often omits words from the first line:

| Example (Psalm 114) | Omitted |
|---------------------|---------|
| "The mountains skipped like rams, the hills like sons of the flock" | "skipped" |
| "What is to you, sea, that you flee? Jordan, you turn backwards?" | "What is to you...that" |

When identifying parallelism, also check whether the second line omits words the reader must supply.

## Key Recognition Patterns

### Relative Ellipsis (Most Common)
Parallel clauses where second clause omits repeated elements:

| Example | Omitted Words |
|---------|---------------|
| "He makes Lebanon skip like a calf **and Sirion like a young ox**" | "he makes" and "skip" |
| "not as unwise **but as wise**" | "walk" |
| "in the judgment... **nor sinners in the assembly**" | "will stand" |
| "one bearing 30, **and one 60, and one 100**" | "bearing" |
| "wiser than **men**" | "the wisdom of" |

### Absolute Ellipsis
Culturally expected completions:

| Type | Example | Omitted Words |
|------|---------|---------------|
| Greetings/Blessings | "Grace and peace" | "May you receive" |
| Short Answers | "In Bethlehem" | "He is born" |
| Polite Responses | "that I might recover my sight" | "I want you to heal me so" |
| Oath Confirmations | "In peace" | "Yes, I have come" |

### Common Incomplete Patterns

**Missing Subject/Verb from Previous Clause:**
- "Great in every way" - needs "The advantage is great..."
- "also Naphtali on the heights" - needs "and the people of Naphtali were also..."

**Missing Comparison Elements:**
- "wiser than men" - needs "than the wisdom of men"
- "stronger than men" - needs "than the strength of men"

**Missing Conditional Words:**
- "if you incline your heart" - continuing condition from earlier "if"
- "But if not" - needs "if you are not doing X"

**Lists with Abbreviated Entries:**
- "Ben Hur, in the hill country" - needs "was the governor"
- "eating and drinking and rejoicing" - needs "They were"

**Answers Without Full Sentences:**
- "Five, and two fish" - needs "We have five loaves"
- "Seven" - needs "We have seven loaves"
- "A prophet" - needs "He is a prophet"

## NOT Ellipsis

### Words Supplied in English (Already in Text)
If words appear in the ULT (even in brackets/braces), this is NOT ellipsis:
- "Who {are} you" - verb supplied, NOT ellipsis
- "Grace {be} with you" - verb supplied, NOT ellipsis

Ellipsis is ONLY for words the reader must supply that are NOT in the text.

This applies when checking for ellipsis alongside parallelism: if the second/third line of a parallel structure omits a word, but the ULT already supplies it in `{}` braces, do not flag it as ellipsis.

### Hebrew Carrying Forward (ULT handles these)
Per Issues Resolved (Jan 8, 2025): "ULT should supply Hebrew conditionals and negatives that carry forward from previous clauses. ULT does not fill in ellipses, but while these seem to be ellipses in English, they are actually not in Hebrew."

### Other Issues to Consider
- **figs-parallelism**: If two clauses repeat the same idea for emphasis, use parallelism even if words are technically omitted
- **translate-blessing**: Blessing formulas like "Grace and peace" - use translate-blessing for the blessing aspect
- **figs-quotations**: Missing quote margins handled by writing-quotations

## Recognition Process

```
Is a sentence/clause grammatically incomplete?
  |
  No --> Not ellipsis
  |
  Yes --> Can missing words be supplied from context?
            |
            +-- From immediately preceding clause?
            |     --> Relative ellipsis (most common)
            |
            +-- From cultural/common expression patterns?
            |     --> Absolute ellipsis
            |
            +-- Words would be supplied in Hebrew but English omits?
                  --> Check if ULT already supplies them
                      (Hebrew conditionals/negatives - NOT ellipsis)
```

## Typical Contexts

| Context | Pattern |
|---------|---------|
| Poetry/Parallelism | Second line omits repeated elements from first |
| Lists | Items after first omit common verb/context |
| Dialogue | Short answers omit full sentence structure |
| Comparisons | "than X" omits full comparison element |
| Conditional Chains | Later conditions omit "if" from earlier |