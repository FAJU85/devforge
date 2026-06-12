#!/usr/bin/env node

/**
 * Intelligent QA Pattern Detector
 *
 * Learns from previously fixed issues and detects similar patterns
 * in new code to prevent regression.
 */

const fs = require('fs');
const path = require('path');

// Patterns learned from fixes
const LEARNED_PATTERNS = {
  pointerEventsBlocking: {
    name: 'Pointer Events Blocking Clicks',
    severity: 'high',
    description: 'Fixed overlays with pointer-events:auto can block clicks on elements above',
    check: (code) => {
      const hasFixedPosition = code.includes('position: fixed');
      const hasPointerEventsAuto = code.includes('pointer-events: auto') || !code.includes('pointer-events: none');
      const hasFlexLayout = code.includes('display: flex') || code.includes('display: inline-flex');
      const hasEventListener = code.includes('addEventListener') || code.includes('onClick');

      return hasFixedPosition && hasFlexLayout && hasEventListener && hasPointerEventsAuto;
    },
    fix: 'Set pointer-events: none on overlay container, use separate background element with pointer-events: auto',
    examples: ['Dialog.ts', 'CommandPalette.ts'],
  },

  transitionAll: {
    name: 'Overly Broad CSS Transitions',
    severity: 'medium',
    description: 'Using "transition: all" can cause unintended animations on state changes',
    check: (code) => {
      return /transition:\s*all/.test(code) && /addEventListener\s*\(['"](mouseenter|focus|click)['"]/i.test(code);
    },
    fix: 'Replace "transition: all" with explicit property list, exclude opacity/visibility',
    examples: ['index.html button styling'],
  },

  dynamicAutofocus: {
    name: 'Dynamic Element Autofocus',
    severity: 'medium',
    description: 'HTML autofocus attribute does not work on dynamically created elements',
    check: (code) => {
      return code.includes('createElement') && code.includes('autofocus') && !code.includes('setTimeout');
    },
    fix: 'Use setTimeout(() => element.focus(), 0) instead of autofocus attribute',
    examples: ['CommandPalette.ts'],
  },

  delayedCallbacks: {
    name: 'Delayed Callback Execution',
    severity: 'medium',
    description: 'Callbacks wrapped in setTimeout cause state to be inconsistent with UI',
    check: (code) => {
      return /setTimeout\s*\(\s*\(\)\s*=>\s*\{[^}]*callback/i.test(code);
    },
    fix: 'Execute callbacks immediately, then animate. Separate business logic from UI effects',
    examples: ['Dialog.ts'],
  },

  partialTextSelectors: {
    name: 'Fragile Text-Based Selectors',
    severity: 'medium',
    description: 'Using :has-text() with partial strings matches unintended elements',
    check: (code) => {
      return /has-text\(['"](Show|Hide|Open)[^"']*['"]\)/i.test(code);
    },
    fix: 'Use explicit ID selectors or data-testid instead of partial text matching',
    examples: ['index.html, integration.spec.ts'],
  },

  uncheckedCallbacks: {
    name: 'Unchecked Optional Callback Invocation',
    severity: 'high',
    description: 'Calling optional callbacks without null check causes runtime errors',
    check: (code) => {
      return /\(options\.[a-zA-Z]+\)/.test(code) && !code.includes('if (options');
    },
    fix: 'Always check: if (options.callback) options.callback()',
    examples: ['Dialog.ts'],
  },

  looseBoundZIndex: {
    name: 'Z-Index Coordination Issues',
    severity: 'medium',
    description: 'Overlapping fixed/absolute elements with uncoordinated z-index values',
    check: (code) => {
      return /z-index:\s*\d+/.test(code) && code.includes('position: fixed');
    },
    fix: 'Use consistent z-index values (998=modal, 999=toast, 9999=tooltip)',
    examples: [],
  },
};

// Severity levels
const SEVERITY_COLORS = {
  high: '\x1b[31m',    // Red
  medium: '\x1b[33m',  // Yellow
  low: '\x1b[36m',     // Cyan
  reset: '\x1b[0m',
};

/**
 * Scan a file for learned patterns
 */
function scanFile(filePath) {
  try {
    const code = fs.readFileSync(filePath, 'utf8');
    const findings = [];

    for (const [patternKey, pattern] of Object.entries(LEARNED_PATTERNS)) {
      if (pattern.check(code)) {
        findings.push({
          file: filePath,
          pattern: pattern.name,
          severity: pattern.severity,
          description: pattern.description,
          fix: pattern.fix,
          examples: pattern.examples,
        });
      }
    }

    return findings;
  } catch (error) {
    console.error(`Error scanning ${filePath}:`, error.message);
    return [];
  }
}

/**
 * Recursively scan directory for component files
 */
function scanDirectory(dirPath, extensions = ['.ts', '.tsx', '.html', '.js']) {
  const findings = [];

  function walk(dir) {
    const files = fs.readdirSync(dir);

    for (const file of files) {
      const filePath = path.join(dir, file);
      const stat = fs.statSync(filePath);

      if (stat.isDirectory()) {
        if (!file.startsWith('.') && file !== 'node_modules') {
          walk(filePath);
        }
      } else if (extensions.some(ext => file.endsWith(ext))) {
        findings.push(...scanFile(filePath));
      }
    }
  }

  walk(dirPath);
  return findings;
}

/**
 * Format and display findings
 */
function displayFindings(findings) {
  if (findings.length === 0) {
    console.log('\n✅ No known anti-patterns detected!\n');
    return;
  }

  console.log(`\n⚠️  Found ${findings.length} potential issues:\n`);

  const byFile = {};
  for (const finding of findings) {
    if (!byFile[finding.file]) {
      byFile[finding.file] = [];
    }
    byFile[finding.file].push(finding);
  }

  for (const [file, fileFinding] of Object.entries(byFile)) {
    console.log(`\n📄 ${file}`);
    console.log('─'.repeat(80));

    for (const finding of fileFinding) {
      const color = SEVERITY_COLORS[finding.severity];
      console.log(`\n  ${color}[${finding.severity.toUpperCase()}]${SEVERITY_COLORS.reset} ${finding.pattern}`);
      console.log(`  └─ ${finding.description}`);
      console.log(`  ✓ Fix: ${finding.fix}`);

      if (finding.examples.length > 0) {
        console.log(`  📚 Related fixes: ${finding.examples.join(', ')}`);
      }
    }
  }

  console.log('\n' + '═'.repeat(80) + '\n');
}

/**
 * Generate test template based on learned patterns
 */
function generateTestTemplate(componentName) {
  const template = `
/**
 * Tests for ${componentName} component
 * Generated from learned patterns
 */

import { test, expect } from '@playwright/test';

test.describe('${componentName}', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('http://localhost:5173');
  });

  // Pattern 1: Pointer events should not block other elements
  test('should not block clicks on elements above', async ({ page }) => {
    const component = await page.locator('[data-testid="${componentName.toLowerCase()}"]').first();
    if (await component.isVisible()) {
      // Verify that clicking elements above doesn't get blocked
      const topElement = await page.locator('[data-z-index-higher]').first();
      if (await topElement.isVisible()) {
        await topElement.click();
        // Should complete without timeout
      }
    }
  });

  // Pattern 2: State changes should be immediate
  test('should update state immediately', async ({ page }) => {
    const component = await page.locator('[data-testid="${componentName.toLowerCase()}"]').first();
    if (await component.isVisible()) {
      const initialState = await component.getAttribute('data-state');
      // Trigger state change
      // Verify state changed immediately, not during animation
      const newState = await component.getAttribute('data-state');
      expect(newState).not.toBe(initialState);
    }
  });

  // Pattern 3: Focus should work on dynamic elements
  test('should auto-focus input elements', async ({ page }) => {
    const input = await page.locator('[data-testid="${componentName.toLowerCase()}-input"]').first();
    if (await input.isVisible()) {
      const focused = await input.evaluate((el) => el === document.activeElement);
      expect(focused).toBe(true);
    }
  });

  // Pattern 4: Callbacks should be invoked immediately
  test('should invoke callbacks at correct time', async ({ page }) => {
    // Setup callback tracking
    const callbackInvoked = await page.evaluate(() => {
      window.callbackLog = [];
      return true;
    });

    if (callbackInvoked) {
      // Trigger callback
      // Verify callback was invoked
      const log = await page.evaluate(() => window.callbackLog);
      expect(log.length).toBeGreaterThan(0);
    }
  });

  // Pattern 5: Cleanup should be thorough
  test('should clean up properly', async ({ page }) => {
    // Create component
    // Destroy component
    // Verify no orphaned elements remain
    const orphaned = await page.locator('[data-testid="${componentName.toLowerCase()}"]').count();
    expect(orphaned).toBe(0);
  });
});
`;

  return template;
}

// Main execution
const command = process.argv[2];
const target = process.argv[3] || './src';

console.log(`\n🔍 QA Pattern Detector - Learning from ${Object.keys(LEARNED_PATTERNS).length} known patterns\n`);

switch (command) {
  case 'scan':
    const findings = scanDirectory(target);
    displayFindings(findings);
    process.exit(findings.length > 0 ? 1 : 0);
    break;

  case 'generate-test':
    const componentName = process.argv[4] || 'MyComponent';
    console.log(generateTestTemplate(componentName));
    break;

  case 'list-patterns':
    console.log('Learned Patterns:\n');
    for (const [key, pattern] of Object.entries(LEARNED_PATTERNS)) {
      console.log(`• ${pattern.name} (${pattern.severity})`);
      console.log(`  ${pattern.description}`);
    }
    break;

  default:
    console.log(`
Usage: node pattern_detector.js <command> [args]

Commands:
  scan [dir]              - Scan directory for known anti-patterns
  generate-test [name]    - Generate test template for component
  list-patterns           - Show all learned patterns

Examples:
  node pattern_detector.js scan ./src/components
  node pattern_detector.js generate-test Dialog
  node pattern_detector.js list-patterns
    `);
    break;
}
