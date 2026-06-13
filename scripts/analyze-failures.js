#!/usr/bin/env node

/**
 * Test Failure Analysis & Learning CLI
 *
 * Main tool for managing the QA learning system:
 * - Collect test failures
 * - Learn patterns from failures
 * - Generate fix suggestions
 * - Show learning progress
 */

const fs = require('fs');
const path = require('path');
const FailureCollector = require('../qa/learning/failure_collector');
const PatternLearner = require('../qa/learning/pattern_learner');
const PatternMatcher = require('../qa/learning/pattern_matcher');
const SuggestionGenerator = require('../qa/learning/suggestion_generator');

// Create instances
const failureCollector = new FailureCollector();
const patternLearner = new PatternLearner();
const patternMatcher = new PatternMatcher();
const suggestionGenerator = new SuggestionGenerator();

const COLORS = {
  reset: '\x1b[0m',
  bold: '\x1b[1m',
  dim: '\x1b[2m',
  red: '\x1b[31m',
  green: '\x1b[32m',
  yellow: '\x1b[33m',
  blue: '\x1b[34m',
  cyan: '\x1b[36m',
  magenta: '\x1b[35m',
};

function log(color, message) {
  console.log(`${COLORS[color]}${message}${COLORS.reset}`);
}

function logSection(title) {
  console.log('\n' + '='.repeat(70));
  log('bold', title);
  console.log('='.repeat(70) + '\n');
}

/**
 * Collect a sample failure for testing/demo
 */
function collectSampleFailure() {
  const samples = [
    {
      testName: 'Dialog component should close on overlay click',
      testFile: 'tests/components/Dialog.test.js',
      errorMessage: 'Expected element to be hidden, but it was visible after 5000ms',
      errorStack: `at closeDialog (src/components/Dialog.ts:45:12)
at processCallback (node_modules/@playwright/test/lib/test.js:123:45)`,
      duration: 5234,
      framework: 'playwright',
      severity: 'high',
      category: 'timeout',
      tags: ['dialog', 'ui', 'interaction'],
    },
    {
      testName: 'CommandPalette should focus input on open',
      testFile: 'tests/components/CommandPalette.test.js',
      errorMessage: 'Timeout waiting for focus to move to input element',
      errorStack: `at focusInput (src/components/CommandPalette.ts:78:15)
at setupPalette (node_modules/vitest/dist/index.js:234:23)`,
      duration: 3000,
      framework: 'vitest',
      severity: 'high',
      category: 'assertion',
      tags: ['command-palette', 'focus', 'input'],
    },
    {
      testName: 'Toast notification should not block clicks',
      testFile: 'tests/ui/Toast.test.js',
      errorMessage: 'Click event did not propagate - pointer-events may be blocking interaction',
      errorStack: `at handleClick (src/components/Toast.ts:92:8)
at executeTest (node_modules/vitest/dist/runner.js:456:12)`,
      duration: 2100,
      framework: 'vitest',
      severity: 'medium',
      category: 'assertion',
      tags: ['toast', 'pointer-events', 'click'],
    },
  ];

  const sample = samples[Math.floor(Math.random() * samples.length)];
  const failure = failureCollector.collect(sample);
  return failure;
}

/**
 * Display a formatted failure
 */
function displayFailure(failure) {
  console.log(`\n${COLORS.bold}Failure ID:${COLORS.reset} ${failure.id}`);
  console.log(`${COLORS.bold}Test:${COLORS.reset} ${failure.testName}`);
  console.log(`${COLORS.bold}File:${COLORS.reset} ${failure.testFile}`);
  console.log(`${COLORS.bold}Error:${COLORS.reset} ${failure.errorMessage}`);
  console.log(`${COLORS.bold}Category:${COLORS.reset} ${failure.category}`);
  console.log(`${COLORS.bold}Time:${COLORS.reset} ${failure.timestamp}`);
  console.log(`${COLORS.bold}Duration:${COLORS.reset} ${failure.duration}ms`);

  if (failure.stackTrace && failure.stackTrace.length > 0) {
    console.log(`\n${COLORS.dim}Stack Trace (first 3 frames):${COLORS.reset}`);
    failure.stackTrace.slice(0, 3).forEach(line => {
      console.log(`  ${line}`);
    });
  }
}

/**
 * Display learning report
 */
function displayReport() {
  logSection('Learning System Report');

  // Read from the persisted database (loaded by PatternMatcher on construction)
  // so the report reflects what's actually on disk, not just this process.
  const persisted = patternMatcher.patterns || [];
  const stats = patternMatcher.getStatistics();

  console.log(`${COLORS.bold}Overview:${COLORS.reset}`);
  console.log(`  Total Patterns Learned: ${stats.totalPatterns}`);
  console.log(`  Total Failures: ${failureCollector.loadFailures().length}`);
  console.log(`  Avg Confidence: ${(stats.avgConfidence * 100).toFixed(0)}%`);

  if (Object.keys(stats.byType).length > 0) {
    console.log(`\n${COLORS.bold}Patterns by Type:${COLORS.reset}`);
    for (const [type, count] of Object.entries(stats.byType)) {
      console.log(`  ${type}: ${count} patterns`);
    }
  }

  const topPatterns = [...persisted]
    .sort((a, b) => (b.occurrences || 0) - (a.occurrences || 0))
    .slice(0, 5);

  if (topPatterns.length > 0) {
    console.log(`\n${COLORS.bold}Top Patterns:${COLORS.reset}`);
    topPatterns.forEach((p, idx) => {
      const confColor = p.confidence >= 0.8 ? 'green' : p.confidence >= 0.6 ? 'yellow' : 'red';
      const confPercent = Math.round(p.confidence * 100);
      log(confColor, `  ${idx + 1}. ${String(p.pattern).substring(0, 50)} (${confPercent}% - ${p.occurrences}x)`);
    });
  } else {
    console.log(`\n${COLORS.dim}No patterns learned yet. Run tests, then "npm run qa:learn".${COLORS.reset}`);
  }

  console.log('');
}

/**
 * Display failure statistics
 */
function displayStats() {
  logSection('Failure Statistics');

  failureCollector.loadFailures();
  const allFailures = failureCollector.failures;
  const stats = failureCollector.getStatistics();

  console.log(`${COLORS.bold}Overall:${COLORS.reset}`);
  console.log(`  Total Failures: ${allFailures.length}`);
  console.log(`  Unique Categories: ${Object.keys(stats.byCategory || {}).length}`);

  if (stats.byCategory) {
    console.log(`\n${COLORS.bold}Failures by Category:${COLORS.reset}`);
    for (const [cat, count] of Object.entries(stats.byCategory)) {
      console.log(`  ${cat}: ${count}`);
    }
  }

  if (stats.bySeverity) {
    console.log(`\n${COLORS.bold}Failures by Severity:${COLORS.reset}`);
    for (const [sev, count] of Object.entries(stats.bySeverity)) {
      console.log(`  ${sev}: ${count}`);
    }
  }

  console.log('');
}

/**
 * Show help message
 */
function showHelp() {
  console.log(`
${COLORS.bold}QA Learning System - Failure Analysis${COLORS.reset}

${COLORS.bold}Usage:${COLORS.reset}
  node scripts/analyze-failures.js <command> [options]

${COLORS.bold}Commands:${COLORS.reset}

  ${COLORS.cyan}collect${COLORS.reset}
    Collect a sample test failure
    
  ${COLORS.cyan}list${COLORS.reset}
    List recent failures
    
  ${COLORS.cyan}stats${COLORS.reset}
    Show failure statistics
    
  ${COLORS.cyan}learn${COLORS.reset}
    Learn patterns from collected failures
    
  ${COLORS.cyan}report${COLORS.reset}
    Show learning progress and pattern recommendations
    
  ${COLORS.cyan}match <code> ${COLORS.reset}
    Analyze code for potential issues
    
  ${COLORS.cyan}clear${COLORS.reset}
    Clear all collected failures
    
  ${COLORS.cyan}demo${COLORS.reset}
    Run a complete learning demo with sample data

${COLORS.bold}Examples:${COLORS.reset}
  # Collect and analyze failures
  node scripts/analyze-failures.js collect
  node scripts/analyze-failures.js stats
  
  # Learn from failures and get suggestions
  node scripts/analyze-failures.js learn
  node scripts/analyze-failures.js report
  
  # Run full demo
  node scripts/analyze-failures.js demo
`);
}

/**
 * Run a complete learning demo
 */
function runDemo() {
  logSection('Learning System Demo');

  // Step 1: Collect sample failures
  console.log(`${COLORS.bold}Step 1: Collecting Sample Failures${COLORS.reset}\n`);
  const failures = [];
  for (let i = 0; i < 5; i++) {
    const failure = collectSampleFailure();
    failures.push(failure);
    console.log(`✓ Collected: ${failure.testName}`);
  }

  // Step 2: Show failure stats
  console.log(`\n${COLORS.bold}Step 2: Analyzing Failures${COLORS.reset}`);
  displayStats();

  // Step 3: Learn patterns
  console.log(`${COLORS.bold}Step 3: Learning Patterns from Failures${COLORS.reset}`);
  failureCollector.loadFailures();
  const unlearned = failureCollector.getUnlearned();
  patternLearner.learn(unlearned);
  const stats = patternLearner.getStatistics();
  console.log(`✓ Learned ${stats.totalPatterns} patterns from ${unlearned.length} failures\n`);

  // Step 4: Show learning report
  console.log(`${COLORS.bold}Step 4: Learning Report${COLORS.reset}`);
  displayReport();

  // Step 5: Analyze code
  if (stats.totalPatterns > 0) {
    console.log(`${COLORS.bold}Step 5: Analyzing Code for Issues${COLORS.reset}\n`);
    const sampleCode = `
      dialog.addEventListener('click', (e) => {
        if (e.target.style.pointerEvents === 'auto') {
          dialog.style.display = 'none';
        }
      });
    `;
    const issues = patternMatcher.analyzeCode(sampleCode, { type: 'dialog' });
    console.log(`Found ${issues.length} potential issues:\n`);
    
    if (issues.length > 0) {
      issues.slice(0, 3).forEach((issue, idx) => {
        console.log(`  ${idx + 1}. Pattern: ${issue.pattern.substring(0, 50)}`);
        console.log(`     Type: ${issue.type}`);
        console.log(`     Score: ${(issue.score * 100).toFixed(0)}%\n`);
      });
    } else {
      console.log('  No issues detected in sample code\n');
    }
  }

  log('green', '\n✓ Demo completed successfully!\n');
}

// Main CLI
const command = process.argv[2];
const args = process.argv.slice(3);

switch (command) {
  case 'collect':
    logSection('Collecting Sample Failure');
    const failure = collectSampleFailure();
    displayFailure(failure);
    log('green', '\n✓ Failure collected and stored\n');
    break;

  case 'list':
    logSection('Recent Failures');
    failureCollector.loadFailures();
    const failuresList = failureCollector.getRecent(20);
    
    if (failuresList.length === 0) {
      log('dim', 'No failures found');
    } else {
      failuresList.forEach((f, idx) => {
        console.log(`${idx + 1}. ${f.testName}`);
        console.log(`   Category: ${f.category}`);
        console.log(`   Error: ${f.errorMessage.substring(0, 60)}`);
        console.log(`   Time: ${f.timestamp}\n`);
      });
    }
    break;

  case 'stats':
    displayStats();
    break;

  case 'learn': {
    logSection('Learning from Failures');
    failureCollector.loadFailures();
    const unlearned = failureCollector.getUnlearned();
    console.log(`Processing ${unlearned.length} unlearned failures...\n`);

    const learnedPatterns = patternLearner.learn(unlearned);
    const learnedStats = patternLearner.getStatistics();

    // Persist learned patterns to learned_patterns.json so the matcher and
    // future runs can use them. Without this, learning is thrown away each run.
    patternMatcher.updatePatterns(learnedPatterns);

    // Mark each failure as learned and link it to the pattern it produced, so
    // subsequent `learn` runs only process new failures.
    let markedCount = 0;
    for (const failure of unlearned) {
      const owningPattern = learnedPatterns.find(p => p.failures.includes(failure.id));
      failureCollector.markLearned(failure.id, owningPattern ? owningPattern.id : null);
      markedCount++;
    }

    console.log(`✓ Learned ${learnedStats.totalPatterns} patterns`);
    console.log(`✓ Persisted to qa/learning/learned_patterns.json`);
    console.log(`✓ Marked ${markedCount} failures as learned\n`);

    if (learnedStats.topPatterns && learnedStats.topPatterns.length > 0) {
      learnedStats.topPatterns.slice(0, 5).forEach((p, idx) => {
        console.log(`${idx + 1}. Pattern (${p.occurrences}x)`);
        console.log(`   Confidence: ${(p.confidence * 100).toFixed(0)}%`);
        console.log(`   Pattern: ${p.pattern.substring(0, 60)}\n`);
      });
    }
    break;
  }

  case 'report':
    displayReport();
    break;

  case 'clear':
    failureCollector.clear();
    logSection('Cleared Failures');
    console.log(`✓ All failures cleared\n`);
    break;

  case 'demo':
    runDemo();
    break;

  case 'help':
  case '--help':
  case '-h':
    showHelp();
    break;

  default:
    showHelp();
}
