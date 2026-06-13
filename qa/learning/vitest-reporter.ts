/**
 * Vitest Reporter - Feeds real unit/integration/UI test failures into the QA
 * learning system. Wired into vitest.config.ts via the `reporters` array.
 *
 * Uses the Vitest 4 "Reported Tasks" API (onTestCaseResult / onTestRunEnd).
 * Vitest runs in an ESM/TS context, so we bridge to the CommonJS
 * FailureCollector with createRequire. Every learning call is wrapped so a
 * fault here can never break the actual test run.
 */

import { createRequire } from 'node:module';

const require = createRequire(import.meta.url);
const FailureCollector = require('./failure_collector');

export default class LearningVitestReporter {
  private collector: any;
  private captured = 0;

  constructor() {
    try {
      this.collector = new FailureCollector();
    } catch (err) {
      this.collector = null;
      // eslint-disable-next-line no-console
      console.error(`[learning-reporter] init failed: ${(err as Error).message}`);
    }
  }

  // Vitest 4: called once per test case when it finishes.
  onTestCaseResult(testCase: any) {
    if (!this.collector) return;

    try {
      const result = typeof testCase.result === 'function' ? testCase.result() : testCase.result;
      if (!result || result.state !== 'failed') return;

      const error = (result.errors && result.errors[0]) || {};
      const filePath =
        (testCase.module && testCase.module.moduleId) ||
        (testCase.file && testCase.file.filepath) ||
        'vitest';

      this.collector.collect({
        testName: testCase.fullName || testCase.name || 'Unknown Vitest test',
        testFile: filePath,
        errorMessage: error.message || 'Vitest test failed',
        stackTrace: error.stack || '',
        context: {
          framework: 'vitest',
        },
        severity: 'high',
      });
      this.captured++;
    } catch (e) {
      // eslint-disable-next-line no-console
      console.error(`[learning-reporter] capture failed: ${(e as Error).message}`);
    }
  }

  onTestRunEnd() {
    if (this.captured > 0) {
      // eslint-disable-next-line no-console
      console.log(
        `\n[learning-reporter] captured ${this.captured} failure(s) into the QA learning store. ` +
          `Run "npm run qa:learn" to update patterns.`
      );
    }
  }
}
