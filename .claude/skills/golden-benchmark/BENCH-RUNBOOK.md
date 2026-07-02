# Golden-benchmark run-on-bot runbook

How to run a model A/B (or single-model regression) against a published golden
chapter without corrupting the live workspace. This captures the guardrails
learned from the NAM 1 and JOS 3 runs. Plain checklist; read it before every run.

## Where things run

- The pipeline runs only on the dfw `uw-bt-bot` Fly machine (the only place with
  source data and the `workspace-tools` MCP). Drive it with
  `flyctl ssh console -a uw-bt-bot`.
- The golden scorer and fixtures live in `bp-assistant-skills` under
  `.claude/skills/golden-benchmark/` (locally, not on the bot). Scoring happens
  off the bot after you copy the generated output back.

## Mandatory preflight (do these before any run)

1. Confirm the bot's skills checkout is on the branch/commit you intend to test.
   A recent A/B accidentally ran against skills that were four commits stale.

   ```
   flyctl ssh console -a uw-bt-bot -C \
     "git -c safe.directory=/data/workspace -C /data/workspace log -1 --oneline"
   ```

   Compare the printed commit to the branch/commit you mean to benchmark. If it
   does not match, the workspace has not refreshed (see the deploy/refresh notes
   in the project CLAUDE.md) - stop and reconcile before running. Scoring a run
   against the wrong skills version produces a result that looks valid but tests
   the wrong thing.

2. Root-ownership sweep. Root-owned leftovers under `output/` or `tmp/` cause
   EACCES failures that kill botuser runs (this is what broke the NAM 1 TN
   quality-check and made that comparison unfair). The following must return
   nothing:

   ```
   flyctl ssh console -a uw-bt-bot -C \
     "find /data/workspace/output /data/workspace/tmp -not -user botuser"
   ```

   If it prints any path, remove or re-own those paths (as the appropriate user)
   before starting. Do not start a run while this is non-empty.

## Run guardrails

- Run pipeline commands as botuser, never as root:

  ```
  flyctl ssh console -a uw-bt-bot -C \
    "su -s /bin/bash botuser -c 'cd /app && TEST_MODEL=<id> node src/test-pipeline.js \"<msg>\"'"
  ```

  After a run, verify the new output files are botuser-owned.

- Always include `--no-push` in the pipeline message. This runs the full
  pipeline (including alignment) but skips the Door43 push. Never create real
  PRs, and never push to Door43 from a benchmark run.

- Force the model with an explicit id, not an alias: `TEST_MODEL=claude-opus-4-8`
  or `TEST_MODEL=claude-sonnet-5`. Confirm the served model from the run log
  (SDK init `model`).

- Do not deploy or restart the bot, and do not edit `Dockerfile.fly` (Node is
  pinned).

- One leg at a time. Legs share output paths, so runs must be strictly
  sequential. Before starting a leg, confirm the bot is idle:
  `curl -s localhost:8080/health/pipelines` should report `"active":0`. After a
  notes run, health can read `active:0` while a roughly five-minute
  `self-diagnosis` tail process still lingers - also confirm no lingering
  process with `ps -eo args | grep test-pipeline` before the next leg.

- Launch each leg detached so it survives the SSH session closing, redirecting
  at the `setsid` level (otherwise the SSH channel hangs):

  ```
  setsid node src/test-pipeline.js "<msg>" > <log> 2>&1 </dev/null &
  ```

  Then poll `/health/pipelines` until `active:0`.

## Per-leg verification

- After each generate, confirm alignment is non-empty:
  `output/AI-{ULT,UST}/<BOOK>/<BOOK>-<CH>-aligned.usfm` must be substantial (not
  about 71 bytes). If empty or timed out, retry - never score a broken run.

- After each notes run, confirm it completed cleanly: expect the Zulip check
  reaction or a `Notes pipeline complete` log line, not a `failed` or
  `self-diagnosis` outcome. A QC-incomplete notes leg is invalid; retry it. An
  asymmetric QC completion between legs makes the TN comparison unfair.

## Cleanup between legs

Clear prior artifacts for the chapter before each leg, including the
directories an earlier cleanup missed:

- `output/{AI-ULT,AI-UST,notes,issues,quality}/<BOOK>/<BOOK>-<CH>*`
- `output/AI-UST/hints/<BOOK>/<BOOK>-<CH>*`
- `tmp/pipeline/<BOOK>-<CH>*`
- `tmp/alignments/<BOOK>-0<CH>-*`
- checkpoints matching `*<BOOK>_<CH>*` under `/app/data/pipeline-checkpoints/`

Confirm `active:0` after cleanup.

## Scoring (off the bot)

1. Copy the generated ULT/UST/notes off the machine into the scorer layout in
   `bp-assistant-skills`:
   `output/AI-ULT/<BOOK>/<BOOK>-<CH>.usfm`,
   `output/AI-UST/<BOOK>/<BOOK>-<CH>.usfm`,
   `output/notes/<BOOK>/<BOOK>-<CH>.tsv`.

2. Ensure the golden fixture exists. If the chapter is not in the fetch script's
   golden set, fetch it manually (ULT/UST from the pinned release tag, TN from
   en_tn master) into `golden/<BOOK>/`.

3. Sanity-check the golden with the self-test before scoring real output; it
   should report perfect scores:

   ```
   node .claude/skills/golden-benchmark/scripts/score_benchmark.mjs \
     --book <BOOK> --chapter <CH> --self-test --json
   ```

4. Score each leg:

   ```
   node .claude/skills/golden-benchmark/scripts/score_benchmark.mjs \
     --book <BOOK> --chapter <CH> \
     --generated-ult ... --generated-ust ... --generated-tn ... --json
   ```

   Report TN verse-only recall/precision alongside the (verse|type) numbers, to
   separate coverage from house-style taxonomy mirroring. Non-empty Tags values
   (for example internal `ISSUE:MATCH_FAIL` markers) surface as convention
   problems - published golden Tags are always empty, so any non-empty Tags in
   generated notes indicate leaked internal markup.
