#!/usr/bin/env bash
# .claude/hooks/check-untracked.sh
# Warns when Claude Code stops and there are untracked files in .claude/skills or scripts

cd "$CLAUDE_PROJECT_DIR" || exit 0

# Get untracked files in directories we care about
untracked=$(git ls-files --others --exclude-standard -- \
  .claude/skills/ \
  scripts/ \
  src/ \
  2>/dev/null)

if [ -n "$untracked" ]; then
  count=$(echo "$untracked" | wc -l)
  # Output JSON to block the stop and show the warning
  cat <<EOF
{
  "decision": "block",
  "reason": "⚠️  $count untracked file(s) that will be LOST if you do branch operations:\n$(echo "$untracked" | head -10 | sed 's/^/  - /')\n\nRun: git add <files> && git commit -m 'save work'"
}
EOF
  exit 0
fi

# Nothing untracked in important dirs — let Claude stop normally
echo '{"decision": "approve"}'
exit 0