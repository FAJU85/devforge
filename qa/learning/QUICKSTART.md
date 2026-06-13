# QA Learning System - Quick Start Guide

Get the learning system up and running in 5 minutes.

## What It Does

The QA Learning System automatically:
- Captures test failures as they occur
- Analyzes patterns in failure data
- Generates fix suggestions for future similar failures
- Improves recommendations based on feedback

## Installation

Files are already in place:
- `qa/learning/failure_collector.js` - Captures failures
- `qa/learning/pattern_learner.js` - Learns from failures
- `qa/learning/pattern_matcher.js` - Detects issues in code
- `qa/learning/suggestion_generator.js` - Generates suggestions
- `qa/learning/learned_patterns.json` - Pattern database
- `scripts/analyze-failures.js` - CLI tool

## Quick Commands

### 1. Run the Demo

See the learning system in action with sample data:

```bash
npm run qa:failures:demo
```

Output shows:
- Failures collected from sample data
- Patterns learned (32 patterns from 5 failures)
- Learning statistics and top patterns
- Code analysis results

### 2. Collect a Failure

Manually add a failure to the system:

```bash
npm run qa:failures:collect
```

### 3. View Collected Failures

See all failures that have been collected:

```bash
npm run qa:failures
```

Shows:
- Test name
- Error category
- Error message
- Timestamp

### 4. Check Statistics

Analyze collected failure data:

```bash
npm run qa:failures:stats
```

Shows:
- Total failure count
- Failures grouped by category (timeout, assertion, etc.)
- Failures grouped by severity (high, medium, low)

### 5. Learn Patterns

Extract patterns from collected failures:

```bash
npm run qa:learn
```

Shows:
- Number of patterns learned
- Top patterns with confidence scores
- Pattern types and occurrences

## Common Workflows

### Workflow 1: Learning from Test Runs

```bash
# 1. Run your tests (failures auto-collected when integrated)
npm run test:all

# 2. Analyze collected failures
npm run qa:failures:stats

# 3. Learn patterns
npm run qa:learn

# 4. See what was learned
npm run qa:failures:demo  # Shows full report
```

### Workflow 2: Analyzing New Code

```bash
# After learning patterns, the matcher can analyze code:
node scripts/analyze-failures.js match "path/to/code.js"

# Shows potential issues based on learned patterns
```

### Workflow 3: Clearing Old Data

```bash
# Start fresh
npm run qa:failures:clear

# Confirm cleared
npm run qa:failures  # Should show no failures
```

## How It Works

### 1. Failure Collection

When a test fails:
```
Test Fails
   ↓
Error Captured (message, stack, context)
   ↓
Saved to qa/failures/ directory
   ↓
Ready for analysis
```

### 2. Pattern Learning

```
Multiple Similar Failures
   ↓
Analyze for patterns (message, stack trace, category)
   ↓
Calculate confidence (how similar are they?)
   ↓
Store in learned_patterns.json
   ↓
Ready to match against new code
```

### 3. Issue Detection

```
New Code Written
   ↓
Pattern Matcher analyzes it
   ↓
Compares against learned patterns
   ↓
Reports potential issues
   ↓
Suggests fixes based on past failures
```

## Example: Timeout Pattern

### Learning Phase

```
Failure 1: Dialog test
  Error: "Element was visible after 5000ms"
  
Failure 2: Toast test  
  Error: "Timeout waiting for hidden element"
  
Failure 3: Dialog test (same issue)
  Error: "Element was visible after 5000ms"
  
Pattern Learned:
  Type: timeout issues
  Confidence: 85%
  Suggestion: "Check visibility state before timeout"
```

### Detection Phase

```
New Code Added:
  dialog.style.display = 'none'
  // Missing: wait for actually visible property
  
Pattern Matcher Detects:
  ✓ Matches learned timeout pattern
  Suggestion: "Add explicit visibility check before assuming hidden"
  Confidence: 85%
```

## Understanding Confidence Scores

Patterns have confidence scores (0-100%):

- **90-100%**: Highly reliable, implement suggestions
- **70-89%**: Likely useful, review suggestions
- **50-69%**: Possibly relevant, consider suggestions
- **Below 50%**: Not yet reliable, gather more data

Confidence increases when:
- More similar failures occur
- Error messages are very similar
- Suggestions actually help (you mark them helpful)

## Demo Output Explained

When you run `npm run qa:failures:demo`, you see:

```
Step 1: Collecting Sample Failures
✓ Collected: Dialog component should close on overlay click
✓ Collected: Toast notification should not block clicks
...
```
5 sample failures collected for testing.

```
Step 2: Analyzing Failures
  Total Failures: 10
  Failures by Category:
    timeout: 4
    assertion: 6
```
Shows categorization of failures collected.

```
Step 3: Learning Patterns from Failures
✓ Learned 32 patterns from 10 failures
```
System extracted 32 distinct patterns.

```
Step 4: Learning Report
Patterns by Type:
  message: 30 patterns (avg 81% confidence)
  category: 2 patterns (avg 90% confidence)
```
Patterns grouped by type with confidence levels.

```
Top Patterns:
  1. element (100% - 6x)
  2. category:assertion (100% - 6x)
```
Most frequent/confident patterns identified.

## Next Steps

1. **Integrate with your tests**: Update test runners to auto-collect failures
2. **Set up regular learning**: Run `npm run qa:learn` after test suites
3. **Review patterns**: Check high-confidence patterns monthly
4. **Provide feedback**: Mark helpful suggestions to improve system
5. **Monitor metrics**: Track failure rate and pattern effectiveness

## Troubleshooting

**No failures showing?**
```bash
npm run qa:failures:collect  # Collect sample
npm run qa:failures          # Verify it's there
```

**No patterns learned?**
```bash
# Need at least 2 matching failures for pattern
npm run qa:failures:stats    # Check failure count
npm run qa:failures          # Check they're categorized
```

**Want to reset?**
```bash
npm run qa:failures:clear    # Clear all data
npm run qa:failures:demo     # Start fresh with demo
```

## File Locations

```
qa/learning/
  ├── failure_collector.js      # Failure capture
  ├── pattern_learner.js        # Pattern extraction
  ├── pattern_matcher.js        # Issue detection
  ├── suggestion_generator.js   # Fix suggestions
  ├── learned_patterns.json     # Learned patterns database
  ├── README.md                 # Full documentation
  └── failures/                 # Collected failure storage
      └── failures.json         # All collected failures

scripts/
  └── analyze-failures.js       # CLI tool for learning system
```

## Performance

- Demo runs in < 2 seconds
- Learning from 10 failures < 100ms
- Code analysis < 100ms
- All data stored locally (no network calls)

## What's Next?

After trying the quick start:

1. Read `qa/learning/README.md` for full documentation
2. Review `scripts/analyze-failures.js --help` for all CLI options
3. Integrate pattern collection into your test runners
4. Set up automated pattern learning in CI/CD

Happy testing!
