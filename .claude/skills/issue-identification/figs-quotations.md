# figs-quotations

## Purpose
Identify places where the translator might benefit from converting between direct and indirect quotations.

## Definition
Direct and indirect quotations are two ways of reporting what someone said:

- **Direct quotation**: Reports words from the original speaker's viewpoint, using their exact words. Usually marked with quotation marks.
  - John said, "**I** do not know when **I** will arrive."

- **Indirect quotation**: Reports words from the reporter's viewpoint, with pronoun/tense changes. No quotation marks.
  - John said that **he** did not know when **he** would arrive.

Key characteristics:
- Direct quotes preserve the original speaker's perspective (pronouns, tense, deixis)
- Indirect quotes shift to the narrator's perspective
- Some languages prefer one form over the other in certain contexts
- Hebrew and Greek texts may use forms that don't translate naturally into the target language

---

## When to Use figs-quotations

Use this issue when:
1. An **indirect quotation in the source** might be more natural as a direct quotation in translation
2. A **direct quotation in the source** might be more natural as an indirect quotation in translation
3. The quotation structure in the source text creates awkwardness in translation

### Common Patterns Requiring figs-quotations Notes

| Pattern | Example | Suggested Direction |
|---------|---------|---------------------|
| Infinitive clauses reporting speech | "commanded him to tell no one" | Indirect -> Direct |
| Brief embedded commands | "he commanded them, telling this to no one" | Indirect -> Direct |
| Purpose/content clauses after speech verbs | "begged him that he might be with him" | Indirect -> Direct |
| Short simple quotes | "they were saying, 'He is out of his mind'" | Direct -> Indirect |
| Interrogative clauses | "asked when the kingdom was coming" | Either direction |

---

## Confirmed Classifications from Issues Resolved

| Pattern | Decision | Notes |
|---------|----------|-------|
| "answered and said" | Use writing-quotations | "and said" is a quote margin, not figs-quotations |
| "saying" as quote introducer | Use writing-quotations | Standard quote margin |
| Direct speech without quote margin | Use writing-quotations | Suggest adding speech identifier |
| "Thus says Yahweh" ... "For Yahweh has spoken" | Use writing-quotations | Concluding quote margin |

### Special Case: "Answered and Said"

This is a common Hebrew construction that requires **writing-quotations**, NOT figs-quotations:

- **"and said"** is viewed as a quote margin (speech tag) comparable to "saying"
- Put discussion in **book intro**; first instance in each book refers back to intro
- First instance in subsequent chapters refers back to first instance or book intro

**When "answered" responds to a situation** (not to something someone said):
- Still use **writing-quotations** for "and said"
- Write a separate **figs-explicit** note explaining the situation response
- Example note: "The elders are responding to a situation, not something that someone said here. You could say that explicitly if that would be helpful to your readers. Alternate translation: [and they shall say in response to the murder situation]"

---

## NOT figs-quotations (Use These Instead)

### Use writing-quotations for:
| Expression | Reason |
|------------|--------|
| Quote margins ("saying," "and said") | These introduce quotes, not quote structure |
| Missing speech identifiers | Missing quote margin, not quote type |
| Prophetic message frames | "Thus says Yahweh" is a speech tag |

### Use figs-quotesinquotes for:
| Expression | Reason |
|------------|--------|
| Multiple nested quote levels | Nested quotes are a distinct issue |
| Embedded quotes causing confusion | Focus is on layers, not direct/indirect |

### Use figs-quotemarks for:
| Expression | Reason |
|------------|--------|
| Marking quotation boundaries | About punctuation, not structure |
| Scripture citations | Indicating where quotes begin/end |

---

## Recognition Process

1. **Identify speech reports**: Look for verbs of speaking (said, commanded, asked, told, begged, etc.) followed by reported content.

2. **Determine current quote type**:
   - Direct: Original pronouns preserved ("I," "you" referring to original speaker/hearer)
   - Indirect: Pronouns shifted to narrator's perspective ("he," "they")

3. **Check for naturalness issues**:
   - Does the current form create awkward phrasing?
   - Would the other form be clearer for readers?
   - Is there a pattern in the book that should be consistent?

4. **Apply the decision**:

   | Signal | Likely Direction |
   |--------|------------------|
   | Infinitive after command/ask verb | Convert to direct |
   | "that" clause after speech verb | Could go either way |
   | Very short embedded quote | May be more natural as indirect |
   | Long complex quote | Usually keep as direct |

---

## Common Triggers for figs-quotations

### Indirect to Direct (most common direction in notes)

These Hebrew/Greek patterns often benefit from direct quotation in translation:

1. **Infinitive commands**: "commanded him to tell no one" -> "commanded him, 'Tell this to no one'"
2. **Purpose clauses**: "begged that he might be with him" -> "begged, 'Let me be with you'"
3. **Content clauses**: "asking about the parables" -> "asking, 'Please explain the parables'"
4. **Reported questions**: "asked whether it was lawful" -> "asked, 'Is it lawful?'"

### Direct to Indirect (less common)

These patterns may work better as indirect quotations:

1. **Very brief quotes**: "saying, 'We never saw thus'" -> "saying that they had never seen such things"
2. **Repetitive quotes**: Multiple short quotes in sequence
3. **Cultural awkwardness**: When direct address creates problems

---

## Relationship to Other Quote Issues

| Issue | Focus | When to Use |
|-------|-------|-------------|
| **figs-quotations** | Quote TYPE (direct vs indirect) | Converting between direct/indirect |
| **figs-quotesinquotes** | Quote NESTING (layers) | Reducing nested quotes |
| **figs-quotemarks** | Quote MARKING (punctuation) | Indicating quote boundaries |
| [writing-quotations](writing-quotations.md) | Quote INTRODUCTION (margins) | "Saying," "answered and said," missing margins |

---

