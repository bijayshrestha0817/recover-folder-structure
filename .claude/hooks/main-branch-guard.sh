#!/bin/bash
# Main Branch Guard — Prevent commits/pushes to protected branches

INPUT=$(cat)

COMMAND=$(echo "$INPUT" | grep -o '"command"[[:space:]]*:[[:space:]]*"[^"]*"' | sed 's/.*"command"[[:space:]]*:[[:space:]]*"//;s/"//')

if [ -z "$COMMAND" ]; then
  exit 0
fi

# Check for git commit on main/master
if echo "$COMMAND" | grep -qE 'git\s+(commit|push)' ; then
  CURRENT_BRANCH=$(git branch --show-current 2>/dev/null)
  if echo "$CURRENT_BRANCH" | grep -qE '^(main|master|ar/develop)$'; then
    printf '{"decision":"block","reason":"Cannot commit/push directly to %s. Create a feature branch first."}\n' "$CURRENT_BRANCH"
  fi
fi

exit 0
