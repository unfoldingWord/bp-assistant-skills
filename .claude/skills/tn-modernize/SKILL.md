---
name: tn-modernize
description: Rewrite old-style en_tn notes into the current note templates without losing information, and deliver them as one open en_tn PR for human review. Use when asked to modernize, re-template or update pre-template translation notes for a book.
---

# Modernize old translation notes

Older en_tn notes predate the current note templates. This skill rewrites the **Note column** of those rows into the template wording, keeps every piece of their information, and delivers the result as one open (never merged) en_tn PR with one commit per book.

The deterministic steps live in bp-assistant (`scripts/tn-modernize/`). This folder holds the three prompts the scripts send:

| File | Used by | Job |
| --- | --- | --- |
| `rewrite-prompt.md` | `rewrite.mjs`, Sonnet | Choose the template variant, fill it from the old note, or decline |
| `claims-prompt.md` | `claims.js`, Haiku | List the separate pieces of information in each old note |
| `judge-prompt.md` | `claims.js`, Haiku | For each claim, the probability the new note still makes it |

jev (TypeSafe's typed-decision model) is the primary claim judge. It takes the claims as yes/no questions and needs no prompt file. On the October 2026 pilot it caught 79% of seeded information losses at the 0.8 threshold, against 49% for the Haiku judge, so Haiku runs only as a second opinion (`--judge both`). Its key is `TYPESAFE_API_KEY_TN_MODERNIZE` in `~/.config/ai-keys.env`.

## What is never touched

- Every column except Note.
- Rows whose note already contains the first fixed phrase of one of its templates (this protects the 2024-2025 human work).
- Intro rows, rows without a translate SupportReference, rows whose SupportReference has no template.
- Rows the model declines (two issues in one note, no fitting template, unclear meaning).
- Any row where a gate fails. It keeps its current text and is listed in the review report.

## Gates (all must pass, or the note stays as it is)

1. Every bold span is exact ULT text of the verse.
2. Every alternate translation is kept word for word in `[brackets]`; none is invented.
3. No `rc://` or `[[...]]` link is left in the note. Dropped "(See also: [[tA]])" and "(See: [[tW]])" links are logged, and the report lists any whose information is not carried elsewhere (no sibling note with that SupportReference; no twl entry for that tW article).
4. Every name and scripture reference survives.
5. The claim check finds every claim of the old note in the new one.
6. The new note contains its template's first fixed phrase and no unfilled placeholder.

## Running it

All paths below are from the bp-assistant checkout. Work files go to `$TN_MODERNIZE_DIR` (default `~/.local/state/tn-modernize`).

    # 0. Freeze one templates snapshot for the whole run (data/templates.csv, "# Fetched:" line)
    # 1. Which books need it (needs an en_tn clone with history: git clone --filter=blob:none ...)
    node scripts/tn-modernize/survey.mjs --tn <en_tn>
    # 2. Candidates for the chosen books
    node scripts/tn-modernize/extract.mjs --tn <en_tn> --ult <en_ult> --twl <en_twl> BOOK...
    # 3. Rewrite, gate, claim-check (resumable; --dry prints the first prompt)
    CLAUDE_CONFIG_DIR=<account dir> node scripts/tn-modernize/rewrite.mjs \
      --skill <bp-assistant-skills>/.claude/skills/tn-modernize \
      --limits ~/.claude/rate-limits.<uuid8>.json BOOK...
    # 4. Review page
    node scripts/tn-modernize/report.mjs BOOK...
    # 5. Local proof that only Note cells change, then the PR
    node scripts/tn-modernize/apply.mjs --tn <en_tn> BOOK...
    DOOR43_TOKEN=... node scripts/tn-modernize/publish.mjs --dry BOOK...
    DOOR43_TOKEN=... node scripts/tn-modernize/publish.mjs --report-url <url> BOOK...

`rewrite.mjs` calls Claude through the Agent SDK with no tools, on the account logged in at `CLAUDE_CONFIG_DIR`, and stops when that account's weekly usage reaches `--stop-pct` (default 60). Keep an interactive Claude session open on that account so the usage file stays fresh.
