# ULT Alignment Rules

Detailed rules for aligning English ULT text with Hebrew source.

## Core Principles

### Precision Over Breadth

The goal is to align at the smallest meaningful unit. This maximizes usefulness for:
- Translation checking
- Word-level analysis
- Vocabulary lookup

### One-to-Many is Normal

A single Hebrew word often maps to multiple English words:
- בְּ⁠רֵאשִׁ֖ית → "In the beginning" (3 English words)
- הַ⁠מֶּ֫לֶךְ → "the king" (2 English words)

### Many-to-One is Rare but Valid

Multiple Hebrew words may map to one English phrase when:
- Direct object marker + noun: אֵת הָ⁠אָ֫רֶץ → "the earth"
- Compound expressions

## Word Type Rules

### Articles

Hebrew definite article (הַ prefix) and English articles align with their head noun:

| Hebrew | English | Alignment |
|--------|---------|-----------|
| הַ⁠מֶּ֫לֶךְ | the king | `[heb_idx]` → `["the", "king"]` |
| מֶ֫לֶךְ | a king | `[heb_idx]` → `["a", "king"]` |

Never align "the" separately from its noun.

### Prepositions

Prefixed prepositions (בְּ, לְ, מִן, etc.) align with their English equivalent plus governed noun:

| Hebrew | English | Alignment |
|--------|---------|-----------|
| בְּ⁠בַ֫יִת | in the house | `[heb_idx]` → `["in", "the", "house"]` |
| לַ⁠מֶּ֫לֶךְ | to the king | `[heb_idx]` → `["to", "the", "king"]` |

### Conjunctions

Prefixed waw (וְ, וַ) typically aligns separately:

| Hebrew | English | Alignment |
|--------|---------|-----------|
| וְ⁠הָ⁠אָ֫רֶץ | And the earth | `[waw_idx]` → `["And"]`; `[aretz_idx]` → `["the", "earth"]` |

But when waw is integral to the word form (wayyiqtol), it may align with the verb:

| Hebrew | English | Alignment |
|--------|---------|-----------|
| וַ⁠יֹּ֫אמֶר | Then ... said | `[heb_idx]` → `["Then"]` and `["said"]` (split) |

### Direct Object Marker (אֵת)

The untranslatable אֵת aligns with its following noun:

| Hebrew | English | Alignment |
|--------|---------|-----------|
| אֵת הַ⁠שָּׁמַ֫יִם | the heavens | `[et_idx, shamayim_idx]` → `["the", "heavens"]` |

### Pronouns

Suffixed pronouns align with the English pronoun:

| Hebrew | English | Alignment |
|--------|---------|-----------|
| דְּבָרוֹ | his word | `[heb_idx]` → `["his", "word"]` |
| עִמָּ֫נוּ | with us | `[heb_idx]` → `["with", "us"]` |

Independent pronouns align directly:

| Hebrew | English | Alignment |
|--------|---------|-----------|
| הוּא | he | `[heb_idx]` → `["he"]` |
| אֲנִי | I | `[heb_idx]` → `["I"]` |

### Verbs

Hebrew verbs align with English verb forms, including auxiliaries:

| Hebrew | English | Alignment |
|--------|---------|-----------|
| יִשְׁמֹר | he will guard | `[heb_idx]` → `["he", "will", "guard"]` |
| שָׁמַר | he guarded | `[heb_idx]` → `["he", "guarded"]` |

When subject is separate, only verb aligns to verb:

| Hebrew | English | Alignment |
|--------|---------|-----------|
| יהוה יִשְׁמֹר | Yahweh will guard | `[yhwh_idx]` → `["Yahweh"]`; `[verb_idx]` → `["will", "guard"]` |

When Hebrew uses an independent pronoun for emphasis alongside a verb that also encodes the subject, and English renders both pronouns, split them:
- The emphatic pronoun aligns to the Hebrew pronoun word
- The verb's subject aligns to the Hebrew verb

| Hebrew | English | Alignment |
|--------|---------|-----------|
| אַתָּה הוֹרֵתָנִי | you, you have taught me | `[pronoun_idx]` → `["you,"]`; `[verb_idx]` → `["you", "have", "taught", "me"]` |

The first "you" is the emphatic pronoun; the second "you" is the verb's implied subject.

### Participles

Participles often need a be-verb in English:

| Hebrew | English | Alignment |
|--------|---------|-----------|
| שֹׁמֵר | is guarding | `[heb_idx]` → `["is", "guarding"]` |

### Infinitives

Infinitive construct aligns with "to" + verb:

| Hebrew | English | Alignment |
|--------|---------|-----------|
| לִשְׁמֹר | to guard | `[heb_idx]` → `["to", "guard"]` |

Infinitive absolute with finite verb (emphatic doubling):

| Hebrew | English | Alignment |
|--------|---------|-----------|
| שָׁמוֹר יִשְׁמֹר | guarding he will guard | `[inf_idx]` → `["guarding"]`; `[finite_idx]` → `["he", "will", "guard"]` |

## Grammatical Additions (Bracketed Words)

Words in {brackets} in ULT are English additions for grammar. These align to the nearest Hebrew word (before or after) that they support:

| Hebrew Context | ULT Text | Alignment Strategy |
|----------------|----------|-------------------|
| טוֹב (adjective) | God {is} good | `[tov_idx]` → `["{is}", "good"]` |
| בֹּקֶר (morning) | {it was} morning | `[boqer_idx]` → `["{it}", "{was}", "morning"]` |

The bracketed word attaches to whichever Hebrew word it grammatically supports - usually the predicate or the word it enables in English.

Note: Keep brackets in the English word array to indicate they are additions.

### Implied Subjects

When Hebrew verb implies subject but ULT makes it explicit:

| Hebrew | English | Alignment |
|--------|---------|-----------|
| אָמַר | he said | `[heb_idx]` → `["he", "said"]` |

The "he" is not bracketed because it's encoded in the Hebrew verb form.

## Construct Chains

### How Hebrew Construct Works

In Biblical Hebrew, a construct phrase (e.g., *sēfer ha-tôrāh* — "the book of the law") expresses a genitive relationship through **morphological linking**, not through a separate preposition. There is no Hebrew word for "of" — the English word "of" is supplied by the translator to render the construct relationship. Because "of" comes from the construct *form* of the **first noun** (the nomen regens / head noun), it MUST align to that first noun.

### Required: Split Strategy

For two-word constructs, each word MUST be its own alignment entry:

| Hebrew | English | Alignment |
|--------|---------|-----------|
| בֵּית הַמֶּ֫לֶךְ | house of the king | `[bayit_idx]` → `["house", "of"]`; `[melek_idx]` → `["the", "king"]` |
| דְּבַר יהוה | word of Yahweh | `[davar_idx]` → `["word", "of"]`; `[yhwh_idx]` → `["Yahweh"]` |
| סֵ֫פֶר הַתּוֹרָה | the book of the law | `[sefer_idx]` → `["the", "book", "of"]`; `[torah_idx]` → `["the", "law"]` |

The "of" goes with the **first word** (nomen regens / head noun / construct form) since it represents the construct relationship expressed by that word's morphology.

### NEVER Do This

| Wrong | Why |
|-------|-----|
| `[head_idx]` → `["house"]`; `[dep_idx]` → `["of", "the", "king"]` | "of" aligned to second (dependent) noun — WRONG |
| `[head_idx]` → `["house"]`; `[dep_idx]` → `["the", "king"]`; "of" unaligned | "of" left unaligned — WRONG |
| `[head_idx, dep_idx]` → `["house", "of", "the", "king"]` | entire chain collapsed — WRONG |

### Complex Constructs

Three+ word chains: split at each word boundary, attaching "of" to the **preceding** construct noun (not to the following noun):

| Hebrew | English | Alignment |
|--------|---------|-----------|
| דְּבַר בֵּית יהוה | word of the house of Yahweh | `[davar_idx]` → `["word", "of"]`; `[bayit_idx]` → `["the", "house", "of"]`; `[yhwh_idx]` → `["Yahweh"]` |

Each interior noun gets "of" appended because it is itself a construct form governing the next noun. Only the final (absolute) noun in the chain has no "of".

## Occurrence Tracking

When a word appears multiple times in a verse, the conversion script handles x-occurrence and x-occurrences attributes automatically. The mapping JSON does not need to track this.

## Edge Cases

### Untranslated Hebrew

Some Hebrew words have no English equivalent (e.g., certain particles). Options:
1. Align to nearest semantically related English word
2. Merge with following Hebrew word's alignment

### Split Alignments

A single Hebrew word may need to align to non-contiguous English words:

Hebrew: וַיֹּ֫אמֶר (wayyiqtol "and he said")
ULT: "Then God said"

This becomes:
```json
{"hebrew_indices": [wayyomer_idx], "english": ["Then"]},
{"hebrew_indices": [elohim_idx], "english": ["God"]},
{"hebrew_indices": [wayyomer_idx], "english": ["said"]}
```

Note: The same Hebrew index can appear in multiple alignments when the Hebrew word maps to non-contiguous English.

### Poetry and Parallelism

In poetry, the same concept may be expressed twice. Align each Hebrew word to its corresponding English word in that line, even if the meaning is parallel.

## Verification Checklist

1. **Coverage**: Every Hebrew word index appears somewhere
2. **Completeness**: Every English word appears exactly once
3. **No orphans**: No alignment has empty english array
4. **Articles attached**: "the", "a" never standalone
5. **Brackets attached**: {added} words align to supporting Hebrew word
6. **Order correct**: Alignments follow English word order
7. **Constructs split**: Each word in construct chain aligned separately; English "of" is with the first (head) noun, never with the second noun and never unaligned
