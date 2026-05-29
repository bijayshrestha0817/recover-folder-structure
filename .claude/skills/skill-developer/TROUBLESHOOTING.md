# Troubleshooting Skills & Hooks

## Table of Contents
- [Skill Not Suggested When Editing](#skill-not-suggested-when-editing)
- [Skill Not Found via /skill-name](#skill-not-found-via-skill-name)
- [False Positives](#false-positives)
- [Hook Not Executing](#hook-not-executing)
- [Debugging Commands](#debugging-commands)

---

## Skill Not Suggested When Editing

### Symptom
You edit a file that should trigger a skill suggestion, but no suggestion appears.

### Checklist

1. **Is the hook registered in settings.json?**
   ```bash
   cat .claude/settings.json
   ```
   Verify the `PreToolUse` entry exists with matcher `Edit|Write`.

2. **Does the file path match the pattern?** Test directly:
   ```bash
   echo "your/file/path.py" | grep -qE '(your|pattern)' && echo "MATCH" || echo "NO MATCH"
   ```

3. **Is the pattern in skill-activation.sh?** Check the script has a block for your file path pattern.

4. **Test the hook standalone:**
   ```bash
   echo '{"file_path":"your/file/path.py"}' | bash .claude/hooks/skill-activation.sh
   ```

---

## Skill Not Found via /skill-name

### Symptom
Typing `/skill-name` doesn't activate the skill.

### Checklist

1. **SKILL.md exists?** Verify: `ls .claude/skills/{name}/SKILL.md`
2. **YAML frontmatter correct?** Must have `name:` field matching what you type after `/`
3. **`user-invokable: true`?** Without this flag, the skill won't respond to `/name` invocation
4. **Frontmatter syntax valid?** Must be between `---` delimiters at the very top of the file

---

## False Positives

### Symptom
A skill is suggested when editing unrelated files.

### Fixes

1. **Make the pattern more specific:**
   ```bash
   # Too broad — matches any path containing "service"
   grep -qE 'service'

   # Better — matches only the versioned service layer
   grep -qE 'v1/service/'
   ```

2. **Add path anchoring:**
   ```bash
   # Matches "tests" anywhere in path
   grep -qE 'tests'

   # Better — matches the tests directory specifically
   grep -qE '/tests/test_'
   ```

---

## Hook Not Executing

### Symptom
No output at all — not even errors.

### Checklist

1. **Verify settings.json is valid JSON:**
   ```bash
   python3 -c "import json; json.load(open('.claude/settings.json'))"
   ```

2. **Test the script directly:**
   ```bash
   echo '{"file_path":"claims/v1/views/test.py"}' | bash .claude/hooks/skill-activation.sh
   ```

3. **Run with debug trace:**
   ```bash
   bash -x .claude/hooks/skill-activation.sh <<< '{"file_path":"claims/v1/views/test.py"}'
   ```

4. **Check $CLAUDE_PROJECT_DIR:** This variable is set by Claude Code at runtime. For manual testing:
   ```bash
   CLAUDE_PROJECT_DIR=$(pwd) bash .claude/hooks/skill-activation.sh <<< '{"file_path":"test.py"}'
   ```

5. **Check timeout:** If the script takes > 5 seconds, it's killed silently.

---

## Debugging Commands

### Test the full hook pipeline
```bash
echo '{"file_path":"claims/v1/views/my_api.py"}' | bash .claude/hooks/skill-activation.sh
```

### Run with debug output
```bash
bash -x .claude/hooks/skill-activation.sh <<< '{"file_path":"claims/v1/views/test.py"}'
```

### List all registered skills
```bash
echo "=== SKILL.md skills ==="
ls .claude/skills/*/SKILL.md 2>/dev/null

echo "=== Frontmatter ==="
for f in .claude/skills/*/SKILL.md; do
  echo "--- $f ---"
  sed -n '2,/^---$/p' "$f" | head -5
done
```

### Verify hook output is valid JSON
```bash
echo '{"file_path":"claims/v1/views/test.py"}' | bash .claude/hooks/skill-activation.sh | python3 -m json.tool
```
