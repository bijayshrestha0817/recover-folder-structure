# Trigger Types — File Path Pattern Guide

## Table of Contents
- [How Patterns Work](#how-patterns-work)
- [ERE Syntax Basics](#ere-syntax-basics)
- [Pattern Examples by Layer](#pattern-examples-by-layer)
- [Testing Patterns](#testing-patterns)
- [Best Practices](#best-practices)

---

## How Patterns Work

The PreToolUse hook extracts `file_path` from the tool input JSON and matches it against Extended Regular Expressions (ERE) using `grep -qE`.

```bash
if echo "$FILE_PATH" | grep -qE '<pattern>'; then
  SUGGESTIONS="${SUGGESTIONS}Use /<skill-name> for <context>. "
fi
```

The file path is the **absolute or relative path** of the file being edited/written. Patterns should match directory segments, not full paths.

---

## ERE Syntax Basics

| Syntax | Meaning | Example |
|---|---|---|
| `(a\|b)` | Alternatives | `(views/\|serializers/)` |
| `.` | Any single character | `models.py` matches `models.py` |
| `.*` | Any characters between | `v1/.*_api\.py` |
| `[abc]` | Character class | `model[s]?` |
| `\.` | Literal dot | `urls\.py` |

---

## Pattern Examples by Layer

### Views / Serializers / URLs (DRF)
```bash
grep -qE '(v1/views/|v1/serializers/|v1/urls\.py|v1/filters/)'
```

### Repositories (N+1 Detection)
```bash
grep -qE '/repository/'
```

### Tests
```bash
grep -qE '/tests/test_'
```

### Test Fixtures
```bash
grep -qE '/tests/fixtures/'
```

### Services / Celery Tasks
```bash
grep -qE '(v1/service/|tasks/|celery)'
```

### Models
```bash
grep -qE '(/models/|models\.py)'
```

### Migrations
```bash
grep -qE '/migrations/'
```

### Infrastructure
```bash
grep -qE '(middleware|permissions|settings)'
```

### Planning Files
```bash
grep -qE 'dev/brd/'
grep -qE 'dev/[^/]+/(task_plan|findings|progress)\.md'
```

---

## Testing Patterns

### Test a single pattern
```bash
echo "claims/v1/views/claim_record_api.py" | grep -qE '(v1/views/|v1/serializers/)' && echo "MATCH" || echo "NO MATCH"
```

### Test the full hook
```bash
echo '{"file_path":"claims/v1/views/claim_record_api.py"}' | bash .claude/hooks/skill-activation.sh
```

### Batch test multiple paths
```bash
for path in \
  "claims/v1/views/claim_api.py" \
  "claims/repository/claim_repository.py" \
  "claims/tests/test_claim_api.py" \
  "README.md"; do
  echo -n "\"$path\" → "
  result=$(echo "{\"file_path\":\"$path\"}" | bash .claude/hooks/skill-activation.sh)
  echo "${result:-(no match)}"
done
```

---

## Best Practices

1. **Match directory segments, not filenames** — `v1/views/` is better than `_api.py`
2. **Use alternation for related paths** — `(v1/views/|v1/serializers/)` covers the DRF layer
3. **Avoid overly broad patterns** — `service` matches `customer_service_api.py`; use `v1/service/` instead
4. **Test with real file paths from the project** — use paths from `git ls-files`
5. **Keep patterns simple** — complex regex is hard to debug and maintain
6. **One suggestion per skill** — don't suggest the same skill from multiple pattern blocks
