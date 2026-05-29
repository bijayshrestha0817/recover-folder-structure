---
name: skill-developer
description: Create and manage Claude Code skills for this project. Use when creating new skills, understanding the activation system, working with hooks, debugging skill triggers, or implementing progressive disclosure. Covers SKILL.md structure, YAML frontmatter, PreToolUse hooks, and the 500-line rule.
user-invokable: true
---

# Skill Developer Guide

## Purpose

Guide for creating and managing skills in Claude Code in this project.

## System Overview

This project uses two distinct mechanisms:

1. **Skills** — `.claude/skills/{name}/SKILL.md` — full content invoked via `/skill-name` (when frontmatter has `user-invokable: true`) or referenced internally by other skills.
2. **PreToolUse hooks** — `.claude/hooks/*.sh` — small per-concern bash scripts that run before each tool use and inject `systemMessage` reminders or block tool calls. Each hook handles one concern (e.g., `migration-guard.sh`, `n-plus-one-check.sh`, `auto-lint.sh`). They are registered in `.claude/settings.json` under `hooks.PreToolUse`.

There is **no single dispatcher hook**. New "auto-suggest a skill on edit" behavior should be added as its own per-concern hook in `.claude/hooks/` and wired into `settings.json`.

---

## Creating a New Skill

### Step 1: Create the SKILL.md

Location: `.claude/skills/{skill-name}/SKILL.md`

```markdown
---
name: my-new-skill
description: Brief description including keywords that help Claude match this skill.
user-invokable: true
argument-hint: '[optional argument hint]'
---

# My New Skill

Short overview, including what other skill (if any) this one delegates to.

## When to Use
Specific scenarios.

## Step 1 / Step 2 / ...
The actual instructions.

## Rules
Guardrails the skill must follow.
```

**Frontmatter fields:**

| Field | Required | Description |
|---|---|---|
| `name` | Yes | Lowercase, hyphens (e.g., `my-new-skill`). Must match the directory name. |
| `description` | Yes | Used by Claude to match the skill against user intent. Include keywords. ≤1024 chars. |
| `user-invokable` | No | `true` to allow `/skill-name` invocation. **Set `false` for primitive libraries** (e.g., `jira-bot`, `azure-devops-bot`, `send-chat`) that other skills delegate to internally. |
| `argument-hint` | No | Hint for arguments shown when the user types `/skill-name`. |

### Step 2: Decide if a Hook Should Suggest It

If editing certain files should remind Claude to consider this skill, add a small hook in `.claude/hooks/` and wire it into `settings.json`. See the existing hooks for the pattern.

```bash
#!/bin/bash
# Example: .claude/hooks/my-new-hook.sh

INPUT=$(cat)
FILE_PATH=$(echo "$INPUT" | grep -o '"file_path"[[:space:]]*:[[:space:]]*"[^"]*"' | sed 's/.*"file_path"[[:space:]]*:[[:space:]]*"//;s/"//')
[ -z "$FILE_PATH" ] && exit 0

if echo "$FILE_PATH" | grep -qE '<your-pattern>'; then
  printf '{"systemMessage":"Editing <X>. Consider running /<your-skill>."}\n'
fi
exit 0
```

Then register in `.claude/settings.json` under `hooks.PreToolUse` (matcher `Edit|Write` for file-path-based hooks). Keep hook scripts small, single-concern, and under 5s — pure bash, no Python or jq.

### Step 3: Add Reference Files (Optional)

For skills with dense reference material, use progressive disclosure:

```
.claude/skills/my-skill/
├── SKILL.md           # Main content (under 500 lines)
├── PATTERNS.md        # Detailed patterns reference
└── EXAMPLES.md        # Extended examples
```

Reference from SKILL.md: `See [PATTERNS.md](PATTERNS.md) for the full list.`

Existing example: `django-expert/` has a `GOTCHAS.md` companion.

---

## Best Practices

### The 500-Line Rule

Keep SKILL.md under 500 lines. Move detailed reference material to separate sibling files. Long SKILLs are slow to load and bury the recipe.

### Delegate Primitives, Don't Duplicate

If your skill needs to call `acli`, `az repos pr`, `gh`, or send a chat message, **delegate to the corresponding primitive skill** instead of inlining the CLI syntax:

| Primitive | Skill |
|---|---|
| `acli jira ...` | `jira-bot` |
| `az repos pr ...` | `azure-devops-bot` |
| Google Chat send | `send-chat` |

Inlining means every primitive change (auth, flag rename, new ADF quirk) requires editing every caller. Delegation means one update propagates everywhere.

### Content Guidelines

- Reference real file paths from this project (e.g., `claims/v1/views/claim_record_api.py`).
- Open with "CLAUDE.md covers X — this skill provides Y" when relevant, to avoid restating project rules.
- Use clear headings, short lists, code blocks. Optimize for scanning.
- No emojis unless the user has asked for them in a writeup.

### Naming Convention

- Lowercase with hyphens: `my-skill-name`
- Verb-led / gerund preferred: `commit-and-push`, `start-ticket`, `task-from-story`.
- Match the domain: `drf-conventions` not `api-helper`.

### Avoid Duplication

- CLAUDE.md covers rules and boundaries — skills provide patterns and recipes.
- If two skills share content, extract to one and cross-reference.
- Reference files must not duplicate their parent SKILL.md.

---

## Project File Structure

```
.claude/
├── hooks/                      # Per-concern PreToolUse hooks (bash, single-concern, <5s)
│   ├── auto-lint.sh
│   ├── env-file-guard.sh
│   ├── fat-view-detector.sh
│   ├── import-sort.sh
│   ├── main-branch-guard.sh
│   ├── migration-guard.sh
│   ├── n-plus-one-check.sh
│   ├── tenant-context-reminder.sh
│   └── test-reminder.sh
├── settings.json               # Global config + hook registration
├── settings.local.json         # User-specific overrides (env vars, reviewers)
└── skills/
    ├── USAGE.md                # User-facing skill reference guide
    └── <skill>/
        ├── SKILL.md
        ├── (optional) reference *.md siblings
        └── (optional) scripts/
```

---

## Hook Mechanics

### Exit Code Behavior

| Exit Code | Effect |
|---|---|
| `0` | Success — stdout used as context (or empty for no message) |
| `non-0` | Hook failed — for PreToolUse, this **blocks** the tool call |

Use non-zero exits for guardrails:

```bash
if echo "$FILE_PATH" | grep -qE '/migrations/[0-9]'; then
  echo "BLOCKED: Do not edit migration files directly" >&2
  exit 1
fi
```

### Output Format

```bash
printf '{"systemMessage":"%s"}\n' "$MESSAGE"
```

### Performance Rules

- **Timeout:** 5 seconds in `settings.json`.
- **No external deps:** pure bash. No `jq`, `python`, `node`.
- **Early exit:** check conditions and `exit 0` as soon as possible.
- **Minimal I/O:** avoid reading files inside the hook.

---

## Troubleshooting

### Skill Not Found via `/skill-name`

1. Verify `SKILL.md` exists at `.claude/skills/{name}/SKILL.md`.
2. Check YAML frontmatter has `name:` matching the directory and `user-invokable: true`.
3. Verify the directory is not empty (Claude lists registered skills from frontmatter).

### Hook Not Firing

1. Confirm the hook is registered in `.claude/settings.json` under `hooks.PreToolUse`.
2. Test the script standalone:
   ```bash
   echo '{"file_path":"claims/v1/views/test.py"}' | bash .claude/hooks/<hook-name>.sh
   ```
3. Debug with trace:
   ```bash
   bash -x .claude/hooks/<hook-name>.sh <<< '{"file_path":"<path>"}'
   ```
4. Check the hook is executable (`chmod +x`).

### False Positives (Hook Suggesting Wrong Thing)

Make file path patterns more specific:

```bash
# Too broad — matches anywhere "service" appears in the path
grep -qE 'service'

# Better — matches only the service layer directory
grep -qE '/v1/service/'
```
