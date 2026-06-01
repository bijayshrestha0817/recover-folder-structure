# GitHub Mechanics for review-pr

Concrete commands for the GitHub-mode steps. Prefer `gh`; fall back to the REST/GraphQL
API via `curl` with a token. Detect repo as `OWNER/REPO` from the `origin` remote:

```bash
git remote get-url origin
# https://github.com/bijayshrestha0817/recover-folder-structure.git
# -> OWNER=bijayshrestha0817  REPO=recover-folder-structure
```

Token (curl fallback): read `GH_TOKEN` or `GITHUB_TOKEN` from env. Never print it.

```bash
AUTH="Authorization: Bearer ${GH_TOKEN:-$GITHUB_TOKEN}"
API="https://api.github.com/repos/$OWNER/$REPO"
```

## 1. Resolve the PR for the current branch

```bash
# gh
gh pr view --json number,title,state,baseRefName,headRefName,url

# curl (by head branch)
BRANCH=$(git rev-parse --abbrev-ref HEAD)
curl -s -H "$AUTH" "$API/pulls?head=$OWNER:$BRANCH&state=open"
```

Extract `number` (PR id), `baseRefName` (base), `headRefName` (head).

## 2. Get the PR diff

```bash
# gh
gh pr diff <number>

# curl (unified diff)
curl -s -H "$AUTH" -H "Accept: application/vnd.github.v3.diff" "$API/pulls/<number>"
```

## 3. Fetch reviewer comments (the human-comment source)

Three relevant kinds — gather all:

```bash
# (a) Inline review comments (file/line threads)
gh api "repos/$OWNER/$REPO/pulls/<number>/comments" --paginate
#   curl: GET $API/pulls/<number>/comments
#   key fields per comment: id, path, line/original_line, body, user.login, in_reply_to_id

# (b) Review summaries (APPROVE / REQUEST_CHANGES / COMMENT bodies)
gh api "repos/$OWNER/$REPO/pulls/<number>/reviews" --paginate
#   key fields: id, state, body, user.login

# (c) Issue-level PR comments (general discussion)
gh api "repos/$OWNER/$REPO/issues/<number>/comments" --paginate
```

Keep each inline comment's `id` and `path:line` — needed to reply and resolve.

### Identify UNRESOLVED threads (GraphQL — REST can't tell resolved state)

```bash
gh api graphql -f query='
  query($owner:String!,$repo:String!,$num:Int!){
    repository(owner:$owner,name:$repo){
      pullRequest(number:$num){
        reviewThreads(first:100){
          nodes{ id isResolved isOutdated
            comments(first:20){ nodes{ databaseId path line body author{login} } } } } } } }' \
  -f owner=$OWNER -f repo=$REPO -F num=<number>
```

Only act on threads where `isResolved == false`. The thread `id` (node id) is used to resolve.

## 4. Reply to a review thread

```bash
# Reply to an inline comment thread (REST) — replies under comment <comment_id>
gh api -X POST "repos/$OWNER/$REPO/pulls/<number>/comments/<comment_id>/replies" \
  -f body="Fixed in <short-sha>: <one-line summary>."

# curl equivalent
curl -s -X POST -H "$AUTH" "$API/pulls/<number>/comments/<comment_id>/replies" \
  -d '{"body":"Fixed in <short-sha>: <one-line summary>."}'
```

## 5. Resolve a review thread (GraphQL mutation)

```bash
gh api graphql -f query='
  mutation($threadId:ID!){
    resolveReviewThread(input:{threadId:$threadId}){ thread{ isResolved } } }' \
  -f threadId="<thread_node_id>"
```

Only resolve threads whose requested change was actually applied. If you disagree or it
needs a human decision, reply with a question and leave it open.

## 6. Post one summary comment (auto-review fixes + overview)

```bash
gh api -X POST "repos/$OWNER/$REPO/issues/<number>/comments" \
  -f body="$(cat <<'EOF'
Applied review changes:
- <comment by @reviewer> → <fix> (<sha>)
- Auto-review: <finding> → <fix> (<sha>)

Tests: <X passed>. pre-commit: green.
EOF
)"
```

## 7. Push the branch

```bash
git push origin <headRefName>
```

## Failure handling
- Any `gh`/`curl` call fails (no auth, network, 404) → log it, fall back to **local mode**
  for the rest of the run, and tell the user. Never block the apply+verify+commit on a
  GitHub call.
- If neither `gh` nor a token is present, skip this file entirely — review-pr runs local-only.

## Installing gh (if the user wants GitHub mode and it's missing)
```bash
# Debian/Ubuntu/WSL
sudo apt update && sudo apt install gh
# then
gh auth login
```
Or set a token instead: `export GH_TOKEN=<personal-access-token>` (scope: repo).
