/**
 * Failure Collector - Captures test failures and extracts context
 * Automatically collects and structures test failure data for pattern learning
 */

const fs = require('fs');
const path = require('path');

class FailureCollector {
  constructor(options = {}) {
    this.options = {
      storageDir: options.storageDir || path.join(__dirname, '../../failures'),
      maxFailuresPerType: options.maxFailuresPerType || 100,
      ...options
    };

    this.failures = [];
    this.ensureStorageDir();
  }

  /**
   * Ensure storage directory exists
   */
  ensureStorageDir() {
    if (!fs.existsSync(this.options.storageDir)) {
      fs.mkdirSync(this.options.storageDir, { recursive: true });
    }
  }

  /**
   * Collect a test failure with full context
   * @param {Object} failure - Failure data
   * @param {string} failure.testName - Name of the failing test
   * @param {string} failure.testFile - Path to test file
   * @param {string} failure.errorMessage - Error message
   * @param {string} failure.stackTrace - Full stack trace
   * @param {string} failure.testCode - The actual test code that failed
   * @param {Object} failure.context - Additional context
   * @param {string} failure.severity - 'critical', 'high', 'medium', 'low'
   * @param {string} failure.category - Error category (e.g., 'assertion', 'timeout', 'selenium')
   * @returns {Object} Collected failure record
   */
  collect(failure) {
    if (!failure.testName || !failure.errorMessage) {
      throw new Error('failure.testName and failure.errorMessage are required');
    }

    const timestamp = new Date().toISOString();
    const failureRecord = {
      id: this.generateId(),
      timestamp,
      testName: failure.testName,
      testFile: failure.testFile || 'unknown',
      errorMessage: failure.errorMessage,
      stackTrace: failure.stackTrace || '',
      testCode: failure.testCode || '',
      context: failure.context || {},
      severity: failure.severity || 'medium',
      category: failure.category || this.categorizeError(failure.errorMessage),
      learned: false,
      patternId: null
    };

    this.failures.push(failureRecord);
    this.persistFailure(failureRecord);

    return failureRecord;
  }

  /**
   * Collect failure from Selenium test result
   * @param {Object} testResult - Selenium test result object
   * @returns {Object} Collected failure record
   */
  collectFromSelenium(testResult) {
    return this.collect({
      testName: testResult.name || 'Unknown Selenium Test',
      testFile: testResult.file || 'selenium',
      errorMessage: testResult.error?.message || testResult.message || 'Selenium test failed',
      stackTrace: testResult.error?.stack || '',
      testCode: testResult.code || '',
      context: {
        browser: testResult.browser || 'chrome',
        url: testResult.url || null,
        screenshot: testResult.screenshot || null,
        selector: testResult.selector || null,
        timeout: testResult.timeout || null
      },
      severity: testResult.severity || 'high',
      category: this.categorizeSeleniumError(testResult.error?.message || '')
    });
  }

  /**
   * Collect failure from Pytest result
   * @param {Object} testResult - Pytest test result object
   * @returns {Object} Collected failure record
   */
  collectFromPytest(testResult) {
    return this.collect({
      testName: testResult.nodeid || 'Unknown Pytest Test',
      testFile: testResult.fspath || 'pytest',
      errorMessage: testResult.longrepr?.split('\n')[0] || 'Test failed',
      stackTrace: testResult.longrepr || '',
      testCode: testResult.code || '',
      context: {
        duration: testResult.duration || null,
        markers: testResult.markers || [],
        outcome: testResult.outcome
      },
      severity: this.calculateSeverity(testResult),
      category: this.categorizePytestError(testResult.longrepr || '')
    });
  }

  /**
   * Persist failure to file
   * @param {Object} failureRecord - Failure record to persist
   */
  persistFailure(failureRecord) {
    try {
      const filePath = path.join(this.options.storageDir, `${failureRecord.id}.json`);
      fs.writeFileSync(filePath, JSON.stringify(failureRecord, null, 2));
    } catch (error) {
      console.error(`Failed to persist failure: ${error.message}`);
    }
  }

  /**
   * Load all failures from storage
   * @returns {Array} Array of failure records
   */
  loadFailures() {
    try {
      if (!fs.existsSync(this.options.storageDir)) {
        return [];
      }

      const files = fs.readdirSync(this.options.storageDir).filter(f => f.endsWith('.json'));
      const failures = [];

      for (const file of files) {
        try {
          const data = fs.readFileSync(path.join(this.options.storageDir, file), 'utf8');
          failures.push(JSON.parse(data));
        } catch (error) {
          console.error(`Failed to load failure file ${file}: ${error.message}`);
        }
      }

      this.failures = failures;
      return failures;
    } catch (error) {
      console.error(`Failed to load failures: ${error.message}`);
      return [];
    }
  }

  /**
   * Get failures by category
   * @param {string} category - Error category
   * @returns {Array} Filtered failures
   */
  getByCategory(category) {
    return this.failures.filter(f => f.category === category);
  }

  /**
   * Get failures by severity
   * @param {string} severity - Severity level
   * @returns {Array} Filtered failures
   */
  getBySeverity(severity) {
    return this.failures.filter(f => f.severity === severity);
  }

  /**
   * Get recent failures
   * @param {number} limit - Number of recent failures to return
   * @returns {Array} Recent failures
   */
  getRecent(limit = 10) {
    return this.failures
      .sort((a, b) => new Date(b.timestamp) - new Date(a.timestamp))
      .slice(0, limit);
  }

  /**
   * Get unlearned failures
   * @returns {Array} Failures that haven't been learned yet
   */
  getUnlearned() {
    return this.failures.filter(f => !f.learned);
  }

  /**
   * Mark failure as learned
   * @param {string} failureId - Failure ID
   * @param {string} patternId - Pattern ID that matched this failure
   */
  markLearned(failureId, patternId) {
    const failure = this.failures.find(f => f.id === failureId);
    if (failure) {
      failure.learned = true;
      failure.patternId = patternId;
      this.persistFailure(failure);
    }
  }

  /**
   * Categorize error based on message
   * @param {string} errorMessage - Error message
   * @returns {string} Error category
   */
  categorizeError(errorMessage) {
    const msg = errorMessage.toLowerCase();

    if (msg.includes('assert') || msg.includes('expected')) return 'assertion';
    if (msg.includes('timeout') || msg.includes('timed out')) return 'timeout';
    if (msg.includes('not found') || msg.includes('no such element')) return 'element_not_found';
    if (msg.includes('stale') || msg.includes('element is no longer attached')) return 'stale_element';
    if (msg.includes('click') && msg.includes('obscured')) return 'element_obscured';
    if (msg.includes('network') || msg.includes('connection')) return 'network';
    if (msg.includes('type error') || msg.includes('syntax')) return 'code_error';

    return 'other';
  }

  /**
   * Categorize Selenium-specific errors
   * @param {string} errorMessage - Error message
   * @returns {string} Error category
   */
  categorizeSeleniumError(errorMessage) {
    const category = this.categorizeError(errorMessage);
    if (category !== 'other') return category;

    const msg = errorMessage.toLowerCase();
    if (msg.includes('move to element')) return 'move_to_element_failed';
    if (msg.includes('send keys')) return 'send_keys_failed';
    if (msg.includes('click')) return 'click_failed';
    if (msg.includes('switch')) return 'switch_failed';

    return 'selenium_error';
  }

  /**
   * Categorize Pytest-specific errors
   * @param {string} errorMessage - Error message
   * @returns {string} Error category
   */
  categorizePytestError(errorMessage) {
    const category = this.categorizeError(errorMessage);
    if (category !== 'other') return category;

    const msg = errorMessage.toLowerCase();
    if (msg.includes('fixture') || msg.includes('setup')) return 'fixture_error';
    if (msg.includes('import')) return 'import_error';
    if (msg.includes('mark')) return 'marker_error';

    return 'pytest_error';
  }

  /**
   * Calculate severity from Pytest result
   * @param {Object} testResult - Pytest result
   * @returns {string} Severity level
   */
  calculateSeverity(testResult) {
    const markers = testResult.markers || [];

    if (markers.includes('smoke') || markers.includes('critical')) return 'critical';
    if (markers.includes('regression')) return 'high';
    if (markers.includes('slow')) return 'low';

    return 'medium';
  }

  /**
   * Generate unique failure ID
   * @returns {string} Unique ID
   */
  generateId() {
    return `failure_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
  }

  /**
   * Get statistics about collected failures
   * @returns {Object} Statistics
   */
  getStatistics() {
    const categories = {};
    const severities = { critical: 0, high: 0, medium: 0, low: 0 };
    let learned = 0;

    for (const failure of this.failures) {
      categories[failure.category] = (categories[failure.category] || 0) + 1;
      severities[failure.severity] = (severities[failure.severity] || 0) + 1;
      if (failure.learned) learned++;
    }

    return {
      total: this.failures.length,
      learned,
      unlearned: this.failures.length - learned,
      byCategory: categories,
      bySeverity: severities,
      learningProgress: this.failures.length > 0
        ? ((learned / this.failures.length) * 100).toFixed(2) + '%'
        : '0%'
    };
  }

  /**
   * Clear all collected failures
   */
  clear() {
    try {
      const files = fs.readdirSync(this.options.storageDir);
      for (const file of files) {
        if (file.endsWith('.json')) {
          fs.unlinkSync(path.join(this.options.storageDir, file));
        }
      }
      this.failures = [];
    } catch (error) {
      console.error(`Failed to clear failures: ${error.message}`);
    }
  }
}

module.exports = FailureCollector;
