# Plan: Add Deep Quality Check to tn-writer Pipeline

## Problem

PSA 68:9-10 revealed that the pipeline can produce contradictory notes across adjacent verses. Issue-id said "inheritance = people" in v9 but "it refers to the land" in v10. The note writer faithfully reflected both, producing notes f4yd and my8i that contradict each other.

Cross-verse interpretive consistency checks were added to issue-id (Final Review item #2), tn-writer Step 6 (mental map guidance), and tn-quality-check (check 3j) in commit 5e013b70ec. Those are already merged.

## Remaining Gap: Template Adherence + Deep QC in the Pipeline

Template adherence (check 3b) and cross-verse consistency (check 3j) both live in tn-quality-check's **deep semantic review** (Step 3). But:

- tn-writer never invokes tn-quality-check -- it's a standalone skill
- makeBP never invokes tn-quality-check -- it goes straight from tn-writer to repo-insert
- The only post-hoc checks in tn-writer are the lightweight Step 10 (manual scan) and optional Step 11 (Gemini)

So in normal pipeline operation (makeBP via Zulip), deep semantic review never runs.

## Proposed Change

Add a new step in tn-writer between current Step 10 (Final Review) and Step 11 (Gemini Review) that runs the full tn-quality-check inline: mechanical script + deep semantic review (checks 3a-3j).

### What to add (tn-writer/SKILL.md)

Insert new **Step 11: Deep Quality Check** after Step 10. Renumber current Step 11 (Gemini) to Step 12.

Contents:

1. Run `check_tn_quality.py` (the mechanical script) on the assembled TSV
2. Read findings JSON
3. Perform semantic review checks 3a-3j from tn-quality-check SKILL.md, with emphasis on:
   - **3b** (template adherence): fixed phrases preserved, no drift
   - **3j** (cross-verse interpretive consistency): pronoun back-refs, carried figures, AT compatibility
4. Fix issues directly in the TSV. If a note needs regeneration, update `generated_notes.json` and re-run `assemble_notes.py`.

### Double-execution check

**Zulip notes pipeline** (`/srv/bot/app/src/notes-pipeline.js`): The pipeline pushes `tn-quality-check` as a separate stage after `tn-writer` (lines 228-233). Once deep QC is integrated into tn-writer, this standalone stage must be **removed** from the pipeline to avoid running the same checks twice (heavy inside tn-writer, then again as a lightweight standalone pass).

- **parallel-batch**: No quality check invocation — no change needed.
- **tn-quality-check as standalone**: Only runs when user explicitly invokes `/tn-quality-check`. Running it standalone after this change would re-run the same checks, but that's intentional (user wants a second look) not accidental duplication.

### Files to modify

1. `.claude/skills/tn-writer/SKILL.md` -- Insert Step 11 (deep QC), renumber Step 11 -> 12
2. `/srv/bot/app/src/notes-pipeline.js` -- Remove the `tn-quality-check` skill push (lines 228-233) since deep QC is now inside tn-writer
3. No changes needed to parallel-batch or tn-quality-check itself
