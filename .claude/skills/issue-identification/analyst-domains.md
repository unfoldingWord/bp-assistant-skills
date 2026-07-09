# Analyst Domains

Domain assignments for the 2-analyst default mode. Both orchestrators
(deep-issue-id, initial-pipeline) use these identical domain definitions.

## Structure Analyst (teammate name: "structure")

Grammar and discourse structure, from macro to micro level. Discourse markers,
participant tracking, paragraph structure, connectors between clauses, quotation
structure, genre indicators, passives, abstract nouns, possession, pronouns,
ellipsis, word-level syntax. Integrates automated detection output first.
Focuses on writing-\*, grammar-connect-\*, figs-activepassive, figs-abstractnouns,
figs-possession, writing-pronouns, figs-ellipsis, and similar structural issues.

Output: `$TMP/wave2_structure.tsv`

## Rhetoric Analyst (teammate name: "rhetoric")

Figures of speech, speech acts, and cultural references. Metaphor, metonymy,
simile, synecdoche, personification, merism, hendiadys, doublet, idiom,
rhetorical questions, imperatives, exclamations, irony, hyperbole, litotes,
euphemism, poetry markers, parallelism. Cross-references the biblical imagery
classification lists in figs-metonymy.md and figs-metaphor.md.

Output: `$TMP/wave2_rhetoric.tsv`

### Figure stacking in dense figurative clauses

In figuratively compressed text -- hymns, theophany, woe-oracles, eschatological
and other poetry/prophecy -- a single clause routinely carries several
*independent* figures: a metaphor whose vehicle is itself a metonymy, plus
implied information the reader must supply, plus a nested "X said..." quotation.
Benchmarking against published notes shows recognition drops on exactly these
clauses -- the analyst flags the one most salient figure and moves on, leaving
the rest unnoted.

On any clause you judge figuratively dense, decompose it and test each figure
type independently instead of stopping at the first hit. Before leaving such a
clause, explicitly check at least: metaphor, metonymy, simile, personification,
quotes-in-quotes / nested speech, and implied-or-explicit information. Each
genuinely distinct figure a translator could misrender earns its own note, even
when several land in the same clause.

This is a per-clause thoroughness instruction, not a license to raise density in
prose. Narrative and disputation clauses rarely stack figures; leave them at
their usual rate -- the calibration budget in `SKILL.md` (Selectivity) still
governs the chapter total.

## Cross-Reading Protocol

As each analyst works, they read the other's TSV file when it appears. If the
same phrase is classified differently, the analyst sends a DM to flag the
disagreement. This is lightweight -- not forced on every issue, just available
when analysts genuinely disagree.

## Analyst Prompt Template

Include in each analyst's prompt:

1. Spawn with `subagent_type: "issue-identification"`, `model: "opus"`, and
   `team_name` set to the team name.
2. The output format guardrail (see `agents/issue-identification.md` lines 9-31).
3. Instruction to read the other analyst's TSV file as it appears.
4. Instruction to use SendMessage for disagreements worth flagging.
5. **Hold instructions** -- orchestrator-specific (see the orchestrator's SKILL.md
   for what each analyst should hold for after writing their TSV).
