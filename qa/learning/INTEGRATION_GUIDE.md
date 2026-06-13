# QA Learning System - Complete Integration Guide

A fully autonomous, production-ready system that learns from test failures and provides intelligent recommendations.

## 🎯 System Overview

This system **automatically**:
- Captures real test failures from Playwright and Vitest
- Learns patterns from failure messages and stack traces
- Persists patterns across test runs  
- Provides intelligent suggestions for fixes
- Visualizes patterns in an interactive dashboard
- Updates patterns on a schedule

**Zero configuration needed** - reporters are already wired into:
- `playwright.config.ts` → captures E2E failures
- `vitest.config.ts` → captures unit/integration failures

## 🚀 Quick Start (5 minutes)

### 1. Run Tests (Auto-Captures Failures)

```bash
npm run test:unit
npm run test:e2e
```

Failures are automatically recorded to `failures/` directory.

### 2. Extract Patterns

```bash
npm run qa:learn
```

Output:
```
Processing 28 unlearned failures...
✓ Learned 62 patterns
✓ Persisted to qa/learning/learned_patterns.json  
✓ Marked 28 failures as learned
```

### 3. View Dashboard

```bash
npm run qa:dashboard
```

Opens live dashboard at http://localhost:3333 showing:
- Pattern statistics and distribution
- Top patterns by occurrence
- Real-time refresh every 30 seconds

### 4. Get Intelligent Suggestions

```bash
npm run qa:suggest
```

Shows pattern matches for most recent failure with:
- Relevance score
- Confidence level  
- Actionable solutions
- Related failures

## 📊 System Architecture

```
┌─────────────────────────────────────────┐
│     Test Execution (Playwright/Vitest)  │
└──────────────────┬──────────────────────┘
                   │
         [Reporters capture failures]
                   │
           ▼───────▼──────┐
    failures/ directory    │
     (28 JSON files)       │
                           │
       [npm run qa:learn]───┘
           │
    ▼──────▼─────────┐
  Pattern Learning   │
  & Extraction       │
           │         │
    [PatternMatcher  │
     persists to     │
     learned_patterns.json]
           │         │
     ◄─────▼─────────┘
     
    learned_patterns.json (62 patterns)
     ┌────────────┬──────────────┬────────────┐
     │            │              │            │
  (API)        (API)        (API)         (API)
     │            │              │            │
   Suggester  Dashboard      CLI Report    Cron
     │            │              │            │
  Intelligent   Visual      Metrics &      Auto-
  Recommendations  Analysis  Insights      Update
```

## 📋 Complete Command Reference

### Learn & Analyze

```bash
npm run qa:learn              # Extract patterns from failures
npm run qa:report            # Show comprehensive learning report
npm run qa:suggest           # Get suggestions for most recent failure
npm run qa:suggest <id>      # Get suggestions for specific failure by ID
```

### Manage Failures

```bash
npm run qa:failures          # List recent failures
npm run qa:failures:stats    # Show failure statistics by category
npm run qa:failures:collect  # Record a sample failure (demo)
npm run qa:failures:clear    # Clear all failures and start fresh
```

### Services & Background

```bash
npm run qa:dashboard         # Start web dashboard (localhost:3333)
npm run qa:cron             # Auto-learn every 30 minutes  
npm run qa:cron:hourly      # Auto-learn every hour
npm run qa:cron:daily       # Auto-learn every day
```

### Utilities

```bash
npm run qa:failures:demo     # Run complete demo with sample data
node scripts/analyze-failures.js help  # Show all CLI options
```

## 🔄 Recommended Workflows

### Local Development

```bash
# Terminal 1: Keep dashboard open
npm run qa:dashboard

# Terminal 2: Run tests frequently
npm run test:unit

# When needed:
npm run qa:suggest           # Get smart recommendations
npm run qa:learn             # Extract new patterns
npm run qa:report            # View comprehensive stats
```

### Production Deployment

```bash
# Start services (use PM2 for persistence)
pm2 start npm --name "qa-cron" -- run qa:cron:hourly
pm2 start npm --name "qa-dash" -- run qa:dashboard
pm2 startup && pm2 save

# Or use system cron
# See CRON_SETUP.md for detailed instructions
```

### CI/CD Integration

```yaml
# GitHub Actions
- name: Learn from test failures
  run: npm run qa:learn
  if: always()  # Run even if tests fail

# Upload patterns for team visibility
- uses: actions/upload-artifact@v4
  with:
    name: learned-patterns
    path: qa/learning/learned_patterns.json
```

## 📈 What You'll See

### Failure Capture (Automatic)

When you run tests, failures are auto-captured:

```
Test: "Dialog should close on overlay click"
Status: ✗ FAILED
Error: "Expected element to be hidden but was visible (timeout: 5000ms)"

→ Automatically recorded to failures/failure_XXXXX.json
```

### Pattern Learning

```
npm run qa:learn
→ Processing 28 unlearned failures
→ Learned 62 patterns
→ Persisted to learned_patterns.json
→ Pattern examples:
   1. "expected ... visible" (24x, 100% confidence)
   2. "category:assertion" (28x, 100% confidence)
   3. "timeout" (12x, 100% confidence)
```

### Intelligent Suggestions

```
npm run qa:suggest
→ Pattern: "expected element hidden"
→ Match Score: 100% relevance
→ Confidence: 100% (seen 24 times)
→ Problem: Element visibility timing issue
→ Solutions:
   • Use explicit wait: await page.waitForFunction(...)
   • Verify animations complete before asserting
   • Check CSS visibility, not just display
```

### Live Dashboard

Web UI showing:
- 📊 Pattern distribution charts
- 📈 Occurrence graphs  
- 🎯 Top patterns ranked by frequency
- 🔍 Searchable pattern table
- ⏱️ Auto-refresh every 30 seconds

## 🎓 How Pattern Matching Works

### 1. Failure Capture

Test frameworks automatically report:
- Test name and file
- Error message
- Stack trace
- Category (timeout, assertion, etc.)
- Severity level

### 2. Pattern Extraction

Learning system identifies recurring patterns:

```
Failure 1: "Expected true but got false"
Failure 2: "Expected true but got false"  
Failure 3: "Expected true but got false"

→ Extract pattern: "expected ... got" (confidence: 100%)
```

### 3. Relevance Scoring

When a new failure occurs, system scores against all patterns:

```
New failure: "Expected false but got true"

Scoring:
  ✓ "expected ... got" → 98% match (highest relevance)
  ✓ "category:assertion" → 100% match (seen 28x)
  ✓ "but" → 85% match
  
→ Show top 3 with solutions
```

### 4. Intelligent Recommendations

Suggestions are context-aware based on pattern type and history:

```
Pattern: "timeout"
Type: technical
Occurrence: 12x
→ Solution: Increase waits, verify async operations, 
            check for race conditions
```

## 📊 Metrics & Insights

Track learning progress:

```bash
npm run qa:report
```

Shows:
- **Total Patterns Learned**: 62
- **High-Confidence (>80%)**: 62 (100%)
- **Avg Confidence**: 87%
- **Patterns by Type**: message (61), category (1)
- **Critical Patterns**: 0
- **Total Failures Processed**: 28

Good targets:
- Total patterns: 50+
- High-confidence %: >70%
- Average confidence: >70%
- Critical resolved: >50%

## 🔒 Data Privacy & Storage

- ✅ All data stored locally in `qa/learning/`
- ✅ Patterns are extracted anonymously (no test code)
- ✅ `failures/` directory is gitignored
- ✅ `learned_patterns.json` can be committed for team sharing
- ✅ No external API calls or cloud storage

## 🚨 Troubleshooting

### No failures captured?

```bash
# Verify reporters are active
grep "playwright-reporter\|vitest-reporter" playwright.config.ts vitest.config.ts

# Check failures directory  
ls -la failures/
```

### Patterns not learning?

```bash
# Run learning with verbose output
npm run qa:learn

# Check patterns were written
cat qa/learning/learned_patterns.json | jq '.patterns | length'

# If empty, verify failures exist
npm run qa:failures:stats
```

### Dashboard won't connect?

```bash
# Check server is running
curl http://localhost:3333/

# Verify patterns file is readable
ls -la qa/learning/learned_patterns.json
chmod 644 qa/learning/learned_patterns.json
```

### Cron job not running?

```bash
# Run in foreground to see output
npm run qa:cron

# Check for errors
npm run qa:cron 2>&1 | head -20
```

## 📚 Related Documentation

- **[CRON_SETUP.md](./CRON_SETUP.md)** - Background automation
- **[README.md](./README.md)** - System overview
- **[qa/learning/pattern-suggester.js](./pattern-suggester.js)** - Suggestion engine
- **[qa/learning/dashboard.html](./dashboard.html)** - Web UI

## ✅ Verification Checklist

- [ ] Tests auto-capture failures (check `failures/` directory)
- [ ] `npm run qa:learn` extracts patterns successfully  
- [ ] `npm run qa:report` shows 50+ learned patterns
- [ ] `npm run qa:suggest` provides intelligent recommendations
- [ ] `npm run qa:dashboard` opens web UI and loads patterns
- [ ] `npm run qa:cron` runs without errors

## 🎯 Next Steps

1. **Start using the system**
   ```bash
   npm run test:unit
   npm run qa:learn
   npm run qa:report
   ```

2. **Get familiar with suggestions**
   ```bash
   npm run qa:suggest
   npm run qa:dashboard
   ```

3. **Set up automation**
   - Follow [CRON_SETUP.md](./CRON_SETUP.md)
   - Keep cron job running in background
   - Monitor dashboard regularly

4. **Share insights with team**
   - Export patterns: `cat qa/learning/learned_patterns.json`
   - Share dashboard link  
   - Use suggestions to fix root causes

---

**Status: ✅ Production Ready**

The learning system is fully integrated, tested with real failures, and ready for continuous use. All components are operational.
