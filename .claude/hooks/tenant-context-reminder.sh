#!/bin/bash
# Tenant Context Reminder — Remind to use tenant_context in Celery tasks

INPUT=$(cat)

FILE_PATH=$(echo "$INPUT" | grep -o '"file_path"[[:space:]]*:[[:space:]]*"[^"]*"' | sed 's/.*"file_path"[[:space:]]*:[[:space:]]*"//;s/"//')

if [ -z "$FILE_PATH" ]; then
  exit 0
fi

if echo "$FILE_PATH" | grep -qE '/tasks/.*\.py$|celery.*\.py$'; then
  printf '{"systemMessage":"Reminder: Celery tasks run outside request middleware. Wrap tenant-scoped DB operations in `tenant_context(tenant)`. See docs/Architecture-Reference.md for the pattern."}\n'
fi

exit 0
