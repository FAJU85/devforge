# QA Learning System

A production-ready learning system for the QA suite that automatically captures test failures, analyzes patterns, and generates actionable fix suggestions.

## Overview

The QA Learning System operates in five interconnected layers:

1. **Failure Collection** (`failure_collector.js`) - Captures test failures with full context
2. **Pattern Learning** (`pattern_learner.js`) - Analyzes failures to extract recurring patterns
3. **Pattern Storage** (`learned_patterns.json`) - Persistent database of learned patterns
4. **Pattern Matching** (`pattern_matcher.js`) - Detects issues in new code against learned patterns
5. **Suggestion Generation** (`suggestion_generator.js`) - Generates fix recommendations

## Architecture

```
Test Execution
      ↓
Failure Collection → Failure Storage
      ↓
Pattern Learning → Pattern Database
      ↓
Pattern Matching ↔ Code Analysis
      ↓
Suggestion Generation → Recommendations
      ↓
Feedback Loop → Pattern Refinement
```

## Components

### 1. Failure Collector (`failure_collector.js`)

Captures comprehensive test failure data including:
- Test name, file path, and framework
- Error message and stack trace
- Code context around failure point
- Severity and category classification
- Environmental information
- Execution duration

**Key Methods:**
- `collect(failureData)` - Capture a new failure
- `getRecent(limit)` - Get recent failures
- `getByCategory(category)` - Filter by error type
- `getBySeverity(severity)` - Filter by severity
- `getUnlearned()` - Get failures not yet analyzed
- `markLearned(failureId, patternId)` - Mark failure as learned
- `getStatistics()` - Aggregate failure statistics

**Usage:**
```javascript
const collector = new FailureCollector();
const failure = collector.collect({
  testName: 'Dialog should close on overlay click',
  testFile: 'tests/components/Dialog.test.js',
  errorMessage: 'Element was visible after 5000ms',
  errorStack: 'at closeDialog (src/components/Dialog.ts:45)',
  duration: 5234,
  category: 'timeout',
  severity: 'high',
});
```

### 2. Pattern Learner (`pattern_learner.js`)

Analyzes collected failures to extract recurring patterns with confidence scoring.

**Pattern Properties:**
- **ID**: Unique pattern identifier
- **Pattern**: String representation of the pattern
- **Type**: `message`, `stack_trace`, `category`, `context_browser`, `context_selector`
- **Occurrences**: How many times this pattern appeared
- **Confidence**: 0-1 score based on consistency and frequency
- **Severity**: `critical`, `high`, `medium`, `low`

**Key Methods:**
- `learn(failures)` - Learn patterns from failures
- `getStatistics()` - Get pattern statistics
- `getTopPatterns(count)` - Get highest-confidence patterns
- `matchFailure(failure)` - Check if failure matches known patterns
- `updatePattern(patternId, update)` - Update pattern with feedback

**Confidence Calculation:**
```
confidence = (frequency * 0.4) + (consistency * 0.6)
  where:
    frequency = min(occurrences / 10, 1.0)
    consistency = similarity of error messages and stack traces
```

### 3. Pattern Storage (`learned_patterns.json`)

JSON database storing all learned patterns with structure:

```json
{
  "patterns": [
    {
      "id": "pattern_1234567890_abc123",
      "pattern": "Element was visible after",
      "type": "message",
      "occurrences": 6,
      "confidence": 0.95,
      "severity": "high",
      "createdAt": "2026-06-12T23:45:00.000Z",
      "lastSeen": "2026-06-12T23:50:00.000Z"
    }
  ],
  "lastUpdated": "2026-06-12T23:50:00.000Z",
  "version": "1.0"
}
```

### 4. Pattern Matcher (`pattern_matcher.js`)

Analyzes code against learned patterns to detect potential issues before they fail.

**Key Methods:**
- `analyzeCode(code, context)` - Scan code for pattern matches
- `matchPattern(code, pattern, context)` - Test single pattern
- `analyzeFile(filePath)` - Analyze entire file
- `updatePatterns(patterns)` - Update from learner

**Analysis Scoring:**
- Score based on pattern confidence and match strength
- Returns only matches above minimum threshold (0.5 default)

**Usage:**
```javascript
const matcher = new PatternMatcher();
const issues = matcher.analyzeCode(componentCode, { type: 'dialog' });
// Returns issues with score, confidence, severity
```

### 5. Suggestion Generator (`suggestion_generator.js`)

Creates actionable fix recommendations based on learned patterns.

**Suggestion Types:**
- Similar failure pattern detected
- Function with failure history
- Browser-specific issue
- Selector fragility detected
- Performance issue detected
- Category-specific recommendations

**Key Methods:**
- `generateSuggestions(failure, patterns)` - Generate suggestions
- `generatePatternSuggestions(failure, pattern)` - Pattern-based suggestions
- `generateCategorySuggestions(failure)` - Category-based suggestions
- `rankSuggestions(suggestions)` - Rank by confidence
- `provideFeedback(suggestionId, feedback)` - Record feedback

## CLI Usage

### Main Analysis Tool

```bash
# Show help
node scripts/analyze-failures.js help

# Collect sample failure for testing
node scripts/analyze-failures.js collect

# List recent failures
node scripts/analyze-failures.js list

# Show failure statistics
node scripts/analyze-failures.js stats

# Learn patterns from failures
node scripts/analyze-failures.js learn

# Show learning progress report
node scripts/analyze-failures.js report

# Clear all collected failures
node scripts/analyze-failures.js clear

# Run complete demo with sample data
node scripts/analyze-failures.js demo
```

### NPM Scripts

```bash
# Learn patterns from failures
npm run qa:learn

# List recent failures
npm run qa:failures

# Show failure statistics
npm run qa:failures:stats

# Run demo
npm run qa:failures:demo

# Collect sample failure
npm run qa:failures:collect

# Clear failures
npm run qa:failures:clear
```

## Integration with Test Runners

### Vitest Integration

Add to `vitest.config.js`:

```javascript
import { defineConfig } from 'vitest/config';
import FailureCollector from './qa/learning/failure_collector';

const collector = new FailureCollector();

export default defineConfig({
  test: {
    onTestFailure: (failure) => {
      collector.collect({
        testName: failure.name,
        testFile: failure.file,
        errorMessage: failure.error?.message,
        errorStack: failure.error?.stack,
        category: failure.category,
        severity: failure.severity || 'medium',
      });
    },
  },
});
```

### Playwright Integration

Add to reporter or test setup:

```javascript
import FailureCollector from './qa/learning/failure_collector';

const collector = new FailureCollector();

test.afterEach(async ({ page }, testInfo) => {
  if (testInfo.status !== 'passed') {
    collector.collect({
      testName: testInfo.title,
      testFile: testInfo.file,
      errorMessage: testInfo.error?.message || 'Test failed',
      errorStack: testInfo.error?.stack,
      duration: testInfo.duration,
      framework: 'playwright',
    });
  }
});
```

## Failure Categories

The system automatically categorizes failures:

- `timeout` - Waiting for element/condition timeout
- `assertion` - Assertion failure (expect, should, etc.)
- `navigation` - Page navigation or routing issue
- `selector` - Element not found or selector issue
- `interaction` - Click, type, or user interaction failed
- `async` - Async/promise-related issue
- `api` - API call or network issue
- `unknown` - Unable to categorize

## Learning Flow Example

### Step 1: Collect Failures

```
Test Run 1 → Dialog test fails on timeout
            → Failure collected with "Element was visible after 5000ms"

Test Run 2 → Toast test fails, click doesn't propagate
            → Failure collected with "pointer-events blocking"

Test Run 3 → Dialog test fails again on same condition
            → Failure collected with same error message
```

### Step 2: Learn Patterns

```
Analyze 3 failures:
  - Error message similarity: 2/3 similar → timeout issues
  - Stack trace similarity: common functions in Dialog.ts
  - Category: mostly "timeout" and "interaction"

Generate patterns:
  Pattern 1: "Element was visible after" (message-based, confidence 80%)
  Pattern 2: "Dialog.ts functions" (stack-trace based, confidence 75%)
  Pattern 3: "timeout" category (category-based, confidence 90%)
```

### Step 3: Apply Patterns

```
New code added with:
  - dialog.addEventListener('click', ...)
  - setTimeout-based state updates
  - pointer-events: auto on fixed element

Pattern matcher checks code:
  ✓ Matches Pattern 2 (Dialog.ts pattern)
  ✓ Matches timeout risk
  → Suggests dialog pointer-events fix
```

### Step 4: Feedback Loop

```
User applies suggestion → Tests pass
  → Mark pattern as helpful
  → Increase pattern confidence to 95%
  → Better suggestions for future similar issues

User reports suggestion wasn't relevant
  → Record feedback
  → Adjust pattern confidence
  → Refine future suggestions
```

## Pattern Confidence Levels

- **90-100%**: Trust in this pattern, suggest fixes automatically
- **70-89%**: Good confidence, suggest but require review
- **50-69%**: Possible pattern, inform but don't strongly suggest
- **Below 50%**: Not yet reliable, continue learning

## Performance Considerations

- Failures stored in JSON (scalable up to ~1000s with minimal overhead)
- Pattern matching is O(n) where n = number of patterns
- Typical response time <100ms for code analysis
- Automatic cleanup of failures older than 30 days
- Patterns indexed by type and confidence for fast retrieval

## Best Practices

### For Test Development

1. **Add meaningful error messages** - Helps pattern recognition
   ```javascript
   expect(isVisible).toBe(true, 'Dialog should be visible after open');
   // Better than: expect(isVisible).toBe(true);
   ```

2. **Use consistent test names** - Aids categorization
   ```javascript
   // Consistent naming for dialog tests
   test('Dialog should open on button click')
   test('Dialog should close on overlay click')
   test('Dialog should focus input on open')
   ```

3. **Tag tests appropriately** - Helps pattern correlation
   ```javascript
   test('Dialog should close on overlay click', { tags: ['dialog', 'interaction'] })
   ```

### For Pattern Refinement

1. **Review patterns regularly** - Check high-frequency patterns monthly
2. **Provide feedback** - Mark helpful suggestions to improve confidence
3. **Clean up patterns** - Remove low-confidence patterns not improving
4. **Monitor learning rate** - Ensure new patterns are being learned

## Monitoring & Metrics

### Key Metrics

- **Failure Rate**: Number of failures per test run
- **Learning Rate**: New patterns learned per week
- **Pattern Coverage**: % of failures matched by patterns
- **Suggestion Accuracy**: % of suggestions that help (from feedback)
- **False Positives**: Suggestions that don't apply

### Reporting

```bash
# Get learning system statistics
node scripts/analyze-failures.js report

# Show failure breakdown
node scripts/analyze-failures.js stats

# View pattern effectiveness
node scripts/analyze-failures.js learn
```

## Troubleshooting

### No patterns being learned

1. Check if failures are being collected:
   ```bash
   npm run qa:failures  # Should show recent failures
   ```

2. Verify failure data completeness:
   ```bash
   npm run qa:failures:stats  # Check categorization
   ```

3. Ensure minimum 2 occurrences of error:
   - Patterns need at least 2 matching failures

### Patterns not matching code

1. Check pattern type matches analysis type
2. Verify code context is being provided
3. Adjust minimum match score if needed
4. Review pattern confidence threshold

### Memory usage growing

1. Clear old failures:
   ```bash
   npm run qa:failures:clear
   ```

2. Check learned_patterns.json size:
   ```bash
   wc -l qa/learning/learned_patterns.json
   ```

## API Reference

See individual module files for complete API documentation:
- `failure_collector.js` - FailureCollector class
- `pattern_learner.js` - PatternLearner class
- `pattern_matcher.js` - PatternMatcher class
- `suggestion_generator.js` - SuggestionGenerator class

## Contributing

When extending the learning system:

1. Follow the existing class-based architecture
2. Add comprehensive error handling
3. Include logging for debugging
4. Write tests for new methods
5. Update this README with new features
6. Maintain backward compatibility with learned_patterns.json

## License

Same as parent project (ISC)
