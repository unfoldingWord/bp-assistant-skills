# Structured Edit Policy (shared by tn-writer and tn-quality-check)

Do NOT write Python, bash, or other scripts to `/tmp/` or anywhere else.

Do NOT hand-`Edit` `generated_notes.json`, `prepared_notes.json`, or the
assembled notes TSV to revise a row's text or quote, or to delete it. Use the
structured tools instead — they locate items by id and never produce "string
to replace not found" errors:

- `mcp__workspace-tools__update_note_text` — set one generated note's text by id
- `mcp__workspace-tools__update_prepared_quote` — set a prepared note's quote fields by id
- `mcp__workspace-tools__remove_note` — remove a note by id from generated_notes.json and/or the TSV

If an `Edit` ever returns "string to replace not found" against any of these
files, do not retry it: re-Read once or switch to the structured tool. If the
target still cannot be matched, leave the row as-is (or tag it unresolved) and
move on. Repeated `Edit` retries against these files trip the runner's
repeated-tool-error guardrail and fail the whole shard.
