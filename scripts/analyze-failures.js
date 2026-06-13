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

// Error handler wrapper
function safeRequire(modulePath, moduleName) {
  try {
    return require(modulePath);
  } catch (err) {
    console.error(`\n❌ Error: Failed to load ${moduleName}`);
    console.error(`   Path: ${modulePath}`);
    console.error(`   Error: ${err.message}\n`);
    process.exit(1);
  }
}

const FailureCollector = safeRequire('../qa/learning/failure_collector', 'FailureCollector');
const PatternLearner = safeRequire('../qa/learning/pattern_learner', 'PatternLearner');
const PatternMatcher = safeRequire('../qa/learning/pattern_matcher', 'PatternMatcher');
const SuggestionGenerator = safeRequire('../qa/learning/suggestion_generator', 'SuggestionGenerator');

// Create instances with error handling
let failureCollector, patternLearner, patternMatcher, suggestionGenerator;
try {
  failureCollector = new FailureCollector();
  patternLearner = new PatternLearner();
  patternMatcher = new PatternMatcher();
  suggestionGenerator = new SuggestionGenerator();
} catch (err) {
  console.error(`\n❌ Error initializing QA system: ${err.message}\n`);
  process.exit(1);
}

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

// Progress bar for processing
function createProgressBar(total) {
  let current = 0;
  return {
    update: (count = 1) => {
      current += count;
      const percent = Math.floor((current / total) * 100);
      const filled = Math.floor(percent / 2);
      const empty = 50 - filled;
      const bar = '█'.repeat(filled) + '░'.repeat(empty);
      process.stdout.write(`\r  Processing: [${bar}] ${percent}% (${current}/${total})`);
    },
    finish: () => {
      process.stdout.write('\r' + ' '.repeat(70) + '\r');
    }
  };
}

// Input validation
function validateCommand(command) {
  const valid = ['collect', 'list', 'stats', 'learn', 'report', 'match', 'clear', 'demo', 'help'];
  if (command && !valid.includes(command)) {
    log('red', `\n❌ Unknown command: "${command}"`);
    log('dim', `\n   Valid commands: ${valid.join(', ')}\n`);
    return false;
  }
  return true;
}

function validateDirectory(dirPath) {
  try {
    return fs.statSync(dirPath).isDirectory();
  } catch (err) {
    return false;
  }
}

function validateFile(filePath) {
  try {
    return fs.statSync(filePath).isFile();
  } catch (err) {
    return false;
  }
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

// Main CLI with comprehensive error handling
const command = process.argv[2];
const args = process.argv.slice(3);

// Validate command before executing
if (command && !['collect', 'list', 'stats', 'learn', 'report', 'match', 'clear', 'demo', 'help', '--help', '-h'].includes(command)) {
  validateCommand(command);
  process.exit(1);
}

try {
  switch (command) {
    case 'collect':
      try {
        logSection('Collecting Sample Failure');
        const failure = collectSampleFailure();
        displayFailure(failure);
        log('green', '\n✓ Failure collected and stored\n');
      } catch (err) {
        log('red', `\n❌ Error collecting failure: ${err.message}\n`);
        process.exit(1);
      }
      break;

    case 'list':
      try {
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
      } catch (err) {
        log('red', `\n❌ Error listing failures: ${err.message}\n`);
        process.exit(1);
      }
      break;

    case 'stats':
      try {
        displayStats();
      } catch (err) {
        log('red', `\n❌ Error displaying stats: ${err.message}\n`);
        process.exit(1);
      }
      break;

  case 'learn': {
    try {
      logSection('Learning from Failures');

      failureCollector.loadFailures();
      const unlearned = failureCollector.getUnlearned();

      if (unlearned.length === 0) {
        log('yellow', '⚠ No unlearned failures found.');
        log('dim', '   Run tests first to capture failures, then try again.\n');
        break;
      }

      console.log(`Processing ${unlearned.length} unlearned failures...\n`);

      // Pattern learning with progress
      const progress = createProgressBar(unlearned.length);
      const learnedPatterns = patternLearner.learn(unlearned);
      progress.finish();

      const learnedStats = patternLearner.getStatistics();

      // Persist learned patterns to learned_patterns.json so the matcher and
      // future runs can use them. Without this, learning is thrown away each run.
      patternMatcher.updatePatterns(learnedPatterns);

      // Mark each failure as learned and link it to the pattern it produced, so
      // subsequent `learn` runs only process new failures.
      const markProgress = createProgressBar(unlearned.length);
      let markedCount = 0;
      for (const failure of unlearned) {
        const owningPattern = learnedPatterns.find(p => p.failures.includes(failure.id));
        failureCollector.markLearned(failure.id, owningPattern ? owningPattern.id : null);
        markedCount++;
        markProgress.update(1);
      }
      markProgress.finish();

      console.log(`\n✓ Learned ${learnedStats.totalPatterns} patterns`);
      console.log(`✓ Persisted to qa/learning/learned_patterns.json`);
      console.log(`✓ Marked ${markedCount} failures as learned\n`);

      if (learnedStats.topPatterns && learnedStats.topPatterns.length > 0) {
        console.log(`${COLORS.bold}Top Patterns:${COLORS.reset}`);
        learnedStats.topPatterns.slice(0, 5).forEach((p, idx) => {
          const confColor = p.confidence >= 0.8 ? 'green' : p.confidence >= 0.6 ? 'yellow' : 'red';
          log(confColor, `  ${idx + 1}. Pattern (${p.occurrences}x) - ${(p.confidence * 100).toFixed(0)}% confidence`);
          console.log(`     ${p.pattern.substring(0, 60)}`);
        });
        console.log('');
      }
    } catch (err) {
      log('red', `\n❌ Error during learning: ${err.message}`);
      console.error(`   Stack: ${err.stack}\n`);
      process.exit(1);
    }
    break;
  }

    case 'report':
      try {
        displayReport();
      } catch (err) {
        log('red', `\n❌ Error generating report: ${err.message}\n`);
        process.exit(1);
      }
      break;

    case 'clear':
      try {
        failureCollector.clear();
        logSection('Cleared Failures');
        console.log(`✓ All failures cleared\n`);
      } catch (err) {
        log('red', `\n❌ Error clearing failures: ${err.message}\n`);
        process.exit(1);
      }
      break;

    case 'demo':
      try {
        runDemo();
      } catch (err) {
        log('red', `\n❌ Error running demo: ${err.message}\n`);
        console.error(`   Stack: ${err.stack}\n`);
        process.exit(1);
      }
      break;

    case 'help':
    case '--help':
    case '-h':
      showHelp();
      break;

    default:
      showHelp();
  }
} catch (err) {
  log('red', `\n❌ Unexpected error: ${err.message}\n`);
  console.error(`   Stack: ${err.stack}\n`);
  process.exit(1);
}
