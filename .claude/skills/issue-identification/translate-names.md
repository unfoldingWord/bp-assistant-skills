# translate-names

## Purpose
Identify when proper names need translation notes to help readers understand what they refer to or how to translate them.

## Definition
Proper names in the Bible refer to specific people, places, groups, or things. Translators may need guidance when:
- Readers won't know what kind of thing a name refers to
- Translators must choose between transliterating the name or expressing its meaning
- A person or place has two different names

## When to Write Notes

### 1. Name Type Identification
When readers might not know what category a name belongs to:
- "**Cyrus** is the name of a man"
- "**Persia** is the name of an empire"
- "**Jordan** is the name of a river"
- "**Abijah** is the name of a division of priests"

### 2. Gender Clarification
When the gender of a person is not clear from context:
- "**Abdon** is the name of a man" (even though context says "Abdon son of Hillel")
- "**Zeruiah** is the name of a woman" (when used as mother/ancestor of men)

### 3. Multiple Names
When person or place has two different names:
- Saul/Paul, Abram/Abraham, Jacob/Israel
- Original and modern names for places
- Note at first occurrence explaining the relationship

### 4. Transliterate vs Express Meaning
When translators may choose to express the name's meaning:
- Names whose meaning is significant in context (Beer Lahai Roi = "Well of the Living One who sees me")
- Musical terms in psalms (Shoshannim, Sheminith)
- Use translate-names when it's a NAME with meaning option (NOT translate-transliterate, which is for non-name words like "Amen")

### 5. Lists of Names
When multiple names appear together:
- "These are the names of eleven men" (for a list)
- Individual notes may not be needed for each name in a list

## When NOT to Write Notes

### Text Already Identifies
Don't write notes when the original text clarifies what something is:
- "the Valley of Jezreel" - text says it's a valley
- "the Jordan River" - text says it's a river
- "King Herod" - text identifies him as a king

### UST Clarifies
If UST identifies something as a town, city, river, etc., no note needed.

### tW Article Exists
If the name matches a Translation Words headword, the tW article provides the definition. Check with:
```bash
python3 .claude/skills/issue-identification/scripts/check_tw_headwords.py "NameToCheck"
```
If match found in "names" category: **generally NO translate-names note needed**.

Exception: If the name is used in a figurative expression, use the appropriate figurative note (figs-idiom, figs-metonymy, etc.) instead.

To verify what the tW article covers, read: `data/en_tw/names/[twarticle].md`

### First Occurrence Only
After the first note explaining a name, use "See how you translated this in [X:Y]" for subsequent occurrences.

## NOT This Issue

### Use translate-transliterate instead when:
- Non-name words kept in original form (Amen, Abba, Hosanna)
- Words transliterated but NOT proper names

### Use figs-metaphor/figs-idiom instead when:
- Name is used in a figurative expression
- "Yahweh burned in his nose" - figs-idiom (anger idiom), not translate-names
- "house of David" meaning descendants - figs-metaphor, not translate-names

### Use writing-participants instead when:
- Introducing a new character (focus on narrative function, not name clarification)

## Categories of Names

### People Names
- Individual people (Cyrus, David, Anna)
- Gender may need clarification
- Common pattern: "**Name** is the name of a man/woman"

### Place Names
- Cities, regions, bodies of water, mountains
- Types: city, town, village, region, province, empire, river, sea, mountain, valley
- Common pattern: "**Name** is the name of a [type of place]"

### People Group Names
- Nations, tribes, ethnic groups
- "**Judah** and **Benjamin** are the names of two of the tribes of Israel"
- Often appear with figs-genericnoun (singular for category)

### Names with Meaning
- When the name's meaning is relevant to the passage
- Note explains both the name and its meaning
- "**Beer Lahai Roi** means 'Well of the Living One who sees me'"

## Headword Check Workflow

After identifying a potential name issue:

1. Run the headword check script:
   ```bash
   python3 .claude/skills/issue-identification/scripts/check_tw_headwords.py "Name"
   ```

2. If match found:
   - Check if name is used literally (straight reference to person/place) -> NO note needed, tW covers it
   - Check if name is used figuratively -> Use appropriate figurative note instead

3. If no match: Likely needs a translate-names note

4. If uncertain whether tW article covers the usage, read the article:
   `data/en_tw/names/[twarticle].md`

## Note Writing Patterns

### Standard Pattern
"**[Name]** is the name of a [man/woman/city/region/etc.]."

### With Context
"**[Name]** is the name of a man. This is the same **[Name]** mentioned in [X:Y]."

### For Lists
"These are the names of [number] men/women/places."

### With Meaning
"If you include the meaning of **[Name]**'s name in your translation or in a footnote, make sure it is similar to the word in the following clause that has the same meaning."

### Cross-reference
"See how you translated this name in [X:Y]."
