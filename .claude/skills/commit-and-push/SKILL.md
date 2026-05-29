---
name: commit-and-push
description: Stage, pre-commit, commit, and push changes to remote. Use when changes are ready to push but no PR is needed (e.g., PR already exists).
user-invokable: true
---

# Commit and Push

CLAUDE.md covers git conventions. This skill handles staging, pre-commit checks, committing, and pushing to the remote branch.

## Step 1: Check for Changes

```bash
git status --porcelain
```

- If there are **staged or unstaged changes** (output is non-empty), proceed to Step 2.
- If there are **no changes** (working tree is clean), **skip directly to Step 3** — everything is already committed.

## Step 2: Stage, Pre-commit & Commit

**Only execute this step if Step 1 detected changes.**

```bash
git status
git add <file1> <file2> ...
```

- Stage only files relevant to the current feature/fix
- **Never stage:** `.env`, credentials, `*.pyc`, IDE config, or files in `.gitignore`
- Prefer `git add <specific files>` over `git add .` or `git add -A`
- If unsure which files to include, ask the user before staging

### DRF nudge

After staging, check if any of the staged files match `v1/views/`, `v1/serializers/`, `repository/`, or `v1/service/`:

```bash
git diff --cached --name-only | grep -E '/v1/(views|serializers|service)/|/repository/'
```

If matches are found, suggest the user run `/review-code` first (it'll trigger `/n-plus-one-detector` automatically). Do NOT block — this is a soft nudge, not a gate. The user can decline and continue.

Then run pre-commit and commit:

```bash
pre-commit run
git commit -m "<type>(RCVR-XXXX): <description>"
```

- Commit message format is defined in CLAUDE.md — follow it exactly
- Scan branch name for `RCVR-` to discover the ticket ID; ask the user if not found
- Never skip pre-commit (`--no-verify` is forbidden)
- If pre-commit fails, fix the issues and create a **new** commit (never `--amend`)

## Step 3: Push

```bash
git push origin $(git branch --show-current)
```

- Skip if the remote branch is already up to date
- Never force push

## Step 4: Report

Output:
1. The branch name and commit hash
2. A one-line summary of what was pushed

---

## Rules

1. **Skip commit when clean** — if `git status --porcelain` is empty, skip staging and committing
2. **Never skip pre-commit** — run `pre-commit run` before committing
3. **Never force push** — use regular `git push` only
4. **Never commit to main** — always work on a feature branch
5. **Ask before staging** if the list of changed files is ambiguous
6. **No Claude attribution** — never add `Co-Authored-By: Claude`, `Generated with Claude Code`, or similar tags to commit messages
