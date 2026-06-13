#!/usr/bin/env node

/**
 * QA Learning Cron Job
 * Automatically learns patterns from test failures on a schedule
 *
 * Usage:
 *   node scripts/cron-learn.js --interval 3600000    # Every hour
 *   node scripts/cron-learn.js --interval 86400000   # Every day
 *   npm run qa:cron                                    # Uses default (30 min)
 */

const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');

const COLORS = {
  reset: '\x1b[0m',
  bold: '\x1b[1m',
  dim: '\x1b[2m',
  green: '\x1b[32m',
  yellow: '\x1b[33m',
  red: '\x1b[31m',
  blue: '\x1b[34m',
};

function log(color, message) {
  const timestamp = new Date().toISOString();
  console.log(`${COLORS[color]}[${timestamp}] ${message}${COLORS.reset}`);
}

function getFailureCount() {
  try {
    const failuresDir = path.join(__dirname, '../failures');
    if (!fs.existsSync(failuresDir)) return 0;
    const files = fs.readdirSync(failuresDir);
    return files.filter(f => f.startsWith('failure_')).length;
  } catch (err) {
    return 0;
  }
}

function getLastLearnTime() {
  try {
    const patternsFile = path.join(__dirname, '../qa/learning/learned_patterns.json');
    const data = JSON.parse(fs.readFileSync(patternsFile, 'utf8'));
    return data.lastUpdated ? new Date(data.lastUpdated) : null;
  } catch (err) {
    return null;
  }
}

function runLearn() {
  log('blue', '🔄 Starting pattern learning...');

  const failureCount = getFailureCount();
  if (failureCount === 0) {
    log('dim', '   No new failures to learn from');
    return false;
  }

  log('bold', `   Found ${failureCount} failure(s) to process`);

  try {
    const output = execSync('npm run qa:learn', {
      cwd: path.join(__dirname, '..'),
      encoding: 'utf8',
    });

    // Extract pattern count from output
    const patternMatch = output.match(/Learned (\d+) patterns/);
    const markedMatch = output.match(/Marked (\d+) failures/);

    if (patternMatch && markedMatch) {
      const patterns = patternMatch[1];
      const marked = markedMatch[1];
      log('green', `✓ Learning complete: ${patterns} patterns, ${marked} failures marked`);
      return true;
    } else {
      log('yellow', '⚠ Learning completed but output parsing failed');
      return false;
    }
  } catch (err) {
    log('red', `✗ Learning failed: ${err.message}`);
    return false;
  }
}

function formatInterval(ms) {
  if (ms < 60000) return `${Math.floor(ms / 1000)}s`;
  if (ms < 3600000) return `${Math.floor(ms / 60000)}m`;
  if (ms < 86400000) return `${Math.floor(ms / 3600000)}h`;
  return `${Math.floor(ms / 86400000)}d`;
}

// Parse command line args
const args = process.argv.slice(2);
let interval = 30 * 60 * 1000; // Default: 30 minutes

for (let i = 0; i < args.length; i++) {
  if (args[i] === '--interval' && args[i + 1]) {
    const parsed = parseInt(args[i + 1], 10);
    if (!isNaN(parsed)) {
      interval = parsed;
      i++;
    }
  }
}

// Log startup
console.log('\n' + '='.repeat(70));
log('bold', '🎯 QA Learning Cron Job');
console.log('='.repeat(70) + '\n');

log('green', `✓ Cron job started`);
log('bold', `  Interval: ${formatInterval(interval)}`);
log('dim', `  Next run: in ${formatInterval(interval)}`);
log('dim', `  Press Ctrl+C to stop\n`);

// Run once on startup
const lastLearn = getLastLearnTime();
if (lastLearn) {
  const minutesAgo = Math.floor((Date.now() - lastLearn.getTime()) / 60000);
  log('dim', `  Last learning: ${minutesAgo} minutes ago`);
}

// Initial run
runLearn();

// Set up interval
let runCount = 0;
const timerId = setInterval(() => {
  runCount++;
  log('dim', `\n📅 Scheduled run #${runCount}`);
  runLearn();
  log('dim', `   Next run: in ${formatInterval(interval)}`);
}, interval);

// Graceful shutdown
process.on('SIGINT', () => {
  clearInterval(timerId);
  log('green', `\n✓ Cron job stopped (ran ${runCount} times)\n`);
  process.exit(0);
});

// Keep process alive
process.on('uncaughtException', (err) => {
  log('red', `Uncaught error: ${err.message}`);
  // Continue running despite errors
});
