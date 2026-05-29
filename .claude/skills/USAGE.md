# Skills Usage Guide

Skills are specialized prompts that give Claude Code domain-specific knowledge about this project. Invoke them with `/<skill-name>` in the chat.

## Quick Reference

**Workflow / orchestration:**

| Skill | Command | When to Use |
|-------|---------|-------------|
| Start Ticket | `/start-ticket` | Branch from `ar/develop`, comment on Jira, transition to In Progress |
| Implement Ticket | `/implement-ticket` | Full end-to-end ticket flow: branch → BRD/Jira context → code → tests → PR (with resume) |
| Task From Story | `/task-from-story` | Create BE task(s) from Jira story key(s), inheriting parent and linking via Relates |
| Create Tickets | `/create-tickets` | Batch-create tickets from a BRD `Planning.md` table |
| Commit and Push | `/commit-and-push` | Stage, pre-commit, commit, and push changes |
| Create PR | `/create-pr` | End-to-end PR: stage → commit → push → Azure DevOps PR → Jira update |
| Review Code | `/review-code` | Self-review local changes (bugs, security, N+1, conventions) |
| Review PR | `/review-pr` | Review an Azure DevOps PR and post inline comments |
| Resolve PR | `/resolve-pr` | Mark fixed PR comment threads as resolved |
| PR Description | `/pr-description` | Generate a PR description from your changes |

**Authoring / domain helpers:**

| Skill | Command | When to Use |
|-------|---------|-------------|
| BRD Planner | `/brd-planner` | Analyze a BRD and generate Planning/Findings/Major-Changes/Questions |
| Planning with Files | `/planning-with-files` | Define the canonical `dev/memory/<task>/` file format for multi-step tasks |
| DRF Conventions | `/drf-conventions` | Create or modify DRF endpoints, serializers, views |
| Django Expert | `/django-expert` | Architecture decisions, debugging, Celery, multi-tenant |
| N+1 Detector | `/n-plus-one-detector` | Audit a view/queryset/serializer for missing prefetch |
| Test Generator | `/test-generator` | Scaffold pytest tests for a view or endpoint |
| Skill Developer | `/skill-developer` | Create new skills or work with hooks |

**Primitive libraries** (internal, `user-invokable: false` — called by the workflow skills above, not typed as slash commands): `jira-bot`, `azure-devops-bot`, `send-chat`.

---

## /brd-planner

**Purpose:** Analyze a Business Requirement Document and generate structured planning files.

**Usage:**
```
/brd-planner [paste BRD text or file path]
```

**What it does:**
1. Researches existing codebase for reusable patterns
2. Generates 4 files in `dev/brd/<brd-name>/`:
   - `Planning.md` — tickets, story points, daily allocation
   - `Findings.md` — risks, contradictions, assumptions
   - `Major-Changes.md` — architectural impact, API changes
   - `Questions.md` — blocking/high/medium priority questions

**Tips:**
- Estimates assume Claude Code does the implementation (days, not weeks)
- Plans favor extending existing code over creating new services
- One sprint = 3 weeks in this project

---

## /planning-with-files

**Purpose:** Organize and track progress on complex tasks using persistent markdown files.

**Usage:**
```
/planning-with-files add bulk export endpoint for claims
```

**What it does:**
1. Creates `dev/<task-name>/` folder (kebab-case)
2. Generates 3 files:
   - `task_plan.md` — phased plan with checkboxes
   - `findings.md` — research discoveries, file map
   - `progress.md` — session log
3. Tracks progress across sessions (survives `/clear`)

**When to use:**
- New endpoints (View + Service + Repository + Serializer + Tests)
- Multi-step bug fixes requiring research
- Refactors spanning multiple files
- Anything requiring >5 tool calls

**When to skip:**
- Simple questions, single-file edits, quick lookups

**Session recovery:** If you `/clear` and come back, invoke `/planning-with-files` again — it detects unfinished plans and resumes.

---

## /drf-conventions

**Purpose:** Get exact import paths, patterns, and recipes for writing DRF code in this project.

**Usage:**
```
/drf-conventions
```

Then ask Claude to create/modify an endpoint. The skill loads:
- Step-by-step endpoint creation order (Repository → Service → Serializer → View → URL)
- Import paths for `BaseARView`, `CustomResponse`, `CustomException`, permissions, serializer bases
- List view pattern with pagination + filtering
- URL wiring chain (`AR/urls.py` → `EPP/v1/urls.py` → app-level)
- Swagger/OpenAPI patterns
- Serializer base class choices (when to use `CamelCaseSerializer` vs `CustomSerializer`)

**Example workflow:**
```
> /drf-conventions
> Create a new GET endpoint to list claim notes for a claim
```

---

## /django-expert

**Purpose:** Get architecture guidance, debugging help, and patterns for Django-specific work.

**Usage:**
```
/django-expert
```

Then ask your question. The skill loads:
- "Where does this code go?" decision framework
- `select_related` vs `prefetch_related` decision tree
- Error handling patterns (`CustomException` usage)
- Tenant context rules (API vs Celery vs management commands vs tests)
- Service layer pattern (stateless, `@staticmethod`, `@transaction.atomic`)
- Repository layer pattern (`setattr` loop, `bulk_update_with_history`)
- Celery task pattern (bind, max_retries, tenant context, exponential backoff)
- S3/Redis/Email patterns
- Common gotchas (tenant context in Celery, QueryDict multi-value, bulk ops without history)

**Example workflow:**
```
> /django-expert
> How should I handle a Celery task that needs to update claims across all tenants?
```

---

## /n-plus-one-detector

**Purpose:** Audit a specific view or queryset for missing `select_related`/`prefetch_related`.

**Usage:**
```
> /n-plus-one-detector
> Check ClaimRecordMyTaskAPIView.get for N+1 queries
```

**What it does:**
1. Traces the full path: View → Service → Repository → Serializer
2. Maps every relationship the serializer accesses
3. Compares against what the repository prefetches
4. Reports gaps with severity (HIGH/MEDIUM/LOW)
5. Suggests exact repository fix

**Severity levels:**
- **HIGH** — triggered on every item in a list endpoint (guaranteed N+1)
- **MEDIUM** — triggered on detail endpoints or conditionally
- **LOW** — triggered rarely or mitigated by annotation

---

## /test-generator

**Purpose:** Generate pytest test files following project conventions.

**Usage:**
```
> /test-generator
> Write tests for ClaimNoteAPIView
```

**What it generates:**
- Class-based test structure with `@pytest.mark.django_db`
- `autouse=True` setup fixture with domain headers and API clients
- Tests for: success, permission denial, validation error, not found, invalid state
- Proper `tenant_context()` wrapping for direct DB assertions
- Correct fixtures from the project's fixture library

**Key conventions it follows:**
- Real DB only (no mocks)
- Arrange-Act-Assert pattern
- CamelCase in response assertions (snake_case in Python)
- `format="json"` for POST/PATCH
- Assert both response AND database state

---

## /review-code

**Purpose:** Self-review your local code changes before pushing — catches bugs, security gaps, missing audit fields, N+1 queries, and convention violations that linters miss.

**Usage:**
```
> /review-code             # review staged changes (default)
> /review-code --unstaged  # review unstaged changes
> /review-code --all       # review all changes vs HEAD
```

**What it checks:**
- Code quality (logic errors, dead code, stale comments)
- Django/DRF rules (business logic in views, DB access in serializers, missing `select_related`)
- Security (cross-client access, IDOR, missing auth checks)
- Data integrity (missing `created_by`, duplicate validation gaps, unique constraint mismatches)
- Project conventions (file placement, docstrings, `# todo` comments)
- Test coverage gaps (missing 409/404/403/400 test cases)

**Difference from `/review-pr`:** This reviews your **local working tree**. `/review-pr` reviews a remote PR on Azure DevOps and posts inline comments.

**Example workflow:**
```
> /drf-conventions                # write the code
> /review-code --staged           # self-review before pushing
> /commit-and-push                # push with confidence
> /create-pr                      # create the PR
```

---

## /pr-description

**Purpose:** Generate a reviewer-friendly PR description from your current changes.

**Usage:**
```
> /pr-description
```

**What it does:**
1. Detects diff source (feature branch vs staged changes)
2. Extracts ticket ID from branch name (`RCVR-` pattern)
3. Generates PR title (`<type>(RCVR-XXXX): <description>`)
4. Generates PR body with:
   - Ticket link (Jira)
   - Summary with warning flags (migration, permission changes, new endpoint)
   - Changes tagged by layer (Repository, Service, View, Model)
   - API Changes table (if endpoints changed)
   - Test Plan grounded in actual test code

**Note:** This repo uses Azure DevOps, not GitHub. The skill outputs markdown for copy-paste or `az repos pr create`.

---

## /start-ticket

**Purpose:** Start work on a Jira ticket by creating a properly named branch from `ar/develop` and commenting the branch name on the Jira ticket.

**Usage:**
```
> /start-ticket RCVR-1234
> /start-ticket RCVR-1234 fix
```

**What it does:**
1. Verifies you're on `ar/develop` (offers to switch if not)
2. Pulls latest `ar/develop`
3. Asks for a short description and optional type (defaults to `feat`)
4. Creates branch: `<type>/<RCVR-XXXX>-<description>` (e.g., `feat/RCVR-1234-add-claim-export`)
5. Pushes branch with upstream tracking
6. Adds a comment on the Jira ticket with the branch name

**Example workflow:**
```
> /start-ticket RCVR-1900
> Description: add bulk export endpoint
> Type: feat (default)
→ Branch: feat/RCVR-1900-add-bulk-export-endpoint
→ Jira commented with branch name
```

---

## /task-from-story

**Purpose:** Scaffold backend task ticket(s) from existing Jira user stories — inherits the story's parent epic and links the new task via `Relates`.

**Usage:**
```
> /task-from-story RCVR-2308
> /task-from-story RCVR-2308 RCVR-2311
> /task-from-story RCVR-2308 --type Bug
> /task-from-story RCVR-2308 --no-parent
> /task-from-story RCVR-2308 --title "[BE] Custom title"
```

**What it does:**
1. Fetches each story (summary, parent, description) via `acli`
2. Derives a `[BE]` title (strips `[Enhancement]`/`[FE]`/etc. prefixes)
3. Distills BE-relevant scope from the story's user-story + acceptance criteria
4. Creates a `Task` (or `Bug`) with the **same parent** as the story
5. Adds a `Relates` link from the new task to the source story
6. Skips sprint assignment by default

**Flags:**
- `--type <Task|Bug>` — work item type (default `Task`)
- `--no-parent` — skip parent inheritance
- `--title "<...>"` — override derived title (single-story mode only)

**When to use:**
- A PM/lead has filed a user story; you need a BE task to track and ship the backend portion
- Multiple related stories need backend tickets in one shot

**When NOT to use:**
- For a one-off ad-hoc ticket unrelated to a story → use `/jira-bot` directly
- For tickets from a BRD plan → use `/create-tickets`

---

## Skill Activation Hooks

Skills are automatically suggested when you read/edit relevant files:

| File Pattern | Skill Suggested |
|---|---|
| `v1/views/`, `v1/serializers/`, `v1/urls.py`, `v1/filters/` | `/drf-conventions` |
| `repository/` | `/n-plus-one-detector` |
| `tests/test_*` | `/test-generator` |
| `tests/fixtures/` | `/test-generator` |
| `v1/service/`, `tasks/`, `celery` | `/django-expert` |
| `models/`, `models.py` | `/django-expert` |
| `migrations/` | `/django-expert` |
| `middleware`, `permissions`, `settings` | `/django-expert` |
| `dev/brd/` | `/brd-planner` |
| `dev/*/task_plan.md`, `findings.md`, `progress.md` | `/planning-with-files` |

## Combining Skills

Skills work best when combined in a natural workflow:

```
1. /start-ticket         → Create branch from ticket, notify Jira
2. /brd-planner          → Analyze requirements, generate tickets
3. /planning-with-files  → Break down implementation, track progress
4. /drf-conventions      → Build the endpoint (loaded automatically via hook)
5. /n-plus-one-detector  → Verify query optimization
6. /test-generator       → Generate tests
7. /review-code          → Self-review before pushing (catches what linters miss)
8. /create-pr            → Commit, push, and create PR
```
