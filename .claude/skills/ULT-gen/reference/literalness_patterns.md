# Literalness Patterns

Patterns for maximum Hebrew-to-English literalness.

## Word Order Preservation

Preserve Hebrew word order when it reflects emphasis and remains natural in English:

| Hebrew Pattern | Literal ULT | NOT |
|----------------|-------------|-----|
| li gilead | "To me {is} Gilead" | "Gilead {is} mine" |
| habah lanu ezrah | "Give help to us" | "Give us help" |
| attah elohim (fronted) | "You, God, have you not..." | "Have you not, God..." |

When Hebrew fronts an element for emphasis, preserve that fronting.

**Avoid awkward English ("Yoda-speak"):**
Preserve fronting when it adds emphasis, but standard clauses should use English SVO:
- "I called to him with my mouth" (normal clause - use English order)
- NOT: "To him with my mouth I called" (unnatural in English)

Only preserve Hebrew word order when:
- An element is clearly fronted for emphasis
- The English result is grammatically natural

## Niphal Passive Voice

Niphal verbs express passive or reflexive action. Always render them with English passive voice — never convert a Niphal to an English active verb:

| Hebrew Stem | Literal ULT | NOT |
|-------------|-------------|-----|
| Niphal imperfect (passive) | "will be dissipated" | "will vanish" |
| Niphal perfect (passive) | "was reckoned" | "counted" |
| Niphal imperative | "be gathered" | "gather" |
| Niphal participle (passive) | "desolated" | "desolate" |

Render Niphal participles with the verbal passive participial form ("desolated cities"), not a plain adjective ("desolate cities") — the participle preserves the sense of a state brought about by action.

Only use a reflexive English construction (e.g., "hid himself") when the Niphal root is inherently reflexive in meaning. For all passive Niphals, use "be/was/will be [verb]-ed" or the participial "-ed" form as appropriate to the grammatical context.

Some roots are stem-dependent (active in Qal, passive in Niphal) — check `data/quick-ref/ult_decisions.csv` for per-root rulings (e.g. H8074, H4414).

## Active Voice Preservation

Do not convert an active or stative Hebrew form into an English passive just because the passive sounds idiomatic. If the Hebrew stem is active, preserve an active or stative English rendering instead:

- "he will be very high" not "he will be greatly exalted"
- "marveled" not "were appalled"

## Hiphil Causatives

Render Hiphil stems with explicit two-verb causative structure:

| Hebrew | Literal ULT | NOT |
|--------|-------------|-----|
| hirita (Hiphil of ראה) | "made see" | "showed" |
| hishqitanu (Hiphil of שקה) | "made drink" | "gave to drink" |
| hirashta (Hiphil of רעש) | "made tremble" | "shook" |
| hishmia (Hiphil of שמע) | "made hear" / "caused to hear" | "announced" |

## Construct Chains

Preserve as "X of Y" - always show the "of" to mark the construct relationship, even where English idiom would drop it:

| Hebrew | Literal ULT | NOT |
|--------|-------------|-----|
| kol-ha'arets | "all of the earth" | "all the earth" |
| ir matsor | "city of fortification" | "fortified city" |
| sir rachitsi | "tub of my washing" | "my washbasin" |
| yayin tar'elah | "wine of staggering" | "staggering wine" |

**Pronominal suffix placement in construct chains**: when a suffix attaches to the dependent noun, keep it there in English ("the land of your destruction," not "your land of destruction").

**Adjective-noun collapse forbidden**: When Hebrew uses a construct chain where the dependent noun is commonly rendered as an English adjective, keep the genitive "X of Y" form; do not collapse it into "adjective + noun":

| Hebrew | Literal ULT | NOT |
|--------|-------------|-----|
| אוֹת עוֹלָם | "a sign of eternity" | "an everlasting sign" |

The dependent noun remains a genitive noun (see `ult_decisions.csv` H5769 for עוֹלָם).

**Plural construct with repeated noun** (`דּוֹר דּוֹרִים` and similar): preserve both the construct and the plural — "the generation of generations," not "generation {after} generation."

## Literal Verbal Idioms

Keep verb + noun form rather than verb + adverb:

| Hebrew | Literal ULT | NOT |
|--------|-------------|-----|
| asah chayil | "do valor" | "do valiantly" |
| asah tsedaqah | "do righteousness" | "act righteously" |
| dibber shalom | "speak peace" | "speak peacefully" |

## Relative Clauses

Do not turn a Hebrew verbal clause into an English relative clause just because it modifies a noun.

- **Participles** should stay participial: use "-ing" forms, agent nouns, or "the ones/those [verb]-ing" where needed.
- **Indicatives / finite verbs** should stay finite: use a plain English verb without prepending "who/that".

Use a relative clause only when the Hebrew syntax actually requires one. When a yiqtol modifies a noun as a relative verbal clause without an explicit Hebrew relative pronoun, render it participially ("every tongue rising against you"), not as an English relative clause ("every tongue that rises against you") — do not insert "that" when none exists in the Hebrew (see `ult_decisions.csv` H6965).

## Substantive Adjectives

When Hebrew uses an adjective (or Qal stative) as a substantive — with or without the article — render it as a nominal adjective in English. Do NOT expand it into a relative clause with "who is," "what is," or similar:

| Hebrew Pattern | Literal ULT | NOT |
|----------------|-------------|-----|
| כָּל-צָמֵא (kol tsame) | "everyone thirsty" | "all who are thirsty" |
| הַטּוֹב (ha-tov) | "the good" | "what is good" |

Do not insert "who is," "what is," or any relative pronoun between the determiner and the adjective (per-word rulings: `ult_decisions.csv` H6771, H2896).

## Prepositional Nominals with Negation

Hebrew expresses "one who has no X" as a prepositional-existential construction (e.g., אֲשֶׁר אֵין לוֹ כֶּסֶף = "to whom there is no silver"). Preserve the Hebrew prepositional structure; do not convert it to an English possession verb or verbal clause:

| Hebrew Pattern | Literal ULT | NOT |
|----------------|-------------|-----|
| אֲשֶׁר אֵין לוֹ כֶּסֶף | "to whom {is} no silver" | "whoever has no money" |
| לְלֹא בְשֹׂבְעָה | "for {what is} not to sufficiency" | "for what does not satisfy" |

Supply only the minimum bracketed copula ({is}) needed for English grammar. Do not introduce "has" or convert a Hebrew prepositional noun phrase (e.g., שְׂבָעָה "sufficiency/satiety") into a verb (see `ult_decisions.csv` H7654).

## Predicate Adjectives

When Hebrew uses an adjective predicatively, keep the English copula if needed to show the predicate relationship. Do not collapse it into an attributive adjective phrase:

- "how they are beautiful" not "how beautiful"
- "he will be very high" not "greatly exalted"

## Comparative Constructions

Comparatives with מִן use English comparative form:

| Hebrew Pattern | Literal ULT | NOT |
|----------------|-------------|-----|
| yarum mimmenni | "higher than I" | "high away from me" |
| gadol mimmenni | "greater than I" | "great from me" |
| X + min (comparative) | "X-er than Y" | "X away from Y" |

## Role/Status Prepositions

When לְ marks a role, office, or resulting status before a noun, preserve it as a prepositional phrase rather than converting it into an infinitive:

| Hebrew Pattern | Literal ULT | NOT |
|----------------|-------------|-----|
| לְ + role noun | "as a/an [role]" | "to be a/an [role]" |
| יֹצְרִי מִבֶּטֶן לְעֶבֶד לוֹ | "formed me from the womb as his servant" | "formed me from the womb to be his servant" |

## Emphatic Doubling

Preserve Hebrew doubling without adding words:

| Hebrew | Literal ULT | NOT |
|--------|-------------|-----|
| yom yom | "day, day" | "day {by} day" |
| dor wador | "generation and generation" | - |

## Disjunctive Conjunctions

When Hebrew waw separates alternatives, render it as English "or", not "and". Do not force plural agreement in English when the Hebrew subject remains singular.
