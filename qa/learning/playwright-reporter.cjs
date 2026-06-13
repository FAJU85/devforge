/**
 * Playwright Reporter - Feeds real test failures into the QA learning system.
 *
 * Wired into playwright.config.ts via the `reporter` array. On every failed or
 * timed-out test, it captures the failure (name, file, error, stack) through
 * FailureCollector so the learning system trains on real data, not demo data.
 *
 * Safety: every learning-system call is wrapped so a fault here can never break
 * or fail the actual test run.
 */

const FailureCollector = require('./failure_collector');

// Strip ANSI color codes that Playwright embeds in error messages/stacks.
function stripAnsi(input) {
  if (!input) return '';
  // eslint-disable-next-line no-control-regex
  return String(input).replace(/\x1b\[[0-9;]*m/g, '');
}

class LearningReporter {
  constructor() {
    try {
      this.collector = new FailureCollector();
    } catch (err) {
      this.collector = null;
      console.error(`[learning-reporter] init failed: ${err.message}`);
    }
    this.captured = 0;
  }

  onTestEnd(test, result) {
    if (!this.collector) return;
    if (result.status !== 'failed' && result.status !== 'timedOut') return;

    try {
      const error = result.error || {};
      this.collector.collect({
        testName: test.titlePath().filter(Boolean).join(' > ') || test.title,
        testFile: test.location ? test.location.file : 'playwright',
        errorMessage: stripAnsi(error.message) || `Test ${result.status}`,
        stackTrace: stripAnsi(error.stack),
        context: {
          framework: 'playwright',
          status: result.status,
          durationMs: result.duration,
          retry: result.retry,
          line: test.location ? test.location.line : null,
        },
        severity: 'high',
        // status 'timedOut' -> let collector categorize as timeout via message,
        // but be explicit so it's correct even when the message is empty.
        category: result.status === 'timedOut' ? 'timeout' : undefined,
      });
      this.captured++;
    } catch (err) {
      console.error(`[learning-reporter] capture failed: ${err.message}`);
    }
  }

  onEnd() {
    if (this.captured > 0) {
      console.log(
        `\n[learning-reporter] captured ${this.captured} failure(s) into the QA learning store. ` +
          `Run "npm run qa:learn" to update patterns.`
      );
    }
  }
}

module.exports = LearningReporter;
