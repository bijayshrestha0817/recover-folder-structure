---
name: create-pr
description: End-to-end PR workflow — stages files, commits, generates PR description via /pr-description, pushes, and creates an Azure DevOps PR targeting ar/develop. Use when asked to create a PR, submit changes, or ship a feature.
user-invokable: true
---

# Create PR

CLAUDE.md covers git conventions and architecture. This skill orchestrates the **full end-to-end workflow** from uncommitted changes to a live Azure DevOps PR, then updates the Jira ticket.

## Step 1: Stage, Commit & Push

Invoke `/commit-and-push` — it handles checking for changes, staging, pre-commit, committing, and pushing. If the working tree is clean and remote is up to date, it will skip automatically.

## Step 2: Check for Existing PR

Use azure-devops-bot's **Check for Existing PR** primitive with:
- source branch: `$(git branch --show-current)`
- target branch: `ar/develop`

If the JSON array is non-empty, a PR exists — extract `[0].pullRequestId` and build URL via the primitive's documented format.

- **If a PR already exists:** skip Steps 3 and 4. Use the existing PR URL and ID. Use **"PR Updated"** in Steps 6–7.
- **If no PR exists:** continue to Steps 3 and 4. Use **"PR Created"** in Steps 6–7.

## Step 3: Generate PR Description (skip if PR exists)

Invoke `/pr-description` — it handles all diff analysis, title generation, and body formatting. Capture the title and body output for Step 4.

## Step 4: Create Azure DevOps PR (skip if PR exists)

Use azure-devops-bot's **Create PR** primitive with:
- title: from Step 3
- description: from Step 3
- source branch: `$(git branch --show-current)`
- target branch: `ar/develop` (unless the user specifies otherwise)
- reviewers: split `$PR_REVIEWERS` (from `settings.local.json`) by comma

Extract `pullRequestId` and the PR URL from the response.

## Step 5: Update Jira Ticket

Extract the ticket ID from the branch name (e.g., `RCVR-1782`).

### 5a: Add PR Link

Use jira-bot's **Comment with a Clickable URL** primitive (under "Add Comment") to post the PR URL as a clickable link. Set:

- `LABEL` = `"PR:"`
- `URL` = the PR URL from Step 2 (existing) or Step 4 (new)
- `<TICKET-ID>` = the ticket ID extracted from the branch name

### 5b: Add QA Acceptance Criteria to "Acceptance Criteria 1" Field

Analyze the diff from Step 3 (or the full diff if the PR already existed) and generate acceptance criteria for QA engineers. **Append** the criteria to the ticket's `Acceptance Criteria 1` custom field (`customfield_10096`) — NOT to the description, and NOT as a comment. The description is the source-of-truth for what was asked; QA criteria belong in the dedicated field.

The helper script preserves the existing ADF in the field — if it already has content it's appended after a horizontal-rule separator; if empty the field is set to the new content.

**Steps:**

1. Write the markdown criteria (see format below) to a temp file.
2. Run the helper:

```bash
JIRA_EMAIL="<your-atlassian-email>" \
JIRA_BASE_URL="https://eclathealthsolutions.atlassian.net" \
python .claude/skills/jira-bot/scripts/jira_append_acceptance_criteria.py "<TICKET-ID>" --markdown-file "<temp-file-path>"
```

`JIRA_API_TOKEN` is loaded from `.claude/settings.local.json`.

Or pipe via stdin instead of `--markdown-file`:

```bash
JIRA_EMAIL="<your-atlassian-email>" \
JIRA_BASE_URL="https://eclathealthsolutions.atlassian.net" \
python .claude/skills/jira-bot/scripts/jira_append_acceptance_criteria.py "<TICKET-ID>" <<'EOF'
- Verifiable scenario covering the happy path, with expected outcome
- Edge case: boundary, empty, invalid input
- Permission case: which role can/cannot do this
- Regression check: existing feature still works
EOF
```

The script prints `appended Acceptance Criteria 1 on <TICKET-ID>.` (or `set ...` if the field was empty) on success.

**How to generate criteria:** Review every changed file in the diff and produce one short, testable scenario per bullet.

**Format:** Acceptance Criteria 1 is a legacy textarea field — its renderer outputs plain text, not rich text. **Emit a flat hyphen-prefixed bullet list. One sentence per bullet. No titles, no section headers, no bold, no headings, no code blocks, no multi-line snippets.** The script joins consecutive `- item` lines into a single paragraph with hard breaks so they render tightly without blank lines between items.

```markdown
- <Happy path: action and expected outcome, single line>
- <Edge case: boundary, empty, or invalid input — single line>
- <Permission case: which role can/cannot do this>
- <Regression: an existing feature that must still work>
- <If the change is BE: name the affected endpoint inline, e.g. "PATCH /api/v1/claims/{id}/ returns 200 with new field">
```

**Rules for criteria:**
- Write from the QA engineer's perspective — they don't read code, they test via UI/API.
- Each bullet is **one sentence**. State the action AND the expected outcome inline.
- For BE-only changes, name the endpoint and HTTP method inline (e.g. `"PATCH /api/v1/claims/{id}/ with {…} returns 200"`). Don't paste sample request/response bodies — those go in the description, not AC1.
- Cover at minimum: happy path, one edge case, one permission case, one regression check.
- For config/migration/non-functional changes, state what to eyeball (e.g. `"Verify existing claims still load after the new column is added"`).
- Do NOT include `---`, `##`, `**bold**`, or fenced code blocks — they leak through as literal `----` / `h2.` / `*text*`.
- Do NOT include a leading `---` rule in the markdown — the helper inserts the separator automatically when appending.

### 5c: Transition Ticket

Use jira-bot's **Transition Work Item** primitive with status `"In Review"` (title-case — `acli` is case-sensitive).

- If the ticket ID cannot be found in the branch name, ask the user for it.
- If the command fails, show the error and point the user to `docs/cli-setup.md`.

## Step 6: Notify via Google Chat

After the PR is created, send a review notification using the `send-chat` skill (primitive — `user-invokable: false`, called internally) with this message format:

```
<mention-tags>

PR Created <TICKET-ID>

PR: <PR-URL>

Jira: https://eclathealthsolutions.atlassian.net/browse/<TICKET-ID>
Branch: <source-branch> -> <target-branch>
Author: <git-author-name>
```

- **Build mention tags** from `$CHAT_REVIEWERS` (comma-separated Google Chat user IDs in `settings.local.json`). Split by comma and format each as `<users/ID>` separated by spaces. Example: `<users/107743332125081496843> <users/110331625397678032928>`
- Replace placeholders:
  - `<TICKET-ID>` — Jira ticket extracted from branch (e.g., `RCVR-1798`)
  - `<PR-URL>` — PR link from Step 2 (existing) or Step 4 (new)
  - `<source-branch>` — current git branch
  - `<target-branch>` — target branch (default `ar/develop`)
  - `<git-author-name>` — from `git config user.name`
- Use **"PR Created"** for new PRs or **"PR Updated"** if the PR already existed

## Step 7: Report

Output the same structured format shown to the user:

```
PR Created <TICKET-ID>

PR: <PR-URL>

Jira: https://eclathealthsolutions.atlassian.net/browse/<TICKET-ID>
Branch: <source-branch> -> <target-branch>
Author: <git-author-name>
```

Also confirm:
1. Jira ticket was commented and moved to "IN REVIEW"
2. Google Chat notification was sent

---

## Rules

1. **Delegate git operations to /commit-and-push** — do not duplicate staging, committing, or pushing logic
2. **Delegate PR description to /pr-description** — do not write it manually or restate its logic
3. **Target branch is `ar/develop`** unless the user says otherwise
4. **Always update Jira** — add PR link comment and transition to "IN REVIEW" after PR creation
