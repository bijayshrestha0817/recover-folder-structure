# Hook Mechanisms

## Table of Contents
- [Hook Types](#hook-types)
- [PreToolUse (Current System)](#pretooluse-current-system)
- [Hook Registration](#hook-registration)
- [Exit Code Behavior](#exit-code-behavior)
- [Other Hook Types](#other-hook-types)
- [Performance Considerations](#performance-considerations)

---

## Hook Types

Claude Code supports hooks at different lifecycle points:

| Hook | When It Fires | Input (stdin) | Output (stdout) |
|---|---|---|---|
| `PreToolUse` | Before a tool executes | `{"tool_name": "...", "tool_input": {...}}` | `{"systemMessage": "..."}` to inject context |
| `PostToolUse` | After a tool executes | `{"tool_name": "...", "tool_input": {...}, "tool_result": "..."}` | Feedback to Claude |
| `UserPromptSubmit` | User submits a prompt | `{"prompt": "..."}` | Injected as context |
| `Stop` | After Claude finishes responding | `{"stop_reason": "..."}` | Shown as follow-up context |

---

## PreToolUse (Current System)

This project uses a **PreToolUse** hook on `Edit|Write` to suggest skills based on file paths.

### Flow

```
Claude calls Edit or Write tool
    |
settings.json triggers PreToolUse hook (matcher: "Edit|Write")
    |
skill-activation.sh reads tool input JSON from stdin
    |
Extracts file_path using grep + sed (no external deps)
    |
Pattern-matches file_path against known directory patterns
    |
Outputs {"systemMessage": "..."} if any pattern matched
```

### The Dispatcher Script

The central dispatcher is `.claude/hooks/skill-activation.sh`. It:

1. Reads JSON from stdin
2. Extracts `file_path` using pure bash (`grep` + `sed`)
3. Runs a series of `grep -qE` checks against the path
4. Accumulates suggestions into a `$SUGGESTIONS` string
5. Outputs a single `{"systemMessage": "..."}` JSON object

Each pattern block follows this structure:

```bash
if echo "$FILE_PATH" | grep -qE '<pattern>'; then
  SUGGESTIONS="${SUGGESTIONS}Use /<skill-name> for <context>. "
fi
```

---

## Hook Registration

Hooks are registered in `.claude/settings.json`:

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Edit|Write",
        "hooks": [
          {
            "type": "command",
            "command": "\"$CLAUDE_PROJECT_DIR\"/.claude/hooks/skill-activation.sh",
            "timeout": 5
          }
        ]
      }
    ]
  }
}
```

### Fields

| Field | Description |
|---|---|
| `matcher` | Regex to match tool names — `Edit\|Write` triggers on file edits/writes |
| `type` | Always `"command"` for shell hooks |
| `command` | Shell command to execute. `$CLAUDE_PROJECT_DIR` is the project root |
| `timeout` | Max execution time in seconds |

---

## Exit Code Behavior

| Exit Code | Effect |
|---|---|
| `0` | Success — stdout is used as context |
| `non-0` | Hook failed — stderr shown as error, tool call may be blocked |

For PreToolUse, a non-zero exit code **blocks** the tool call. Use this for guardrails:

```bash
if echo "$FILE_PATH" | grep -qE 'migrations/'; then
  echo "BLOCKED: Do not edit migration files directly" >&2
  exit 1
fi
```

---

## Other Hook Types

### PostToolUse

Runs after a specific tool completes. Good for validation after edits.

```json
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Edit|Write",
        "hooks": [
          {
            "type": "command",
            "command": "bash $CLAUDE_PROJECT_DIR/.claude/hooks/post-edit-check.sh"
          }
        ]
      }
    ]
  }
}
```

### Stop Hook

Runs after Claude finishes responding. Good for linting or type-checking.

```json
{
  "hooks": {
    "Stop": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "ruff check . 2>&1 | head -20"
          }
        ]
      }
    ]
  }
}
```

---

## Performance Considerations

- **Timeout**: Set `"timeout": 5` (seconds) to prevent hangs
- **No external deps**: Use pure bash — no `jq`, `python`, `node`
- **Early exit**: Check conditions and `exit 0` as soon as possible
- **Minimal I/O**: Avoid reading files unless necessary
- **Single script**: All file-path patterns live in one script to avoid spawning multiple processes
