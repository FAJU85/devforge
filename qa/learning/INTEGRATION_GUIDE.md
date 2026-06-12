# Integration Guide - QA Learning System

Instructions for integrating the learning system with your test runners.

## Overview

The learning system needs to be integrated at two points:

1. **Failure Capture** - When tests fail, capture the failure data
2. **Pattern Learning** - Periodically analyze failures and learn patterns

## Vitest Integration

### Option 1: Global Test Hook

Add to your `vitest.config.js`:

```javascript
import { defineConfig } from 'vitest/config';
import FailureCollector from './qa/learning/failure_collector.js';

const collector = new FailureCollector();

export default defineConfig({
  test: {
    // ... other config
    
    // Hook for handling test failures
    onTestFailure: (result) => {
      if (result.error) {
        collector.collect({
          testName: result.name,
          testFile: result.file,
          errorMessage: result.error.message,
          errorStack: result.error.stack,
          category: categorizeError(result.error.message),
          severity: 'medium', // Can be 'critical', 'high', 'medium', 'low'
          duration: result.duration || 0,
          framework: 'vitest',
        });
      }
    },
  },
});

function categorizeError(message) {
  if (message.includes('timeout')) return 'timeout';
  if (message.includes('not found')) return 'selector';
  if (message.includes('Expected')) return 'assertion';
  if (message.includes('Cannot read')) return 'async';
  return 'unknown';
}
```

### Option 2: Test Wrapper

Create `tests/helpers/failure-tracking.js`:

```javascript
import FailureCollector from '../../qa/learning/failure_collector.js';

const collector = new FailureCollector();

export function trackTestFailure(test) {
  return async (context) => {
    try {
      await test(context);
    } catch (error) {
      collector.collect({
        testName: context.task.name,
        testFile: context.task.file,
        errorMessage: error.message,
        errorStack: error.stack,
        category: categorizeError(error.message),
        severity: 'medium',
        framework: 'vitest',
      });
      throw error; // Re-throw to fail test
    }
  };
}
```

Then use in tests:

```javascript
import { test, expect } from 'vitest';
import { trackTestFailure } from './helpers/failure-tracking';

test('Dialog closes on overlay click', trackTestFailure(async () => {
  // Your test code
}));
```

## Playwright Integration

### Option 1: Custom Reporter

Create `playwright/reporters/learning-reporter.ts`:

```typescript
import { Reporter, FullResult, TestCase, TestError } from '@playwright/test/reporter';
import FailureCollector from '../../qa/learning/failure_collector';

const collector = new FailureCollector();

export class LearningReporter implements Reporter {
  onTestEnd(test: TestCase, result: TestError) {
    if (result.status === 'failed' && result.error) {
      collector.collect({
        testName: test.title,
        testFile: test.file,
        errorMessage: result.error.message || 'Test failed',
        errorStack: result.error.stack,
        category: categorizeError(result.error.message),
        severity: 'medium',
        duration: result.duration,
        framework: 'playwright',
      });
    }
  }

  onEnd(result: FullResult) {
    // Optionally learn patterns after test run
    console.log(`\nCollected ${result.stats.failures} failures`);
  }
}

function categorizeError(message: string): string {
  if (message.includes('Timeout')) return 'timeout';
  if (message.includes('not found')) return 'selector';
  if (message.includes('Expected')) return 'assertion';
  return 'unknown';
}
```

Add to `playwright.config.ts`:

```typescript
import { defineConfig } from '@playwright/test';
import LearningReporter from './reporters/learning-reporter';

export default defineConfig({
  reporter: [
    ['html'],
    ['./reporters/learning-reporter.ts'],
  ],
  // ... rest of config
});
```

### Option 2: Test Wrapper

Add to your `tests/base.ts`:

```typescript
import { test as base, expect } from '@playwright/test';
import FailureCollector from '../qa/learning/failure_collector';

const collector = new FailureCollector();

export const test = base.extend({
  collectFailures: async ({}, use, testInfo) => {
    await use(null);
    
    if (testInfo.status === 'failed') {
      collector.collect({
        testName: testInfo.title,
        testFile: testInfo.file,
        errorMessage: testInfo.error?.message || 'Test failed',
        errorStack: testInfo.error?.stack,
        category: categorizeTestError(testInfo.error?.message),
        severity: 'medium',
        duration: testInfo.duration,
        framework: 'playwright',
      });
    }
  },
});

function categorizeTestError(message?: string): string {
  if (!message) return 'unknown';
  if (message.includes('Timeout')) return 'timeout';
  if (message.includes('not found')) return 'selector';
  if (message.includes('Expected')) return 'assertion';
  if (message.includes('navigate')) return 'navigation';
  return 'unknown';
}
```

## Jest Integration

Add to `jest.config.js`:

```javascript
const FailureCollector = require('./qa/learning/failure_collector');
const collector = new FailureCollector();

module.exports = {
  // ... other config
  
  reporters: [
    'default',
    [
      'jest-junit',
      {
        outputDirectory: './test-results',
        onComplete: (results) => {
          // Process failures
          const failures = results.testResults
            .filter(result => result.numFailingTests > 0)
            .flatMap(result => 
              result.assertionResults
                .filter(assertion => assertion.status === 'failed')
                .map(assertion => ({
                  testName: assertion.fullName || assertion.title,
                  testFile: result.name,
                  errorMessage: assertion.failureMessages?.[0] || 'Test failed',
                  category: 'assertion',
                  severity: 'medium',
                  framework: 'jest',
                }))
            );
          
          failures.forEach(failure => collector.collect(failure));
        },
      },
    ],
  ],
};
```

## Python/Pytest Integration

Create `qa/learning/pytest_integration.py`:

```python
import json
from pathlib import Path
from qa.learning.failure_collector import FailureCollector

class LearningPlugin:
    def __init__(self):
        self.collector = FailureCollector()
    
    def pytest_runtest_logreport(self, report):
        if report.failed:
            # Extract failure info from pytest report
            failure_info = {
                'testName': report.nodeid,
                'testFile': report.fspath,
                'errorMessage': str(report.longrepr.reprcrash.message) if report.longrepr else 'Test failed',
                'category': self._categorize(report.longrepr),
                'severity': 'medium',
                'framework': 'pytest',
                'duration': report.duration * 1000,
            }
            
            self.collector.collect(failure_info)
    
    def _categorize(self, longrepr):
        if 'timeout' in str(longrepr).lower():
            return 'timeout'
        if 'assertion' in str(longrepr).lower():
            return 'assertion'
        return 'unknown'

# Register with pytest
def pytest_plugins():
    return [LearningPlugin()]
```

Add to `conftest.py`:

```python
from qa.learning.pytest_integration import LearningPlugin

pytest_plugins = [LearningPlugin()]
```

## CI/CD Integration

### GitHub Actions

Add to `.github/workflows/test.yml`:

```yaml
name: Tests with Learning

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Setup Node
        uses: actions/setup-node@v3
        with:
          node-version: '18'
      
      - name: Install dependencies
        run: npm ci
      
      - name: Run tests
        run: npm run test:all
        continue-on-error: true
      
      - name: Learn patterns
        run: npm run qa:learn
      
      - name: Generate report
        run: npm run qa:failures:stats
      
      - name: Upload failure data
        uses: actions/upload-artifact@v3
        if: always()
        with:
          name: failure-analysis
          path: qa/failures/
```

### GitLab CI

Add to `.gitlab-ci.yml`:

```yaml
test:
  script:
    - npm ci
    - npm run test:all || true
    - npm run qa:learn
    - npm run qa:failures:stats
  artifacts:
    paths:
      - qa/failures/
      - qa/learning/learned_patterns.json
    when: always
```

## Post-Test Pattern Learning

### Add to package.json

```json
{
  "scripts": {
    "test:all": "npm run test:unit:run && npm run test:integration:run && npm run test:e2e",
    "test:learn": "npm run test:all && npm run qa:learn"
  }
}
```

Run with learning:

```bash
npm run test:learn
```

### Automated Learning Hook

Create `scripts/post-test-learn.js`:

```javascript
const { spawn } = require('child_process');
const PatternLearner = require('../qa/learning/pattern_learner');
const FailureCollector = require('../qa/learning/failure_collector');

async function learnFromTests() {
  const collector = new FailureCollector();
  const learner = new PatternLearner();
  
  // Get unlearned failures
  const failures = collector.getUnlearned();
  
  if (failures.length === 0) {
    console.log('✓ No new failures to learn from');
    return;
  }
  
  console.log(`Learning from ${failures.length} failures...`);
  
  // Learn patterns
  learner.learn(failures);
  
  // Mark failures as learned
  const stats = learner.getStatistics();
  failures.forEach(f => {
    collector.markLearned(f.id, `auto_${Date.now()}`);
  });
  
  console.log(`✓ Learned ${stats.totalPatterns} patterns`);
}

// Run if called directly
if (require.main === module) {
  learnFromTests().catch(console.error);
}

module.exports = learnFromTests;
```

Add to `package.json`:

```json
{
  "scripts": {
    "test:learn": "npm run test:all && node scripts/post-test-learn.js"
  }
}
```

## Error Categorization

Customize error categorization for your codebase:

Create `qa/learning/categorizers.js`:

```javascript
// Custom error categorizers for different frameworks

export function categorizeVitestError(error) {
  const message = error.message || '';
  
  if (message.includes('timeout')) return 'timeout';
  if (message.includes('Expected')) return 'assertion';
  if (message.includes('not found')) return 'selector';
  if (message.includes('Cannot read')) return 'async';
  if (message.includes('ReferenceError')) return 'reference';
  
  return 'unknown';
}

export function categorizeDomError(error) {
  const message = error.message || '';
  
  if (message.includes('querySelector')) return 'selector';
  if (message.includes('addEventListener')) return 'listener';
  if (message.includes('style')) return 'style';
  
  return 'dom_error';
}
```

## Testing Integration

Verify integration works:

```bash
# Manually trigger a test failure
npm run test:unit:run -- --reporter=verbose

# Check if failures were collected
npm run qa:failures

# Learn patterns
npm run qa:learn

# Verify patterns exist
npm run qa:failures:stats
```

## Next Steps

1. Choose integration method for your test framework
2. Implement failure collection
3. Run tests to collect initial failures
4. Run `npm run qa:learn` to extract patterns
5. Review learned patterns with `npm run qa:failures:stats`
6. Set up CI/CD integration for automatic learning

## Support

For questions or issues with integration:
- Check `qa/learning/README.md` for API details
- Review example implementations in this guide
- Run demo: `npm run qa:failures:demo`
