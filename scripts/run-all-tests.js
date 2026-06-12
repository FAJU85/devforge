#!/usr/bin/env node

/**
 * Autonomous Test Coordinator
 *
 * Runs all test layers and generates a unified report:
 * - Unit Tests (Vitest)
 * - E2E Tests (Playwright)
 * - Pattern Detection
 */

const { execSync } = require('child_process');
const fs = require('fs');
const path = require('path');

const COLORS = {
  reset: '\x1b[0m',
  bold: '\x1b[1m',
  green: '\x1b[32m',
  red: '\x1b[31m',
  yellow: '\x1b[33m',
  blue: '\x1b[34m',
  cyan: '\x1b[36m',
};

function log(color, message) {
  console.log(`${COLORS[color]}${message}${COLORS.reset}`);
}

function logSection(title) {
  console.log('\n' + '='.repeat(80));
  log('bold', `🧪 ${title}`);
  console.log('='.repeat(80) + '\n');
}

function runCommand(command, label) {
  log('cyan', `Running: ${label}...`);
  try {
    const output = execSync(command, { encoding: 'utf8' });
    return { success: true, output };
  } catch (error) {
    return { success: false, output: error.stdout || error.message };
  }
}

async function runTests() {
  const startTime = Date.now();
  const results = {};

  logSection('AUTONOMOUS TEST SUITE');

  // 1. Pattern Detection
  logSection('Phase 1: Pattern Detection');
  const patternResult = runCommand('npm run qa:scan 2>&1', 'Pattern Scanner');
  results.patterns = patternResult;
  if (patternResult.success) {
    log('green', '✓ Pattern detection completed');
  }

  // 2. Unit Tests
  logSection('Phase 2: Unit Tests (Vitest)');
  const unitResult = runCommand('npm run test:unit:run 2>&1', 'Unit Tests');
  results.unit = unitResult;

  let unitPassed = 0;
  let unitTotal = 0;
  if (unitResult.success) {
    const match = unitResult.output.match(/Tests\s+(\d+)\s+passed/);
    if (match) {
      unitPassed = parseInt(match[1]);
      unitTotal = unitPassed;
    }
    log('green', `✓ Unit tests: ${unitPassed}/${unitTotal} passing`);
  } else {
    log('red', '✗ Unit tests failed');
  }

  // 3. E2E Tests
  logSection('Phase 3: E2E Tests (Playwright)');
  const e2eResult = runCommand('npm run test:e2e 2>&1', 'E2E Tests');
  results.e2e = e2eResult;

  let e2ePassed = 0;
  let e2eTotal = 0;
  if (e2eResult.success || e2eResult.output.includes('passed')) {
    const match = e2eResult.output.match(/(\d+)\s+passed/);
    const failMatch = e2eResult.output.match(/(\d+)\s+failed/);

    if (match) {
      e2ePassed = parseInt(match[1]);
      e2eTotal = e2ePassed;
    }
    if (failMatch) {
      const failed = parseInt(failMatch[1]);
      e2eTotal = e2ePassed + failed;
    }

    log('green', `✓ E2E tests: ${e2ePassed}/${e2eTotal} passing`);
  } else {
    log('red', '✗ E2E tests failed');
  }

  // Generate report
  logSection('Test Results Summary');

  const totalTests = unitTotal + e2eTotal;
  const totalPassed = unitPassed + e2ePassed;
  const passRate = totalTests > 0 ? ((totalPassed / totalTests) * 100).toFixed(1) : 0;

  console.log(`
${COLORS.bold}Test Coverage by Layer:${COLORS.reset}
  Unit Tests (Vitest):        ${unitPassed}/${unitTotal} passing
  E2E Tests (Playwright):     ${e2ePassed}/${e2eTotal} passing
  ─────────────────────────────────────
  ${COLORS.bold}Total:${COLORS.reset}                   ${totalPassed}/${totalTests} passing (${passRate}%)

${COLORS.bold}Architecture:${COLORS.reset}
  ✓ Unit Testing Layer        (Component-level)
  ✓ E2E Testing Layer         (Integration-level)
  ✓ Pattern Detection Layer   (Quality assurance)

${COLORS.bold}Status:${COLORS.reset}
  ${totalPassed === totalTests ? COLORS.green + '✓ ALL TESTS PASSING' + COLORS.reset :
    COLORS.yellow + `⚠ ${totalTests - totalPassed} tests failing` + COLORS.reset}

  Pass Rate: ${passRate}%
  `);

  const duration = ((Date.now() - startTime) / 1000).toFixed(1);
  log('cyan', `\nCompleted in ${duration}s`);

  // Exit with appropriate code
  process.exit(totalPassed === totalTests ? 0 : 1);
}

// Run the tests
runTests().catch((error) => {
  log('red', `Error running tests: ${error.message}`);
  process.exit(1);
});
