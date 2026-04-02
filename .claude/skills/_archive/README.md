# Archived Python Scripts

These are **reference implementations** superseded by Node.js MCP tools in `app/src/workspace-tools/`.

The bot pipeline runs in a Chainguard Node.js container with no Python/bash. All mechanical pipeline work
goes through `mcp__workspace-tools__*` tools. These scripts are preserved for:
- Historical reference and documentation of original logic
- Porting guide if additional checks need to be adapted
- Debugging when Node.js behavior differs unexpectedly

## How to find the MCP equivalent

| Python script | MCP tool |
|---|---|
| `check_tn_quality.py` | `mcp__workspace-tools__check_tn_quality` |
| `validate_tn_tsv.py` | `mcp__workspace-tools__validate_tn_tsv` |
| `fix_trailing_newlines.py` | `mcp__workspace-tools__fix_trailing_newlines` |
| `prepare_notes.py` | `mcp__workspace-tools__prepare_notes` |
| `assemble_notes.py` | `mcp__workspace-tools__assemble_notes` |
| `generate_ids.py` | `mcp__workspace-tools__generate_ids` |
| `resolve_gl_quotes.py` | `mcp__workspace-tools__resolve_gl_quotes` |
| `extract_alignment_data.py` | `mcp__workspace-tools__extract_alignment_data` |
| `fix_hebrew_quotes.py` | `mcp__workspace-tools__fix_hebrew_quotes` |
| `fix_unicode_quotes.py` | `mcp__workspace-tools__fix_unicode_quotes` |
| `flag_narrow_quotes.py` | `mcp__workspace-tools__flag_narrow_quotes` |
| `verify_at_fit.py` | `mcp__workspace-tools__verify_at_fit` |
| `build_strongs_index.py` | `mcp__workspace-tools__build_strongs_index` |
| `build_tn_index.py` | `mcp__workspace-tools__build_tn_index` |
| `build_ust_index.py` | `mcp__workspace-tools__build_ust_index` |
| `fetch_door43.py` | `mcp__workspace-tools__fetch_door43` |
| `fetch_hebrew_bible.py` | `mcp__workspace-tools__fetch_hebrew_bible` |
| `fetch_all_ult.py` | `mcp__workspace-tools__fetch_ult` |
| `fetch_all_ust.py` | `mcp__workspace-tools__fetch_ust` |
| `fetch_t4t.py` | `mcp__workspace-tools__fetch_t4t` |
| `fetch_glossary.py` | `mcp__workspace-tools__fetch_glossary` |
| `fetch_templates.py` | `mcp__workspace-tools__fetch_templates` |
| `fetch_issues_resolved.py` | `mcp__workspace-tools__fetch_issues_resolved` |
| `check_tw_headwords.py` | `mcp__workspace-tools__check_tw_headwords` |
| `compare_ult_ust.py` | `mcp__workspace-tools__compare_ult_ust` |
| `detect_abstract_nouns.py` | `mcp__workspace-tools__detect_abstract_nouns` |
| `extract_ult_english.py` | `mcp__workspace-tools__extract_ult_english` |
| `filter_psalms.py` | `mcp__workspace-tools__filter_psalms` |
| `curly_quotes.py` / `fix_quotes.py` | `mcp__workspace-tools__curly_quotes` |
| `check_ust_passives.py` | `mcp__workspace-tools__check_ust_passives` |
| `split_tsv.py` | `mcp__workspace-tools__split_tsv` |
| `merge_tsvs.py` | `mcp__workspace-tools__merge_tsvs` |
| `prepare_tq.py` | `mcp__workspace-tools__prepare_tq` |
| `verify_tq.py` | `mcp__workspace-tools__verify_tq` |
| `prepare_compare.py` | `mcp__workspace-tools__prepare_compare` |
| `gitea_pr.py` | `mcp__workspace-tools__gitea_pr` |
| `insert_tn_rows.py` | handled by `door43-push.js` in app/ |
| `insert_usfm_verses.py` | handled by `door43-push.js` in app/ |
| `validate_alignment_json.py` | `mcp__workspace-tools__validate_alignment_json` |
| `validate_ult_brackets.py` | `mcp__workspace-tools__validate_ult_brackets` |
| `check_ult_voice_mismatch.py` | `mcp__workspace-tools__check_ult_voice_mismatch` |

## Scripts NOT archived (still in use)
- `gemini_review.py` — external Gemini CLI wrapper, runs interactively where Python is available
- `test_prompt_over_code.py` — test harness for A/B comparisons
