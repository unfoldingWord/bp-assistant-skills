# UST Alignment Rules

Detailed rules for aligning English UST text with Hebrew source.

## Core Principle

UST alignment shows which Hebrew word(s) contribute meaning to each English phrase. The overarching purpose is to show the user from which Hebrew words the English phrases take their meaning.

**Default to the smallest possible alignment unit.** Start with 1-to-1 mappings and expand only when the English rendering genuinely cannot be divided. Granularity is a virtue; large groupings are the exception.

## Granularity Hierarchy

Apply this decision ladder in order — stop at the first level that fits:

1. **1-to-1 (preferred)**: One Hebrew word → one English word or short phrase. Use this whenever a single English word or 2–3-word phrase clearly renders a single Hebrew word.
   ```json
   {"hebrew_indices": [3], "english": ["Yahweh"]},
   {"hebrew_indices": [4], "english": ["remember"]},
   {"hebrew_indices": [5], "english": ["David"]}
   ```

2. **Small N-to-M (acceptable)**: A small group of 2–3 Hebrew words that together produce a 2–6-word English phrase where the words cannot be assigned individually. Example: a construct chain whose English equivalent is "the house of the king."

3. **Large group (last resort)**: Many Hebrew words collapsed into a long English clause. Reserve this **only** for:
   - A large image or idiom with no word-level correspondence (e.g., a simile restructured into a subordinate clause)
   - A parallelism that the UST collapses into a single sentence
   - A rhetorical question restructured as a statement where the entire question maps as a unit
   - A prepositional phrase expanded into a full relative clause where no sub-phrase can be independently assigned

**Never default to large groups.** If you find yourself assigning 4+ Hebrew indices and 8+ English words to one entry, ask: "Can I split this into two or three smaller entries?" If yes, split it.

## Key Differences from ULT Alignment

| Aspect | ULT | UST |
|--------|-----|-----|
| Goal | Word-level precision | Meaning-level mapping |
| English per entry | 1-3 words typical | 1-5 words preferred; larger only when restructuring requires it |
| Hebrew per entry | Usually 1 | Often 3-5 |
| Split alignment | Occasional | Very common |
| Brackets | Grammar additions ({is}, {was}) | Implied information ({when Yahweh}) |
| Empty hebrew_indices | Not used | For purely implied content |
| Restructuring | Minimal | Radical |

## Pattern Catalog

### Preposition Expansion

Hebrew single preposition-noun expands to a full clause.

Hebrew: `בַּ⁠עֲצַ֪ת` + `רְשָׁ֫עִ֥ים` (in-counsel-of + wicked)
UST: "what evil people tell him to do"

```json
{"hebrew_indices": [3, 4, 5, 6], "english": ["does", "not", "do", "what", "evil", "people", "tell", "him", "to", "do,"]}
```

Multiple Hebrew words merged because the UST restructures the entire prepositional phrase into a relative clause.

### Split Alignment

Same Hebrew index appears in multiple entries when meaning maps to non-contiguous English.

Hebrew: `בְּ⁠תוֹרַ֥ת` (in-law-of) -> "in what...teaches"

```json
{"hebrew_indices": [5], "english": ["in", "what"]},
{"hebrew_indices": [6], "english": ["Yahweh"]},
{"hebrew_indices": [5], "english": ["teaches"]}
```

The Hebrew word for "law/teaching" splits into the frame "in what...teaches" with Yahweh inserted between.

### Unaligned Implied Information

Words with no Hebrew correspondent at all.

UST: `{It seems like}` with no Hebrew source

```json
{"hebrew_indices": [], "english": ["{It}", "{seems}", "{like}"]}
```

All words must be bracketed. The validation script enforces this.

### Implied Information Connected to Hebrew

Bracketed words that relate to a specific Hebrew word.

UST: `{when Yahweh} judges {the world}`

```json
{"hebrew_indices": [7], "english": ["{when}", "{Yahweh}"]},
{"hebrew_indices": [7], "english": ["judges"]},
{"hebrew_indices": [7], "english": ["{the}", "{world}"]}
```

Here the Hebrew word for "judgment" expands to "{when Yahweh} judges {the world}" with implied subject and object.

### Verb Expansion

Hebrew single verb expands to a full clause.

Hebrew: `הָלַךְ֮` (walked)
UST: "does not do what...tell him to do"

```json
{"hebrew_indices": [3, 4, 5, 6], "english": ["does", "not", "do", "what", "evil", "people", "tell", "him", "to", "do,"]}
```

The verb gets merged with its modifiers because the UST restructures them as an inseparable unit.

### Rhetorical Question to Statement

Hebrew question restructured as a statement.

Hebrew: `מִי אָדוֹן לָנוּ` (who is lord to us?)
UST: "no one can tell us what we should say"

The entire question maps as a unit, since the rhetorical function is restructured.

### Repeated Reference

Same Hebrew word aligned to two different English renderings when the UST repeats a concept.

Hebrew: `הָ⁠אִ֗ישׁ` (the-man)
UST: "The person who..." and "is the person who..."

```json
{"hebrew_indices": [1], "english": ["The", "person", "who", "will", "have", "a", "truly", "good", "life"]},
{"hebrew_indices": [0], "english": ["is", "the", "person"]}
```

Both entries reference the same concept but in different parts of the UST rendering.

### Mixed Bracketed and Unbracketed

A single alignment group can contain both bracketed and unbracketed words.

```json
{"hebrew_indices": [7], "english": ["{when}", "{Yahweh}"]},
{"hebrew_indices": [7], "english": ["judges"]},
{"hebrew_indices": [7], "english": ["{the}", "{world}"]}
```

Or within one entry:
```json
{"hebrew_indices": [5], "english": ["{his}", "{faithfulness}", "{to}", "{Yahweh}"]}
```

## Word Type Rules

### Names and Proper Nouns

Anchor alignment on these first. Direct 1:1 mapping when possible:

| Hebrew | English | Alignment |
|--------|---------|-----------|
| יהוה | Yahweh | `[yhwh_idx]` -> `["Yahweh"]` |
| דָּוִד | David | `[david_idx]` -> `["David"]` |

### Articles

English articles align with their head noun, same as ULT:

| Hebrew | English | Alignment |
|--------|---------|-----------|
| הָ⁠רְשָׁעִ֑ים | wicked people | `[heb_idx]` -> `["wicked", "people"]` |

### Conjunctions

Prefixed waw often aligns to UST's restructured connector:

| Hebrew | English | Alignment |
|--------|---------|-----------|
| וּ⁠בְ⁠דֶ֣רֶךְ | who does not | Merged with clause it introduces |

### Construct Phrases

"of" aligns with the construct noun, same principle as ULT but groups may be larger:

| Hebrew | English | Alignment |
|--------|---------|-----------|
| בַּ⁠עֲצַ֪ת רְשָׁ֫עִ֥ים | what evil people tell him | Merged as meaning unit |

### Implicit Verbs

When Hebrew has no verb but UST supplies one, align the supplied verb with the predicate:

| Hebrew | English | Alignment |
|--------|---------|-----------|
| (no verb) + רָשָׁע | wicked people are like | `[adj_idx]` -> `["wicked", "people", "are", "like"]` |

### Possessives

Align both parts of a possessive with the Hebrew word:

| Hebrew | English | Alignment |
|--------|---------|-----------|
| חַטָּאִים's | sinful people's behavior | `[heb_idx]` -> `["sinful", "people", "'s", "behavior"]` |

Note: In published UST, apostrophe-s is sometimes split: `\w people\w*'\w s\w*`

## Implied Information Rules

From the GL Guidelines:

1. **Forward alignment only**: Implied information can be aligned with earlier Hebrew words but NOT with later Hebrew words. Information cannot be implied from something that hasn't been stated yet.

2. **Same clause preferred**: Align English words with Hebrew words within the same phrase or clause when possible.

3. **Cross-clause when necessary**: Sometimes UST words must align with Hebrew words much earlier or later in the text due to UST restructuring rules (short sentences, chronological order, etc.).

## Bracket Decision Guide

Brackets are applied by the UST-gen skill. The alignment skill preserves them.

For reference:
- `{word}` in UST text = implied information, not directly in Hebrew
- Unbracketed word = renders Hebrew meaning (even if heavily restructured)
- The alignment skill does NOT add or remove brackets

## What NOT to Do

- **Don't default to large groupings** -- if a Hebrew word maps cleanly to a specific English word or phrase, align it 1-to-1 rather than folding it into a large multi-word entry
- **Don't merge just because words are adjacent** -- adjacency in the Hebrew does not mean they must be grouped; only merge when the English rendering genuinely cannot be divided into smaller pieces
- **Don't treat the UST's meaning-based approach as license to always group** -- the UST is meaning-based, but that does not mean every alignment entry must cover multiple Hebrew words; prefer granularity
- **Don't bracket words that are simply restructured** from Hebrew (restructuring is not the same as implying)
- **Don't split groups that represent a single, inseparable meaning unit** -- if an entire clause renders one Hebrew concept with no divisible sub-parts, keep it together
- **Don't merge groups that represent distinct meaning units** -- if two Hebrew words contribute distinct meanings to different parts of the English, keep them separate
- **Don't leave Hebrew words unaligned** when they have meaning correspondence in the UST -- only leave unaligned if the Hebrew word truly has no representation
- **Don't align implied info with later Hebrew words** -- implied information can only point backward

## Verification Checklist

1. **English completeness**: Every English word appears in exactly one alignment entry
2. **Brackets preserved**: All `{brackets}` from UST-gen carried through
3. **No orphan brackets**: Entries with `hebrew_indices: []` have ALL words bracketed
4. **Split alignment correct**: Same Hebrew index in multiple entries only when meaning is genuinely split
5. **Groups minimal**: No unnecessarily large Hebrew index arrays
6. **Names anchored**: Proper nouns have direct mappings
7. **Forward-only implied**: Implied info aligned with earlier Hebrew, not later
