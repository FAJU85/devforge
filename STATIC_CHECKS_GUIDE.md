# Static Checks & Guardrails Analysis

This document describes the static rules (Semgrep) created to prevent recurring errors identified from the project's CLAUDE.md and git history.

## Analysis Summary

Based on CLAUDE.md and observed patterns in commits, the following categories of errors were recurring:

### 1. **Claims Without Verification** (Most Critical)
**Pattern:** Reporting features as "done" without actually verifying they work  
**Impact:** High - Wastes time and erodes trust  
**Rule:** `verify-before-claiming-complete`, `no-unverified-subagent-claims`

Examples from commits:
- Claiming tests pass without showing output
- Saying "feature added" when only a file was created
- Relying on subagent success reports without independent verification

**Static Check:**
```yaml
verify-before-claiming-complete:
  - Detects: print("✅ ... complete")
  - Enforces: Must show command output proving verification
```

### 2. **Fabricated Metrics** (Hard Rule #1)
**Pattern:** Reporting numbers (latency, percentages, error rates) without running commands  
**Impact:** Critical - Directly violates CLAUDE.md rule 1  
**Rule:** `avoid-fake-metrics`

**Static Check:**
```yaml
avoid-fake-metrics:
  - Detects: Any hardcoded numeric claims in output/returns
  - Enforces: Numbers must come from actually executed commands
```

### 3. **Orphaned Code** (Hard Rule #2)
**Pattern:** Creating files/modules that aren't imported into the running app  
**Impact:** High - Code exists but isn't wired, leading to false "done" claims  
**Rule:** `no-orphaned-imports`

Examples:
- Creating `api/services/new_service.py` without importing it in `main.py`
- Lazy imports without verification that they're actually used
- Files on disk but unreachable in the running application

**Static Check:**
```yaml
no-orphaned-imports:
  - Detects: New imports without verification
  - Enforces: Code must be actually used in main.py
```

### 4. **State Confusion** (Hard Rule #3)
**Pattern:** Conflating "written" (file exists) with "wired" (imported) with "verified" (tested)  
**Impact:** Medium - Leads to imprecise status reporting  
**Rule:** `distinguish-states`, `distinguish-import-vs-wired`

**Static Check:**
```yaml
distinguish-states:
  - Detects: Generic "done", "complete", "working" claims
  - Enforces: Must use: written | wired | verified
```

### 5. **Silent Failures** (Implicit Anti-Pattern)
**Pattern:** Catching exceptions and ignoring them  
**Impact:** Medium - Hides bugs and makes debugging harder  
**Rule:** `no-silent-failures`

**Static Check:**
```yaml
no-silent-failures:
  - Detects: try/except with pass or silent continue
  - Enforces: Errors must be logged/reported
```

### 6. **Placeholder Documentation** (Hard Rule #5)
**Pattern:** Creating `PHASE_X_COMPLETE.md`, `FEATURE_Y_DONE.md` style files  
**Impact:** Low - Clutters repo with describing work instead of documenting behavior  
**Rule:** `no-placeholder-docs`

**Static Check:**
```yaml
no-placeholder-docs:
  - Detects: Files named PHASE_*_COMPLETE.md or VERSION_*_DONE.md
  - Enforces: Documentation describes verified behavior only
```

### 7. **Missing Test Coverage** (Implicit Hard Rule)
**Pattern:** Writing new code without corresponding tests  
**Impact:** High - Untested code breaks silently  
**Rule:** `test-coverage-for-new-code`

**Static Check:**
```yaml
test-coverage-for-new-code:
  - Detects: New functions without test_* counterparts
  - Enforces: New code must have tests that prove it works
```

### 8. **Unhandled Imports** (Best Practice)
**Pattern:** Direct imports without try/except for optional features  
**Impact:** Medium - Causes cryptic failures in certain environments  
**Rule:** `import-error-must-be-handled`

**Static Check:**
```yaml
import-error-must-be-handled:
  - Detects: "from X import Y" without error handling
  - Enforces: Optional features wrapped in try/except
```

---

## Using the Static Checks

### Installation

The Semgrep rules are already in `.semgrep.yml`.

### Running Checks Locally

```bash
# Install Semgrep
pip install semgrep

# Run all checks
semgrep --config .semgrep.yml

# Run specific rule
semgrep --config .semgrep.yml --include-rule verify-before-claiming-complete

# Run with auto-fix (for some rules)
semgrep --config .semgrep.yml --autofix
```

### In CI/CD Pipeline

Add to your CI workflow:

```bash
semgrep --config .semgrep.yml --error
```

This will fail the build if any critical rules are violated.

### IDE Integration

Most IDEs support Semgrep plugins. Configure to run on save:

```json
{
  "semgrep.config": ".semgrep.yml",
  "semgrep.level": "warning"
}
```

---

## Rule Severity Levels

| Severity | Meaning | Action |
|----------|---------|--------|
| **ERROR** | Blocks deployment | Fix before committing |
| **WARNING** | Should be reviewed | Fix before merging |
| **INFO** | Best practice suggestion | Address when convenient |

---

## Mapping Rules to CLAUDE.md Hard Rules

| CLAUDE.md Rule | Semgrep Rule(s) | Severity |
|---|---|---|
| 1: Never invent metrics | `avoid-fake-metrics` | WARNING |
| 2: Never relay subagent reports | `no-unverified-subagent-claims` | WARNING |
| 3: Distinguish written/wired/verified | `distinguish-states` | INFO |
| 4: Prefer vertical slices | _(requires human judgment)_ | - |
| 5: No celebration docs | `no-placeholder-docs` | INFO |
| 6: Verify subagent results | `no-unverified-subagent-claims` | WARNING |

---

## Common Fixes

### ❌ Before (Fails Checks)
```python
# Claims without verification
print("✅ Feature working")

# Orphaned code
from api.services.new_service import execute
_NEW_SERVICE_AVAILABLE = True

# Fake metrics
print(f"Latency improved by 45%")

# Silent failure
try:
    setup_cache()
except Exception:
    pass
```

### ✅ After (Passes Checks)
```python
# Verify before claiming
import subprocess
result = subprocess.run(["pytest", "tests/test_feature.py"], capture_output=True)
if result.returncode == 0:
    print("feature working (verified)")
else:
    print(f"feature failed: {result.stderr.decode()}")

# Wire the code
from api.services.new_service import execute
_NEW_SERVICE_AVAILABLE = True
# Verify in main.py that this import is used

# Report only measured metrics
import time
start = time.time()
result = expensive_operation()
latency_ms = (time.time() - start) * 1000
print(f"Latency: {latency_ms:.2f}ms (measured)")

# Handle errors explicitly
try:
    setup_cache()
except Exception as e:
    print(f"[WARN] Cache setup failed: {e}")
    _CACHE_AVAILABLE = False
```

---

## Integration Workflow

1. **Before committing:** Run `semgrep --config .semgrep.yml`
2. **Before pushing:** Fix any WARNING or ERROR level violations
3. **In code review:** Reviewer can point to specific rule violations
4. **In CI:** Build fails if rules are broken
5. **During coding:** IDE shows suggestions in real-time

---

## Extending Rules

To add more rules based on new patterns:

```yaml
- id: my-new-rule
  pattern: <pattern>
  message: |
    Explanation of the rule and how to fix it.
  languages: [python, javascript]
  severity: WARNING
```

See [Semgrep docs](https://semgrep.dev/docs/writing-rules/overview) for pattern syntax.

---

## Limitations

These rules catch **structural** anti-patterns but cannot:
- Verify business logic is correct
- Check if the implementation matches requirements
- Ensure tests are good quality (only presence)
- Validate that imports are actually used (requires data flow analysis)

For those, rely on human code review and testing.

---

## References

- CLAUDE.md: Project working agreement and hard rules
- Semgrep: https://semgrep.dev/docs/
- Pattern syntax: https://semgrep.dev/docs/writing-rules/pattern-syntax/
