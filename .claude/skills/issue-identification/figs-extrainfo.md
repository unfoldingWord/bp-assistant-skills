# figs-extrainfo

## Purpose
Identify when the author intentionally left information vague or unclear, and translators should NOT make it explicit.

## Definition
Sometimes it is better NOT to state assumed knowledge or implicit information explicitly. This happens when:
- The speaker/author intentionally left something unclear
- The original audience did not understand what was meant
- Making it explicit would spoil the literary/theological effect
- The explanation comes later in the text

This is fundamentally different from figs-explicit: here we **preserve** the ambiguity rather than resolve it.

## Key Differentiator: Direction of Information Flow
- **figs-explicit**: Implicit -> Explicit (ADD information for reader comprehension)
- **figs-explicitinfo**: Explicit -> Implicit (REMOVE redundant information)
- **figs-extrainfo**: Keep Implicit (DON'T add information; preserve authorial intent)

## Confirmed Classifications (from Issues Resolved)

### IS figs-extrainfo:
1. **"his anointed" in Psalms** - when David uses expressions that refer to himself AND to future kings including the Messiah, do NOT narrow it to just "me, his anointed" (Oct 15, 2025)
2. **Intentionally vague references** - when the author deliberately doesn't specify
3. **Information explained later** - don't explain now what the text will explain soon
4. **Characters who don't understand** - if characters in the narrative are confused, don't make it clear to readers
5. **Riddles and mysteries** - preserve the puzzle

### NOT figs-extrainfo (use these instead):
- **Reader lacks background knowledge original audience had** -> figs-explicit
- **Text has redundant/extra wording** -> figs-explicitinfo
- **Clear meaning that author stated indirectly** -> figs-explicit

## Categories/Subtypes

### 1. Intentionally Vague References
Author deliberately doesn't specify who/what:
- "I hear" - Paul doesn't say from whom (to avoid conflict)
- "the remaining things" - Paul intentionally vague about what these are
- "the brothers" - no information about who they are
- "this punishment" - both Paul and Corinthians knew but we don't

**Pattern**: Author uses general terms when he could have been specific.

**Key marker**: "does not clarify," "does not state," "intentionally uses vague language"

### 2. Information Explained Later
The text will explain this soon - don't spoil it:
- Jesus' metaphors before he explains them ("living water," "bread of life," "yeast")
- Actions whose purpose is stated in the next verse
- References that will be clarified in following context

**Pattern**: "Since the story/text indicates in the next verse..." or "Jesus does not explain the metaphor to them in this verse"

**Key marker**: Note refers to upcoming explanation in text

### 3. Characters Who Don't Understand
Original audience/characters were confused - readers should experience same:
- Disciples not understanding "yeast of the Pharisees" (until Matt 16:11-12)
- Nicodemus not understanding "born again" (until Jesus explains)
- Crowd not understanding "true bread from heaven" (until v. 35)
- Jews not understanding "eating my flesh and drinking my blood"

**Pattern**: "However, the [character/audience] did not understand this. Therefore, you do not need to explain its meaning further here."

### 4. Riddles and Mysteries
Purposely obscure for literary effect:
- Samson's riddle about the lion and honey
- Prophetic visions meant to be mysterious

**Pattern**: "The author purposely said this in a way that would be hard to understand."

### 5. Ambiguity Preserving Multiple Meanings
The ambiguity itself is meaningful:
- "his anointed" - David AND future kings AND Messiah
- Phrases that apply to multiple referents intentionally
- Theological richness in open interpretation

**Pattern from Issues Resolved**: "when David uses an expression such as 'his anointed' that refers to himself and to future kings, including the Messiah, we can write a figs-extrainfo note recommending that translators not represent this as 'me, his anointed.'"

### 6. Narrative Suspense
Information withheld to maintain story tension:
- "stayed" - reason (exhaustion) given in next verse
- Actions whose purpose becomes clear through context
- Details that would spoil the narrative

**Pattern**: "Since the story indicates [in the next verse/later] the reason/purpose..."

## Recognition Process

```
START: Is there something in the text that could be made clearer?
  |
  +--NO--> Not figs-extrainfo (or any explicit-related issue)
  |
  +--YES--> Did the ORIGINAL AUDIENCE understand it?
              |
              +--YES (and modern readers won't)--> figs-explicit (add info)
              |
              +--NO (original audience also confused/meant to be)-->
                    |
                    Did the author INTEND the ambiguity?
                    |
                    +--YES--> figs-extrainfo (preserve ambiguity)
                    |
                    +--NOT SURE--> Check: Is meaning explained later in text?
                                   |
                                   +--YES--> figs-extrainfo
                                   |
                                   +--NO--> Consider figs-explicit
```

## Key Test Questions

1. **Did the author have a reason to be vague?** (Yes = likely figs-extrainfo)
2. **Were the original characters/audience also confused?** (Yes = figs-extrainfo)
3. **Is the meaning explained later in the text?** (Yes = figs-extrainfo - don't spoil it)
4. **Would making it explicit narrow the meaning inappropriately?** (Yes = figs-extrainfo)
5. **Is this a riddle, mystery, or intentional puzzle?** (Yes = figs-extrainfo)
6. **Would the original audience have understood but modern readers won't?** (Yes = figs-explicit, NOT figs-extrainfo)

## Common Patterns in Examples

### Vague References (Preserve)
| Text | Note Pattern |
|------|--------------|
| "I hear" | Paul does not state from whom |
| "the remaining things" | Paul does not clarify what these are |
| "these things" | Could refer to several sections; keep general |
| "the brothers" | Paul provides no information about who they are |

### Explained Later (Don't Spoil)
| Text | Note Pattern |
|------|--------------|
| "living water" | Jesus doesn't explain the metaphor here; John explains in next verse |
| "true bread from heaven" | Jesus doesn't tell them plainly until verse 35 |
| "born again" | Nicodemus doesn't understand; Jesus explains later |
| "stayed" | Reason given in next verse |

### Multiple Valid Meanings (Preserve Richness)
| Text | Note Pattern |
|------|--------------|
| "his anointed" | Refers to David AND future kings AND Messiah |
| "all" | Could mean all humans or all believers; keep ambiguous |
| "spirit" | Could be Paul's spirit or Holy Spirit; keep open |

### Character Confusion (Match Reader Experience)
| Text | Note Pattern |
|------|--------------|
| "yeast of the Pharisees" | Disciples didn't understand; readers shouldn't either yet |
| "eating my flesh" | Jews didn't understand; don't explain here |
| "I go away" | Jews didn't understand Jesus meant death/heaven |

## Critical Distinction from figs-explicit

| Aspect | figs-explicit | figs-extrainfo |
|--------|--------------|----------------|
| Original audience | Understood | Did NOT understand (or ambiguity intended) |
| Author's intent | Expected understanding | Intended vagueness |
| Action | ADD information | DON'T add information |
| Goal | Reader comprehension | Preserve authorial intent |
| Test | Would original readers know? | Did author want it unclear? |

## Warning Signs: Probably figs-extrainfo

- Note says "does not clarify" or "does not specify"
- Note says "preserve the ambiguity"
- Note says "explained in the next verse"
- Note says "did not understand"
- Note says "you do not need to explain"
- Text is a riddle, parable, or mystery
- Multiple interpretations are theologically valid
- Characters in narrative are confused

## Warning Signs: Probably NOT figs-extrainfo

- Original audience would have understood
- Modern readers lack cultural/historical background
- Meaning is clear but unstated for brevity
- Text has redundant wording to remove (figs-explicitinfo)

## Relationship to Other Issues

| If you see... | Use... | Because... |
|---------------|--------|------------|
| Original audience understood, modern won't | figs-explicit | ADD missing background |
| Text has redundant wording | figs-explicitinfo | REMOVE extra info |
| Author intentionally vague | figs-extrainfo | PRESERVE ambiguity |
| Meaning explained later in text | figs-extrainfo | Don't spoil the revelation |
| Characters in story confused | figs-extrainfo | Readers should experience same |
| Multiple meanings all valid | figs-extrainfo | Preserve theological richness |
