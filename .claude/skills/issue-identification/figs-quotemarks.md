# figs-quotemarks

## Purpose
Identify places where translators may need guidance on using quotation marks or other punctuation/conventions to mark quotation boundaries.

## Definition
**Quote markings** are punctuation or other conventions that languages use to indicate where quotations begin and end. Different languages use different systems:

- English uses " " for first level, ' ' for second level
- Some languages use other marks: " " , ' , " " , << >> , -- , etc.
- Some languages use no marks but rely on verb forms or particles
- Alternating marks help readers track nested quotation levels

Key characteristics:
- Quotation marks are NOT used with indirect quotes
- Alternating mark styles help distinguish nested layers
- The ULT uses standard English convention (double, then single, then double...)
- Translators need to use their own language's conventions

---

## When to Use figs-quotemarks

Use this issue when:
1. A quotation begins and translators need to **mark its start**
2. A quotation ends and translators need to **mark its end** (especially in long quotes)
3. A **Scripture citation** is being quoted (often important to distinguish)
4. Multiple **quotation levels** need different marking styles
5. The quotation has an **unusual structure** that may confuse readers

### Common Situations Requiring figs-quotemarks Notes

| Situation | Why a Note Helps |
|-----------|------------------|
| Long speech beginning | Translators need to know where to place opening mark |
| Scripture quotations | Important to distinguish from surrounding text |
| Multiple speakers in dialogue | Helps readers track who is speaking |
| Nested quotes (3+ levels) | Need guidance on marking system |
| Quote spanning multiple verses | Remind where quote continues/ends |

---

## Quotation Mark Conventions

### Standard English System (ULT follows this)
- **Level 1**: "double quotes"
- **Level 2**: 'single quotes'
- **Level 3**: "double quotes" again
- **Level 4**: 'single quotes' again

### Other Common Systems
- French: << guillemets >>
- German: ,,low opening" "high closing"
- Some Asian languages: corner brackets
- Some languages: no marks, use verbal affixes instead

---

## Recognition Process

1. **Identify the quotation structure**:
   - Is this a first-level quote or embedded quote?
   - How many levels deep is this quotation?
   - Is this the beginning, middle, or end of a quote?

2. **Check for special situations**:
   - Is this a Scripture citation?
   - Is this a long speech spanning multiple verses?
   - Is there potential confusion about quote boundaries?

3. **Determine note need**:

   | Situation | Note Type |
   |-----------|-----------|
   | First-level quote, simple | Usually no note needed |
   | Scripture citation | Note about marking the quoted text |
   | Third+ level quotation | Note about marking levels |
   | End of long speech | Note to mark ending if helpful |
   | Psalm or poetry quotation | Special formatting may help |

---

## Common Patterns in Biblical Text

### Scripture Citations (NT quoting OT)

When NT writers quote Scripture:
- Mark the citation clearly to distinguish from commentary
- May use special formatting (indentation, block quote)
- Help translators identify where the quote ends

Examples:
- "It is written, 'Man shall not live by bread alone'"
- "This is what the prophet said, 'A virgin shall conceive...'"

### Long Speeches

When a speech extends over many verses:
- Opening mark at the beginning
- Some languages re-mark at paragraph breaks
- Closing mark at the very end

### Dialogue Exchanges

When multiple people speak in quick succession:
- Each speaker's words need clear marking
- Helps readers track who is saying what

---

## NOT figs-quotemarks (Use These Instead)

### Use figs-quotations for:
| Situation | Reason |
|-----------|--------|
| Converting direct to indirect | About quote type, not marking |
| Converting indirect to direct | About quote type, not marking |

### Use figs-quotesinquotes for:
| Situation | Reason |
|-----------|--------|
| Simplifying nested quotes | About reducing levels, not marking |
| Pronoun confusion in layers | About structure, not punctuation |

### Use writing-quotations for:
| Situation | Reason |
|-----------|--------|
| Adding "he said" speech margins | About quote introduction |
| Missing quote introducers | About speech identifiers |

---

## Confirmed Decisions from Issues Resolved

| Decision | Notes |
|----------|-------|
| Use alternating double/single marks | Standard English convention in ULT |
| Direct speech without quote margin gets quotation marks in ULT | Then use writing-quotations note |
| Indented block quotes for long quotations | Alternative to marks for major quotes |

---

## Relationship to Other Quote Issues

| Issue | Focus | When to Use |
|-------|-------|-------------|
| **figs-quotations** | Quote TYPE (direct vs indirect) | Converting between types |
| **figs-quotesinquotes** | Quote NESTING (layers) | Simplifying nested quotes |
| **figs-quotemarks** | Quote MARKING (punctuation) | Indicating where quotes are |
| [writing-quotations](writing-quotations.md) | Quote INTRODUCTION (margins) | "Saying," "answered and said," missing margins |

---

## Critical Distinctions

### figs-quotemarks vs figs-quotesinquotes

- **figs-quotemarks**: "Use punctuation to mark this quotation"
- **figs-quotesinquotes**: "Simplify by converting inner quote to indirect"

Both may apply to the same passage:
1. First, decide if quotes should be simplified (figs-quotesinquotes)
2. Then, advise on marking the resulting quotes (figs-quotemarks)

### When BOTH Notes Are Needed

For complex nested quotations (3+ levels):
1. **figs-quotesinquotes note**: Suggest reducing levels by making some indirect
2. **figs-quotemarks note**: Guide on marking the remaining direct quotes

---

