---
name: review-pr
description: Review a pull request and apply the resulting changes. Reviews the PR diff for bugs, security, N+1, convention violations, and missing tests, AND reads human reviewer comments on the PR, then implements the fixes across the layered architecture, verifies (pytest + pre-commit), commits/pushes to the PR branch, and replies to / resolves the review threads. Triggers on "review pr", "review the pull request", "address pr comments", "apply review feedback", "fix the pr", or "/review-pr". Works locally (branch-vs-base diff) with no GitHub access, and uses GitHub (gh CLI or GH_TOKEN) when available.
user-invokable: true
argument-hint: '[<pr-number|url> | --local | --no-push]'
---

# review-pr — Review a PR and apply the changes

Reviews a pull request and then makes the changes the review calls for. Two
review sources are combined: (1) an **automated review** of the diff, and
(2) **human reviewer comments** on the PR (when GitHub is reachable).

CLAUDE.md covers the layered architecture and boundaries. This skill defines the
review→apply→verify→ship loop. It **delegates** code work to the specialist skills.

## When to Use
- "review the PR and fix what it finds"
- "address the review comments on PR #N"
- After a teammate reviews your PR and you want the requested changes applied.

## Flags / Argument
| Arg | Meaning |
|-----|---------|
| `<pr-number>` or PR URL | Target that PR on GitHub. |
| (none) | Target the current branch's PR if GitHub is reachable; else local diff. |
| `--local` | Force local mode: review `base...HEAD` diff, ignore GitHub. |
| `--no-push` | Apply + verify + commit, but do not push or reply on the PR. |

## Step 1 — Resolve the target
1. If a PR ref is given, use it. Else try the current branch's PR (see GITHUB.md).
2. Determine `base` (PR base branch, default `main`) and `head` (PR branch / current branch).
3. Get the diff:
   - GitHub mode: the PR's diff (see [GITHUB.md](GITHUB.md)).
   - Local mode: `git diff <base>...HEAD` and `git diff` (uncommitted) — review both.

## Step 2 — Detect GitHub access
Check in order: `gh` on PATH (`command -v gh`), then `GH_TOKEN`/`GITHUB_TOKEN` env.
- **Available** → GitHub mode: can fetch reviewer comments, push, and reply/resolve threads.
- **Unavailable** → local mode: auto-review only; still applies, verifies, commits (and
  pushes the branch if a remote/upstream exists), but cannot read or reply to PR comments.
Announce which mode is active.

## Step 3 — Gather review inputs (BOTH sources)
1. **Automated review** — review the diff for: correctness bugs, security, N+1 queries,
   DRF/convention violations, and missing tests. Reuse **`review-code`** (or `/code-review`)
   to produce findings; don't hand-roll a parallel checklist.
2. **Human reviewer comments** (GitHub mode) — fetch unresolved review threads and
   review-summary comments (see [GITHUB.md](GITHUB.md)). Capture: file, line, comment body,
   thread/comment id (needed to reply/resolve later), author.

## Step 4 — Build one actionable list
Merge both sources into a single, deduped, severity-tagged list. For each item record:
`source` (auto | reviewer), `file:line`, `what to change`, `why`, and (if reviewer) the
`thread/comment id`. Drop pure-opinion comments that request no change; note them as
"acknowledged, no change" so they can still get a reply.

## Step 5 — Apply the changes (layered, delegated)
Implement each actionable item respecting the architecture:
- Multi-step / cross-layer change → plan with **`planning-with-files`** first.
- Views / serializers / services → follow **`drf-conventions`**.
- New/changed behavior → add or update tests via **`test-generator`**.
- Query/N+1 fixes → repository layer only, per **`n-plus-one-detector`**.
Keep each fix minimal and on-point to the comment/finding. Do not opportunistically
refactor unrelated code.

## Step 6 — Verify (never skip)
- `python -m pytest student_management/tests/ -q` → must pass; quote the count.
- `pre-commit run --all-files` (or on changed files) → ruff / ruff-format / mypy must pass.
- If anything fails, fix and re-run before shipping. No "should pass".

## Step 7 — Ship (per apply-scope = push + reply)
Unless `--no-push`:
1. **Never on `main`.** Confirm `head` is a feature branch (you are usually on `dev`).
2. Commit with a message summarizing what the review asked for and what changed.
   End the commit body with the Co-Authored-By line from the harness git rules.
3. Push to the PR branch.
4. **GitHub mode** — for each addressed reviewer thread, post a reply noting how it was
   handled (e.g. "Fixed in <short-sha>: <one line>") and resolve the thread; post one
   summary comment listing auto-review fixes too. See [GITHUB.md](GITHUB.md).
5. **Local / no GitHub** — print the same per-item summary to the user instead of posting.

## Step 8 — Record (if zero memory exists)
If `dev/memory/zero/` exists, append a `TIMELINE.md` entry (PR #, what was addressed,
test result, pushed sha) and refresh `STATE.md`.

## Rules
1. **Two sources, one list** — always combine auto-review + reviewer comments (when reachable);
   never silently ignore human comments.
2. **Apply only what the review asks** — minimal, targeted edits; no unrelated refactors.
3. **Verify before shipping** — pytest + pre-commit green, quoted. Mandatory.
4. **Never push to `main`**; branch if needed. Never force-push.
5. **Reply honestly** — only mark a thread resolved if the change actually addresses it;
   if you disagree or it needs a human decision, reply asking, leave it open.
6. **Secrets/auth** — read GitHub token from env only; never print or commit it.
7. **Delegate, don't duplicate** — review-code, drf-conventions, test-generator,
   n-plus-one-detector, planning-with-files do the heavy lifting.
8. **GitHub failures degrade gracefully** — if a fetch/reply call fails, fall back to local
   mode and tell the user; never block the apply+verify on a network call.
