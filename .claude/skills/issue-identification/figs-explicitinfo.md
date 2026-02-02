# figs-explicitinfo

## Purpose
Identify when the source text contains redundant or extra information that would sound unnatural if translated directly, allowing translators to shorten or simplify the expression.

## Definition
Some languages say things explicitly that other languages would leave implicit. When translating, if the explicit information from the source language sounds foreign, unnatural, or unintelligent in the target language, it is best to leave that information implicit.

This is the **OPPOSITE** of figs-explicit: here we REMOVE information rather than ADD it.

## Key Differentiator: Direction of Information Flow
- **figs-explicit**: Implicit -> Explicit (ADD information for reader comprehension)
- **figs-explicitinfo**: Explicit -> Implicit (REMOVE redundant information for natural expression)
- **figs-extrainfo**: Keep Implicit (DON'T add information; author was intentionally vague)

## Confirmed Classifications (from Issues Resolved)

### IS figs-explicitinfo:
1. **"the gods that you have chosen upon them"** - can be shortened if more natural
2. **Redundant demonstratives**: "this, that" -> just "that"
3. **Travel marked for elevation** when elevation is not significant:
   - "went up" / "went down" / "came up" -> just "went" / "came"
4. **"called its name X"** -> "called it X" or "named it X"
5. **"burned it with fire"** -> "burned it" (fire is implicit in burning)
6. **"answered and said"** -> "answered" (speaking is implicit in answering)
7. **"he opened his mouth and taught"** -> "he began to teach"
8. **"kneeling on his knees"** -> "kneeling down"
9. **"stoned him with stones"** -> "stoned him"
10. **Redundant parallel phrases**: "has been hidden in a mystery" -> "has been hidden" OR "is a mystery"

### NOT figs-explicitinfo (use these instead):
- **Reader lacks background knowledge** -> figs-explicit
- **Author intentionally vague** -> figs-extrainfo
- **Poetic repetition for effect** -> writing-poetry or figs-parallelism
- **Emphatic repetition** -> may be intentional (check context)

## Categories/Subtypes

### 1. Redundant Action-Instrument Pairs
Action already implies the instrument:
- "burn with fire" -> "burn"
- "stone with stones" -> "stone"
- "cut with a sword" -> "cut"

**Pattern**: Action verbs that inherently involve a specific instrument.

### 2. Redundant Verb-Speech Pairs
One verb implies the other:
- "answered and said" -> "answered" or "said"
- "opened his mouth and taught" -> "began to teach" or "taught"

**Pattern**: Two verbs of speaking where one implies the other.

### 3. Redundant Body Part References
Body part is implicit in the action:
- "kneeling on his knees" -> "kneeling down"
- "saw with his eyes" -> "saw"
- "heard with his ears" -> "heard"
- "play by his hand" -> "strum" or "play"

**Pattern**: Actions already associated with specific body parts.

### 4. Redundant Demonstratives/Pronouns
Extra referential words:
- "this, that" -> "that"
- "where X was there" -> "where X was"
- "in this manner, as" -> "as"

**Pattern**: Double markers that serve the same function.

### 5. Elevation Markers in Travel
Hebrew marks travel for change in elevation; many languages don't:
- "went up to Jerusalem" -> "went to Jerusalem" (if elevation is not significant)
- "came down from the hill" -> "came from the hill"

**Pattern**: "went up" / "went down" / "came up" / "came down" when elevation is not the point.

**Note**: Some elevation markers are significant and should be kept. Use figs-explicitinfo only when the elevation is conventional rather than meaningful.

### 6. Redundant Naming Formulas
Overly formal naming expressions:
- "called its name X" -> "called it X" or "named it X"
- "my son whom I had borne" -> "my own son" or "the son I had borne"

### 7. Redundant Semantic Overlap
Two phrases that mean the same thing:
- "has been hidden in a mystery" -> one or the other
- "raised / raise up" (same meaning, slight variation) -> use consistently

## Recognition Process

```
START: Does the text contain more words than seem necessary?
  |
  +--NO--> Not figs-explicitinfo
  |
  +--YES--> Is the "extra" information genuinely redundant?
              |
              +--NO (it adds meaning)--> Not figs-explicitinfo
              |
              +--YES--> Would a native speaker find it unnatural?
                        |
                        +--NO--> May not need a note
                        |
                        +--YES--> Is it poetic repetition for effect?
                                  |
                                  +--YES--> writing-poetry or figs-parallelism
                                  |
                                  +--NO--> figs-explicitinfo
```

## Key Test Questions

1. **Does removing this information change the meaning?** (No = likely figs-explicitinfo)
2. **Is the action + instrument pair redundant?** (burn + fire, stone + stones, etc.)
3. **Are there two words serving the same grammatical function?** (this + that, where + there)
4. **Would a native English speaker find this wording strange?** (Yes = figs-explicitinfo)
5. **Is this elevation marking meaningful or conventional?** (Conventional = can be simplified)

## Common Patterns in Examples

### Action-Instrument Redundancy
| Source | Shortened |
|--------|-----------|
| burn it with fire | burn it |
| stone him with stones | stone him |

### Speech Verb Redundancy
| Source | Shortened |
|--------|-----------|
| answered and said | answered |
| opened his mouth and taught | began to teach |

### Body Part Redundancy
| Source | Shortened |
|--------|-----------|
| kneeling on his knees | kneeling down |
| seen with our eyes | whom we saw |
| touched with our hands | whom we touched |

### Demonstrative Redundancy
| Source | Shortened |
|--------|-----------|
| this, that | that |
| where X was there | where X was |
| where he would judge there | where he would judge |

### Elevation Markers
| Source | Shortened |
|--------|-----------|
| went up to | went to |
| came down from | came from |
| went up against | attacked |

### Naming Formulas
| Source | Shortened |
|--------|-----------|
| called its name X | called it X / named it X |
| my son whom I had borne | my own son |

## Relationship to Other Issues

| If you see... | Use... | Because... |
|---------------|--------|------------|
| Reader lacks background info | figs-explicit | Need to ADD information |
| Text has redundant wording | figs-explicitinfo | Can REMOVE information |
| Author was intentionally vague | figs-extrainfo | Keep implicit; don't add |
| Poetic parallelism for effect | writing-poetry | Redundancy is intentional |
| Cognate accusative (dreamed a dream) | writing-poetry | Special Hebrew form |

## Critical Distinction from figs-explicit

| Aspect | figs-explicit | figs-explicitinfo |
|--------|---------------|-------------------|
| Problem | Reader lacks info | Source has extra info |
| Solution | ADD information | REMOVE information |
| Direction | Implicit -> Explicit | Explicit -> Implicit |
| Question | What's missing? | What's redundant? |
