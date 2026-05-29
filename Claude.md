# AGENTS.md — OmniDial Platform (v1.2, 2026-03-15)

Enterprise Omnichannel Contact Center | Demo + MVP Phases | AI Agent Team

---

## RULE 0 - THE FUNDAMENTAL OVERRIDE PEROGATIVE

If I tell you to do something, even if it goes against what follows below, YOU MUST LISTEN TO ME. I AM IN CHARGE, NOT YOU.

---

## RULE 1 — ABSOLUTE: NO DELETIONS

- NEVER delete files/directories without explicit per-session approval for the exact command.
- This includes files you just created. If unsure, ask first.
- Forbidden without explicit approval: `git reset --hard`, `git clean -fd`, `rm -rf`, any destructive command.
- Prefer safe tools: `git status`, `git diff`, `git stash`, backups.
- After approval: restate command, list effects, wait for confirmation.

---

## Project Structure & File Safety

Repository layout and file classification (sacred/generated/development): See [`docs/agents-reference.md`](docs/agents-reference.md#repository-layout).

---

## Mandatory Skills

These skills MUST be used proactively. Do not wait for the user to ask.

### /maitri-memory -- Session Continuity (ALWAYS)

**Every session, every agent, no exceptions.**

1. **Session start:** Run `/maitri-memory` to load or create a memory file
2. **Before each step:** Read the memory file for current context
3. **After each action:** Update the memory file (progress log, files modified)
4. **After architectural changes:** Update `docs/ARCHITECTURE_REFERENCE.md` (API routes, DB schema, config, directory structure)
5. **Session end:** Run `/maitri-memory` to save session summary

Memory files live in `docs/memory/<task-name>-<YYYY-MM-DD>.md`. The architecture reference is the single source of truth for how the system is structured.

### /frontend-design -- UI/UX Implementation

**Use WHEN** building or modifying any user-facing page or component.

- Uses shadcn/ui + Tailwind CSS + Lucide React icons (adjust to your stack)
- Follow your project's design system and branding guidelines

### Available Project Skills

All skills live in `.claude/skills/` and are auto-detected. Use proactively when the trigger matches.

| Skill | Trigger | Description |
|-------|---------|-------------|
| `/maitri-memory` | Every session (mandatory) | Persistent task memory + architecture reference maintenance |
| `/frontend-design` | UI/UX work (mandatory) | Production-grade frontend interfaces with shadcn/ui + Tailwind |
| `/software-taste` | Any code writing, review, or architecture task | Enforces architectural taste, complexity management, deep modules, and changeability principles |
| `/bug-report` | "bug report", "create bug", "file bug" | Investigate bugs and create structured bug beads with Jira sync |
| `/database-schema-designer` | Schema design, migrations, indexing | Design robust SQL/NoSQL schemas with normalization and performance optimization |
| `/product-requirements` | PRD creation, feature specification | Interactive requirements gathering with quality scoring and PRD generation |
| `/weekly-summary` | "weekly summary", "status report" | Generate semi-technical weekly project summaries for clients |

---


## Agent Mail

Agents coordinate via MCP Agent Mail (identities, inbox, file reservations, threads). Register with `macro_start_session`, reserve files before editing, use `thread_id="BMO-<N>"`. Full guide: [`docs/tools/agent-mail-reference.md`](docs/tools/agent-mail-reference.md).

---

## Development Workflow

### Branching Strategy

```
main (production — human-controlled releases only)
  └── develop (integration branch — PR merges only)
        ├── feature/BMO-123-auth-endpoint (Backend Dev)
        ├── feature/BMO-124-login-page (Frontend Dev)
        └── feature/BMO-125-e2e-tests (QA Agent)
```

- **`main`** is production. Only the human merges `develop → main` for releases.
- **`develop`** is the integration branch. Always deployable to staging.
- **Feature branches** are created off `develop` using convention: `feature/BMO-<number>-<task-title-truncated>` where `BMO-<number>` comes from the bead's `external_ref` field (the Jira ticket ID). Use `br show <bead-id> --json | jq -r '.[0].external_ref'` to read it.
- Agents MUST NOT push directly to `main` or `develop` — only to feature branches via PRs.

### Worktree Isolation

Dev agents share a single repository clone. To prevent branch clobbering, each agent uses a **git worktree** for its feature branch. The main repo stays on `develop` at all times.

```bash
JIRA_ID=$(br show <bead-id> --json | jq -r '.[0].external_ref')
BRANCH="feature/${JIRA_ID}-<short-title>"
git fetch origin develop
git worktree add ../omnidial-worktrees/${BRANCH} -b ${BRANCH} origin/develop
cd ../omnidial-worktrees/${BRANCH}
```

After merge: `git worktree remove ../omnidial-worktrees/${BRANCH}`

### Commit Convention

Format: `<type>: <description> [BMO-<N>]`. Types: feat/fix/refactor/test/docs/chore/style. Imperative mood. Full details + examples: [`docs/agents-reference.md#commit-convention`](docs/agents-reference.md#commit-convention).

### Agent Roster

| Agent | Domain | Ownership | Model |
|---|---|---|---|
| Backend Dev | FastAPI, Python | `backend/**`, `alembic/**` | Sonnet |
| Frontend Dev | Next.js, React | `frontend/**` | Sonnet |
| DevOps | AWS, Terraform/Terragrunt, CI/CD, cloud security | `infra/**`, `.github/**`, `Dockerfile*`, `compose*.yml` | Sonnet |
| QA Agent | Testing & QA | `qa/**` (read-only elsewhere) | Opus 4.6 |
| Team Lead | Review & architecture | Read-only | Opus |

Register via `macro_start_session` with `project_key="/data/projects/omnidial-platform"` and `agent_name` at session start. Agent names: `team-lead`, `backend-dev`, `frontend-dev`, `devops`, `qa`. After registering, each agent introduces itself to the team via Agent Mail (see `team/*.md` Section 3).

### Lifecycle

Full details per role in `team/*.md` Sections 3-4. Overview: `br ready` → claim bead → send `task_picked_up` notification → worktree → reserve files → develop → PR to `develop` → review → merge → release reservations → close bead → cleanup. Thread ID: `BMO-<N>`.

After completing a task, check `br ready -t task --json` for bug beads — bugs are priority over new features. Notify QA after fix merges.

### Task Pickup Checklist (exact commands)

When picking up a new task, the Dev/QA Agent completes these steps **in order**:

```bash
# 1. Claim the bead
br update <bead-id> --status in_progress --assignee "<role>" --json
```

```bash
# 2. Send chat notification (creates the task thread — ALL subsequent notifications thread under this)
python3 -m notifications task_picked_up <bead-id> --agent-name "<role>"
```

```bash
# 3. Create worktree (ONLY after notification is sent)
JIRA_ID=$(br show <bead-id> --json | jq -r '.[0].external_ref')
BRANCH="feature/${JIRA_ID}-<short-title>"
git fetch origin develop
git worktree add ../omnidial-worktrees/${BRANCH} -b ${BRANCH} origin/develop
cd ../omnidial-worktrees/${BRANCH}
```

```bash
# 4. Reserve files via Agent Mail
file_reservation_paths(project_key="/data/projects/omnidial-platform", agent_name=<your-name>, paths=["<your-domain>/**"], ttl_seconds=3600, exclusive=true, reason="Working on BMO-<number>")
```

```bash
# 5. Notify team via Agent Mail
send_message(
  project_key="/data/projects/omnidial-platform", sender_name=<your-name>,
  to=[<team-lead>],
  subject="Picked up: BMO-XXX - Task Title",
  body_md="Starting work on BMO-XXX. Branch: feature/BMO-XXX-short-title",
  thread_id="BMO-XXX"
)
```

**CRITICAL:** Step 2 creates the chat thread that ALL subsequent notifications (PR created, approved, merged, completed) reply to. Skipping it breaks the entire notification chain for this task.

### Merge & Close Checklist (exact commands)

After Team Lead approval, the Dev Agent completes these steps:

```bash
# 1. Wait for EXPLICIT human approval before merging
#    Present the approved PR to the human and STOP. Do NOT merge until the human says "merge" or "go ahead".
#    The human may want to review the PR themselves, delay the merge, or give additional instructions.

# 2. Merge the PR (ONLY after human confirms)
gh pr merge <number> --merge

# 3. Send chat notification
python3 -m notifications pr_merged <bead-id> --pr-number <N> --pr-url "<url>" --merge-commit "<sha>"
```
```bash
# 4. Release file reservations
release_file_reservations(project_key="/data/projects/omnidial-platform", agent_name=<dev-agent>)

# 5. Close the bead (DB-only — no flush)
br comments add <bead-id> "Merged to develop. PR #XX closed. Commit: <sha>"
br close <bead-id> --reason "Completed and merged" --json
```
```bash
# 6. Send chat notification (includes project status + next tasks)
python3 -m notifications task_complete <bead-id>

# 7. Clean up worktree
cd /data/projects/omnidial-platform
git worktree remove ../omnidial-worktrees/${BRANCH}
```
```bash
# 8. Notify Team Lead + QA via Agent Mail
send_message(
  project_key="/data/projects/omnidial-platform", sender_name=<dev-agent>,
  to=[<team-lead>, <qa-agent>],
  subject="Merged: BMO-XXX - Task Title",
  body_md="PR #XX merged to develop. Bead closed.\nTeam Lead: please flush beads and sync to Jira.\nQA: check `br ready -t task` for newly unblocked QA tasks.",
  thread_id="BMO-XXX"
)
```

*(Do NOT run `br sync --flush-only` — Team Lead handles beads flush on `develop`.)*

### Notifications

ALL lifecycle events MUST trigger chat notifications (`python3 -m notifications <event> <bead-id> ...`). `task_picked_up` MUST be first (creates thread). Full event table: [`docs/agents-reference.md#notification-events`](docs/agents-reference.md#notification-events). See also `notifications/README.md`.

### Self-Healing Hooks

Two hooks run automatically — on tool failure (`SELF-HEALING`) and on premature stop (blocking with fix instructions). After 3 retries of the same error, try a fundamentally different approach. See `team/*.md` for details.

### Audit Trail

Every bead must have complete audit comments (pickup, PR, review, merge). QA bugs need: report, approval, assigned dev, fix PR. Details: [`docs/agents-reference.md#audit-trail-requirements`](docs/agents-reference.md#audit-trail-requirements).

### Beads Flush Protocol

Only Team Lead runs `br sync --flush-only` on `develop`. All other agents: DB-only ops only. Never flush in worktrees.

**Allowed DB-only operations (all agents):** `br update`, `br close`, `br comments add`, `br create`, `br label`.

Team Lead flush procedure: `team/team-lead.md` Section 4.

---

## Issue Tracking

All tracking via `br` (beads_rust). No TODO lists or other trackers. Key: `br ready -t task` to find work, DB-only ops (no flush). Full reference: [`docs/agents-reference.md#beads-reference`](docs/agents-reference.md#beads-reference).

## CLI Quick Reference

Common CLI mistakes and correct syntax: [`docs/agents-reference.md#cli-quick-reference`](docs/agents-reference.md#cli-quick-reference).

---

## Tools

- **bv**: [`docs/tools/bv-reference.md`](docs/tools/bv-reference.md) — **CRITICAL: Use ONLY `--robot-*` flags. Bare `bv` blocks session.**
- **UBS**: [`docs/tools/ubs-reference.md`](docs/tools/ubs-reference.md) — Run `ubs <changed-files>` before every commit.
- **cass**: [`docs/tools/cass-reference.md`](docs/tools/cass-reference.md) — **NEVER run bare `cass`**. Use `--robot`/`--json` only.
- **Agent Mail**: [`docs/tools/agent-mail-reference.md`](docs/tools/agent-mail-reference.md) — Multi-agent coordination.

---

## Session Completion

1. Run quality gates (tests,linters,builds) if code changed
2. Update bead status — `br update`/`br close`/`br comments add` (DB-only — no flush)
3. Commit docs/ changes — `git add docs/memory/ docs/ARCHITECTURE_REFERENCE.md` (skip if no changes; do NOT flush beads)
4. Push to remote — `git pull --rebase && git push && git status` (MUST show "up to date")
5. Hand off context for next session

Full checklist per role: `team/*.md` Section 9.

**CRITICAL:** NEVER stop before pushing. NEVER say "ready to push when you are" — YOU must push.

---

## Agent Capabilities & Constraints

### What Agents CAN Do

- Read any file in the codebase for context
- Create and edit code in feature branches
- Run tests and verify functionality
- Coordinate via file locks and Agent Mail
- Claim tasks and update status in beads
- Create new documentation files
- Propose architectural changes (with justification)

### What Agents MUST NOT Do

- Edit `AGENTS.md` without explicit instruction (only document discoveries)
- Edit `CLAUDE.md` (user instructions only)
- Push directly to `main` or `develop` branches (use feature branch + PR workflow)
- Make breaking changes to database schema without migration plan
- Ignore performance testing requirements
- Skip code review approval

### Model Selection Guidelines

| Task | Model | Reasoning |
|------|-------|-----------|
| Read docs, quick questions | Haiku | Fast, cheap |
| Code implementation, testing | Sonnet | Balanced capability/cost |
| Architecture review, debugging | Opus | Deep reasoning, complex analysis |
| Security review | Opus | Highest scrutiny |

---

## Reference

- **Glossary**: [`docs/agents-reference.md#glossary`](docs/agents-reference.md#glossary)
- **Escalation**: [`docs/agents-reference.md#escalation`](docs/agents-reference.md#escalation)
- **Project plan**: `docs/project-plan.md`
- **Technical design**: `docs/omnidial-technical-design.md`

---

*v1.2 | 2026-03-15 | ACTIVE — all agents reference this document*
