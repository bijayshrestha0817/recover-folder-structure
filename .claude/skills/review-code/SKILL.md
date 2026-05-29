---
name: review-code
description: Self-review staged or unstaged code changes for bugs, security, N+1 queries, missing tests, and project convention violations. Use when asked to review code, review my changes, review the diff, or self-review before creating a PR.
user-invokable: true
argument-hint: '[--staged | --unstaged | --all]'
---

# Review Code (Self-Review)

Reviews local code changes (staged, unstaged, or both) for bugs, security issues, N+1 queries, and project convention violations. Unlike `/review-pr` which reviews remote PRs on Azure DevOps, this skill reviews **your local working tree** before you push.

## When to Use

- Before creating a PR (`/create-pr`)
- After writing code with `/drf-conventions` or `/implement-ticket`
- When the user asks to "review my code", "review changes", "self-review", or "check my diff"

## Step 1: Determine Scope

Parse the argument to decide what to diff:

| Argument | Git Command | Default |
|----------|------------|---------|
| `--staged` | `git diff --cached` | **Yes** (default if no arg) |
| `--unstaged` | `git diff` | |
| `--all` | `git diff HEAD` | |

Run `git diff --stat` (with the appropriate flag) first. If no changes, tell the user and stop.

## Step 2: Read the Diff

```bash
git diff [--cached|HEAD] -- <file>
```

For large diffs (>3000 lines), break down by file using `--name-only` first, then read each file's diff individually.

**Important:** Also read the full current version of each changed file (not just the diff) to understand context. Use the `Read` tool for new files and files with complex changes.

## Step 3: Analyze Every Changed File

Run through **all** checklist categories for **every** file. Do NOT skip files or categories.

### Mandatory: Run `/n-plus-one-detector` when DRF code is touched

If the diff includes any file under `v1/views/`, `v1/serializers/`, `repository/`, or `v1/service/`, you **must** invoke the full `/n-plus-one-detector` workflow on each affected endpoint. The Step 3.2 checklist below is a quick scan; the detector does the deep trace (view → service → repository → serializer + the SerializerMethodField red-flag table). Both run; the detector's findings feed back into the report from Step 4 with `Performance` category.

Skip the detector only when the diff is purely tests, docs, fixtures, configs, or non-DRF code.

### 3.1 Code Quality

- [ ] Logic errors, off-by-one, race conditions
- [ ] Missing error handling at system boundaries
- [ ] Unused imports, dead code, unreachable branches
- [ ] Naming clarity (variables, functions, classes)
- [ ] Stale comments that no longer match the code
- [ ] `validated_data` mutation via `.pop()` without copying

### 3.2 Django / DRF Specific

- [ ] Business logic in views (must be in service layer)
- [ ] Database access in serializers (forbidden)
- [ ] Missing `select_related`/`prefetch_related` (N+1 queries)
- [ ] Serializing a freshly-created instance without re-fetching with `select_related`
- [ ] Missing `@pytest.mark.django_db` on test classes
- [ ] Tenant context missing in Celery tasks
- [ ] Missing permissions or incorrect permission classes
- [ ] Missing `@extend_schema()` on view methods
- [ ] Missing `ordering` class attribute when using `OrderingFilter`
- [ ] Missing docstrings on new functions/classes

### 3.3 Security

- [ ] SQL injection, XSS, command injection
- [ ] Sensitive data exposure in responses
- [ ] Missing authentication/authorization checks
- [ ] Detail/update/delete endpoints not scoped to `client_id` (cross-client access)
- [ ] Lookup by PK without verifying ownership (IDOR)

### 3.4 Data Integrity

- [ ] Missing `created_by` / `updated_by` audit fields on create/update
- [ ] Missing duplicate validation before create AND update (check unique constraints)
- [ ] Unique constraint fields in model vs. fields checked in `get_existing_duplicate`
- [ ] Soft-delete `updated_by` not persisting (check if mixin `save()` uses `update_fields`)
- [ ] Empty PATCH body accepted without validation

### 3.5 Project Conventions (CLAUDE.md)

- [ ] File placement (views in `v1/views/`, services in `v1/service/`, repos in `repository/`)
- [ ] Import ordering (ruff isort)
- [ ] Line length (120 chars)
- [ ] Docstrings on all new functions/classes
- [ ] Enums defined as `models.TextChoices`
- [ ] `# todo` / `# hack` / `# fixme` comments that shouldn't ship

### 3.6 Test Coverage

- [ ] New service methods have corresponding test cases
- [ ] Duplicate/conflict paths tested (409)
- [ ] Not-found paths tested (404)
- [ ] Permission denied paths tested (403)
- [ ] Validation error paths tested (400)
- [ ] Both response structure AND database state asserted
- [ ] Soft-delete and reactivation flows tested

## Step 4: Report Findings

Present findings in a structured table, grouped by severity:

```markdown
## Code Review: <brief description>

### ACTIVE Issues (must fix)

| # | File | Line | Issue | Category |
|---|------|------|-------|----------|
| 1 | `/path/to/file.py` | 42 | Description | Security |

### CLOSED Issues (suggestions/nitpicks)

| # | File | Line | Issue | Category |
|---|------|------|-------|----------|
| 1 | `/path/to/file.py` | 10 | Description | Convention |

### Summary

| Severity | Count |
|----------|-------|
| Active (must fix) | X |
| Closed (suggestions) | Y |
```

**Category tags:** `Bug`, `Security`, `Performance`, `Convention`, `Data Integrity`, `Test Gap`, `Suggestion`

## Step 5: Offer Fixes

After presenting findings, ask:

> **Found X active issues and Y suggestions. Want me to fix any of them?**

If the user says "fix all" or "fix N", apply the fixes directly — do not just describe them.

## Rules

1. **Review ALL changed files** — never skip a file, even test fixtures or markdown
2. **Be thorough on the first pass** — the user should not need to run this twice to find all issues. Check every category for every file.
3. **No false positives** — only flag genuine issues. Read the actual code, don't guess.
4. **Use right-side line numbers** — reference line numbers in the new version of the file
5. **Cross-reference constraints** — when reviewing create/update logic, always check the model's `Meta.constraints` and `unique_together` to verify the duplicate check matches
6. **Verify audit fields** — on any create/update path, check that `created_by`, `updated_by`, `created_at`, `updated_at` are properly set
7. **Verify client scoping** — on any detail/update/delete endpoint, verify the query filters by `client_id` from the request
8. **Check the full chain** — for each endpoint, trace View → Service → Repository → Model to find gaps
9. **Don't repeat yourself** — if an issue was already reported and the user said "ignore" or "defer", don't flag it again
10. **Always invoke `/n-plus-one-detector`** when DRF files are in the diff (`v1/views/`, `v1/serializers/`, `repository/`, `v1/service/`) — the inline checklist is not a substitute for the detector's full trace
