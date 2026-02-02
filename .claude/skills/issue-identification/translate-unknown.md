# translate-unknown

## Purpose
Identify when concepts, objects, or practices from the biblical world may be unfamiliar to target culture readers.

## Definition
"Unknowns" are things in the source text that readers may not recognize because they are not part of their culture. This includes:
- Animals, plants, foods not found in their region
- Objects, tools, clothing from ancient times
- Cultural practices, roles, or institutions
- Abstract concepts expressed in unfamiliar ways

## When to Write Notes

### 1. Animals Unknown to Target Culture
Animals that don't exist in the target region:
- Jackals, wolves, lions, bears - wild animals not found everywhere
- Locusts, specific birds, sea creatures

### 2. Plants and Foods
Foods or plants not part of the target culture:
- Bread, wine, specific grains
- Myrrh, frankincense, other plant products
- Figs, olives, cedars

### 3. Objects and Materials
Items from ancient culture:
- Portable beds/mats for carrying people
- Fishing nets, agricultural tools
- Specific fabrics (linen, sackcloth)

### 4. Cultural Practices and Roles
Practices or positions readers may not understand:
- Specific occupations or conditions (paralytic, eunuch)
- Religious roles (high priest, Levite functions)
- Social customs

### 5. Abstract Concepts
When abstract ideas need clarification:
- Divisions, factions within groups
- Specific types of arguments or debates

## When NOT to Write Notes

### tW Article Covers It
If the term matches a Translation Words headword, the tW article provides the definition. Check with:
```bash
python3 .claude/skills/issue-identification/scripts/check_tw_headwords.py "TermToCheck"
```
If match found in "other" or "kt" category: **generally NO translate-unknown note needed**.

To verify what the tW article covers, read: `data/en_tw/[category]/[twarticle].md`

### Figurative Use
When the unknown item is used figuratively, use the appropriate figurative note:
- "bread" in "give us our daily bread" (metonymy for food/provision) -> figs-metonymy
- "lion" in "Judah is a lion's cub" -> figs-metaphor
- "wolves in sheep's clothing" -> figs-metaphor

### Historical Items Must Stay
Don't encourage substituting modern or local items for specific historical things:
- DON'T suggest replacing "judges and elders" with local equivalents
- DON'T suggest replacing specific historical objects
- For figurative uses (like in similes), substitution may be acceptable

### Widely Known Concepts
If something is widely known around the world (even if not locally):
- If UTW assumes knowledge of it in a related article, it's probably widely enough known

## NOT This Issue

### Use translate-names instead when:
- The unknown item is a proper name (person, place, group)
- Focus is on identifying what kind of thing a name refers to

### Use figs-metaphor/figs-simile instead when:
- Item is part of a comparison or metaphor
- Focus is on the figurative meaning, not the item itself

### Use translate-transliterate instead when:
- Word is kept in original form (Hebrew/Greek/Aramaic)
- Focus is on how to render an untranslated word

## Special Rules

### Rhetorical Series
When translate-unknown addresses a series of terms used together for rhetorical effect, **preserve the effect**:
- DON'T simplify "brooks of water, fountains, and springs" to just "rivers"
- The alternate translation should maintain the rhetorical impact (e.g., "many flowing bodies of water")

### Historical Accuracy
For specific historical items described in the text:
- Use a general term or descriptive phrase
- Don't suggest substituting culturally-specific equivalents
- Footnotes can provide more detail

## Headword Check Workflow

After identifying a potential unknown concept:

1. Run the headword check script:
   ```bash
   python3 .claude/skills/issue-identification/scripts/check_tw_headwords.py "term"
   ```

2. If match found:
   - Check if term is used literally -> NO note needed, tW covers it
   - Check if term is used figuratively -> Use appropriate figurative note instead

3. If no match: Likely needs a translate-unknown note

4. If uncertain whether tW article covers the usage, read the article:
   `data/en_tw/[category]/[twarticle].md`

## Categories of Unknowns

### Animals
- Wild animals (jackals, wolves, lions, bears)
- Birds (partridge, raven, dove)
- Insects (locusts, bees, gnats)
- Sea creatures (Leviathan, various fish)

### Plants and Foods
- Grains (wheat, barley)
- Prepared foods (bread, wine, olive oil)
- Trees and plants (fig, olive, cedar, hyssop)
- Spices and perfumes (myrrh, frankincense)

### Objects and Materials
- Clothing (linen, sackcloth, leather belt)
- Tools (nets, plows, millstones)
- Furniture (mat, couch)
- Building materials (cedar, bronze)

### Cultural Concepts
- Social roles (paralytic, eunuch)
- Religious items (ephod, Urim and Thummim)
- Institutions (synagogue, Sanhedrin)
