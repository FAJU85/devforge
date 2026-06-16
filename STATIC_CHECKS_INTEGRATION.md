# Static Checks Integration Guide

This guide shows how to integrate the new static validation rules into your development workflow and CI/CD pipeline.

## What Was Created

### 1. **`.semgrep.yml`** - Professional Semgrep Rules
Industry-standard rules in Semgrep format. Can be used with professional CI/CD tools.

**When to use:**
- Professional/enterprise CI/CD (GitHub Actions, GitLab CI, Jenkins)
- Team environments with shared CI infrastructure
- When you want automated enforcement in code review

**Installation:**
```bash
# Install Semgrep
pip install semgrep

# Run checks
semgrep --config .semgrep.yml

# Run in CI with failure
semgrep --config .semgrep.yml --error
```

### 2. **`scripts/validate-rules.py`** - Native Python Validator
Standalone Python script with no external dependencies.

**When to use:**
- Quick local checks before committing
- Development without Semgrep installed
- Testing/verification in restricted environments
- CI systems that don't support Semgrep

**Usage:**
```bash
# Quick check
python scripts/validate-rules.py

# Verbose output showing all issues
python scripts/validate-rules.py --verbose

# Show detailed fix suggestions
python scripts/validate-rules.py --verbose | less
```

### 3. **`STATIC_CHECKS_GUIDE.md`** - Rules Documentation
Complete reference of all rules, what they catch, and how to fix violations.

---

## Integration Steps

### Step 1: Configure Git Hooks (Pre-commit)

Add to `.git/hooks/pre-commit`:

```bash
#!/bin/bash
# Run validation before commit
python scripts/validate-rules.py
if [ $? -ne 0 ]; then
    echo "❌ Static checks failed. Run --verbose for details."
    exit 1
fi
```

Enable with:
```bash
chmod +x .git/hooks/pre-commit
```

### Step 2: Add to Makefile

```makefile
validate:
	python scripts/validate-rules.py --verbose

validate-fix:
	python scripts/validate-rules.py --fix

ci: validate lint test
	@echo "✅ All checks passed"
```

Usage:
```bash
make validate        # Check for violations
make validate-fix    # Auto-fix where possible
```

### Step 3: GitHub Actions Integration

Create `.github/workflows/static-checks.yml`:

```yaml
name: Static Checks

on: [push, pull_request]

jobs:
  validate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Run static validation
        run: python scripts/validate-rules.py --verbose

      - name: Run Semgrep (if installed)
        run: |
          pip install semgrep
          semgrep --config .semgrep.yml --error || true
```

### Step 4: IDE Configuration

**VS Code:**
Add to `.vscode/settings.json`:

```json
{
  "python.linting.enabled": true,
  "python.linting.pylintEnabled": false,
  "[python]": {
    "editor.defaultFormatter": "ms-python.python",
    "editor.formatOnSave": true,
    "editor.codeActionsOnSave": {
      "source.organizeImports": true
    }
  },
  "tasks.runTasks": ["validate-on-save"]
}
```

**PyCharm:**
- Settings → Tools → Python Integrated Tools → Testing → Pytest
- Run `python scripts/validate-rules.py` before commit

---

## Rules Summary

| Rule | Severity | Checks For | Fix Time |
|------|----------|-----------|----------|
| `avoid-fake-metrics` | WARNING | Hardcoded numbers without command execution | 2 min |
| `verify-before-claiming-complete` | WARNING | "Done" claims without verification | 5 min |
| `no-unverified-subagent-claims` | WARNING | Subagent reports relied on as facts | 10 min |
| `no-silent-failures` | WARNING | Exceptions swallowed without logging | 2 min |
| `distinguish-states` | INFO | Vague status terms (use: written/wired/verified) | 1 min |
| `no-orphaned-imports` | INFO | Imports without try/except or proof of wiring | 3 min |
| `no-placeholder-docs` | INFO | PHASE_*_COMPLETE.md style files | Deletion |
| `test-coverage-for-new-code` | INFO | New functions without tests | 10 min |

---

## Workflow Examples

### ✅ Passing Check

```python
# Measure, verify, then report
import subprocess
import time

start = time.time()
result = expensive_operation()
elapsed = (time.time() - start) * 1000

# Verify it worked
if result.success:
    print(f"Operation completed in {elapsed:.2f}ms (measured)")
    return True
else:
    print(f"Operation failed: {result.error}")
    return False
```

**Validation:**
- ✅ Metrics come from actual execution
- ✅ No claims without verification
- ✅ Errors are logged

### ❌ Failing Checks (Before Fix)

```python
# Multiple violations
print("✅ Feature working")  # ❌ No verification
print("Improved by 50%")      # ❌ No measurement
try:
    setup()
except:
    pass                       # ❌ Silent failure
```

### ✅ Fixed Version

```python
# Proper error handling and verification
try:
    result = setup()
    assert result is not None
    print("feature working (verified)")
except Exception as e:
    print(f"[ERROR] Setup failed: {e}")
    _SETUP_AVAILABLE = False
```

---

## Using in Code Review

When reviewing PRs, you can reference these rules:

**Comment on PR:**
```
⚠️ This appears to violate the `verify-before-claiming-complete` rule.
Before claiming the feature is "working," please:
1. Run the relevant tests
2. Show the test output
3. Then report the verified result

See STATIC_CHECKS_GUIDE.md for details.
```

---

## Monitoring & Metrics

The validator can produce metrics:

```bash
# Count issues by severity
python scripts/validate-rules.py --verbose | grep "WARNING:" | wc -l

# Track improvement over time
python scripts/validate-rules.py > validation-$(date +%Y-%m-%d).log

# Generate trend report
diff validation-2026-06-01.log validation-2026-06-15.log
```

---

## Troubleshooting

### "ImportError: No module named 'semgrep'"

Use the native validator instead:
```bash
python scripts/validate-rules.py --verbose
```

### "Rule not triggering on obvious violation"

Patterns have limitations. Use manual code review for complex cases:
- Semgrep catches structural patterns, not logic errors
- Some violations require human judgment
- False positives can happen; review results carefully

### "Too many INFO-level warnings"

Configure CI to only fail on WARNING:
```bash
python scripts/validate-rules.py --verbose | grep "WARNING" || true
```

---

## Next Steps

1. **Immediate:** Run `python scripts/validate-rules.py` to establish baseline
2. **This week:** Set up git hook `pre-commit`
3. **This sprint:** Add to CI/CD pipeline
4. **Ongoing:** Review violations in sprint retrospectives

---

## Questions?

Refer to:
- **CLAUDE.md** - Core project rules (what violations prevent)
- **STATIC_CHECKS_GUIDE.md** - Complete rule documentation
- **`.semgrep.yml`** - Rule definitions and patterns
- **`scripts/validate-rules.py`** - Implementation details
