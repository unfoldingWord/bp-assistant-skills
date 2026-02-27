#!/bin/bash
# Weekly refresh of canonical data files (issues_resolved.txt + glossary CSVs)
# Intended to run via cron every Thursday at 05:00 UTC
# Runs fetch scripts inside the zulip-bot container

CONTAINER=zulip-bot
LOG=/srv/bot/workspace/tmp/weekly-refresh.log
TIMESTAMP=$(date '+%Y-%m-%d %H:%M')

mkdir -p /srv/bot/workspace/tmp

echo "[$TIMESTAMP] Weekly refresh starting" >> "$LOG"

docker exec "$CONTAINER" python3 \
  /workspace/.claude/skills/issue-identification/scripts/fetch_issues_resolved.py --force \
  >> "$LOG" 2>&1

docker exec "$CONTAINER" python3 \
  /workspace/.claude/skills/utilities/scripts/fetch_glossary.py --all --force \
  >> "$LOG" 2>&1

echo "[$TIMESTAMP] Weekly refresh complete" >> "$LOG"
