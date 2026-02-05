# Skill Improvement Guide

How to improve ULT-gen and related skills based on comparing AI output to human output.

## The Improvement Process

### 1. Compare AI vs Human Output

Run the skill on a passage, then compare against human-created version side-by-side:

```
| AI Output | Human Output |
|-----------|--------------|
| "For the music director" | "For the chief musician" |
```

### 2. Categorize Each Difference

| Category | Where to Fix | Example |
|----------|--------------|---------|
| **Vocabulary choice** | `project_glossary.md` Words table | "preserve" not "guard" |
| **Phrase pattern** | `project_glossary.md` Phrases table | "day, day" not "day {by} day" |
| **Grammar rule** | `SKILL.md` (new section or update existing) | Comparatives use "-er than" form |
| **Style/format** | `reference/gl_guidelines.md` | Periods between superscription elements |
| **Literalness pattern** | `reference/literalness_patterns.md` | Emphatic doubling preserved |
| **USFM formatting** | `SKILL.md` Step 6 | Selah uses `\qs ... \qs*` |

### 3. Check Authority Sources First

Before adding a correction, verify against the authority hierarchy:

1. **Issues Resolved** (`data/issues_resolved.txt`) - If it contradicts your correction, Issues Resolved wins
2. **Published ULT** - Check 3-5 occurrences of the term/pattern
3. **Existing glossaries** - May already have guidance

If your correction aligns with these sources, proceed. If it contradicts them, the AI may actually be correct and the human version may need review.

## Where Each Type of Fix Goes

### project_glossary.md

**Use for:** Individual word or phrase decisions that override or supplement fetched glossaries.

**Format - Words table:**
```markdown
| Hebrew | Strong | ULT | Not | Notes |
|--------|--------|-----|-----|-------|
| נָצַר | H5341 | preserve | guard | watching over/protecting context |
```

**Format - Phrases table:**
```markdown
| Hebrew Pattern | ULT | Not | Notes |
|----------------|-----|-----|-------|
| יוֹם יוֹם | day, day | day {by} day | preserve doubling |
```

**Do NOT modify:** `psalms_reference.csv`, `hebrew_ot_glossary.csv`, or other fetched glossaries - they get overwritten.

### SKILL.md

**Use for:** Rules that apply across many situations, workflow steps, new pattern categories.

**Where to add:**
- **Step 3 subsections (A-J):** Translation rules by category
- **Step 4:** Bracket usage rules
- **Step 5:** Style rules
- **Step 6:** USFM formatting
- **Quality Checklist:** New verification items

**Example - Adding a new subsection:**
```markdown
#### K. New Pattern Category

| Hebrew | ULT | NOT |
|--------|-----|-----|
| example | correct | incorrect |
```

### reference/literalness_patterns.md

**Use for:** Patterns about preserving Hebrew structure literally.

**Current sections:**
- Word Order Preservation
- Hiphil Causatives
- Construct Chains
- Literal Verbal Idioms
- Comparative Constructions
- Emphatic Doubling

**Format:**
```markdown
## New Pattern Type

Description of when this applies.

| Hebrew | Literal ULT | NOT |
|--------|-------------|-----|
| example | correct | incorrect |
```

### reference/gl_guidelines.md

**Use for:** Style, formatting, punctuation, capitalization rules.

**Rarely needs modification** - most style rules are already comprehensive.

## Decision Tree

```
Is it a single word rendering?
  YES -> project_glossary.md Words table
  NO  -> continue

Is it a phrase or construction?
  YES -> Does it involve literalness/Hebrew structure?
    YES -> reference/literalness_patterns.md
    NO  -> project_glossary.md Phrases table
  NO  -> continue

Is it a grammar/translation rule?
  YES -> SKILL.md (find appropriate Step 3 subsection or create new)
  NO  -> continue

Is it about USFM formatting?
  YES -> SKILL.md Step 6
  NO  -> continue

Is it about style/punctuation/capitalization?
  YES -> reference/gl_guidelines.md
  NO  -> Ask for clarification
```

## File Size Guidelines

| File | Target | Current | Notes |
|------|--------|---------|-------|
| SKILL.md | <500 lines | ~450 | Core workflow only |
| literalness_patterns.md | <100 lines | ~65 | Pattern examples |
| gl_guidelines.md | <150 lines | ~132 | Style rules |
| project_glossary.md | No limit | ~30 | Grows with decisions |

## After Making Changes

1. **Update Quality Checklist** in SKILL.md if you added a new rule category
2. **Test** by re-running the skill on the same passage
3. **Spot-check** 2-3 other passages to ensure changes don't break existing patterns

## Common Pitfalls

- **Don't duplicate** - Check if a rule already exists before adding
- **Don't contradict** - Verify against Issues Resolved first
- **Don't over-specify** - Add rules only when AI consistently gets something wrong
- **Don't modify fetched glossaries** - Use project_glossary.md for overrides

## Example: Full Improvement Cycle

**Observation:** AI produces "high away from me" but human has "higher than I"

**Analysis:**
1. Check Issues Resolved - no specific ruling
2. Check published ULT - consistently uses comparative form
3. This is a literalness pattern about comparatives

**Actions:**
1. Add to `reference/literalness_patterns.md`:
   ```markdown
   ## Comparative Constructions
   | יָרוּם מִמֶּנִּי | higher than I | high away from me |
   ```

2. Add to `SKILL.md` Step 3:
   ```markdown
   #### G. Comparatives with מִן
   | Hebrew Pattern | ULT | NOT |
   | יָרוּם מִמֶּנִּי | "higher than I" | "high away from me" |
   ```

3. Add to `project_glossary.md` Phrases table:
   ```markdown
   | יָרוּם מִמֶּנִּי | higher than I | high away from me | comparative with מִן |
   ```

4. Add to Quality Checklist:
   ```markdown
   - [ ] Comparatives with מִן use "-er than" form ("higher than I")
   ```

**Why all three places?**
- `literalness_patterns.md`: Documents the pattern for reference
- `SKILL.md`: Instructs the AI during generation
- `project_glossary.md`: Catches this specific phrase in lookups
