/**
 * Pattern Matcher - Matches code against learned patterns
 * Detects potential issues based on learned failure patterns
 */

const fs = require('fs');
const path = require('path');

class PatternMatcher {
  constructor(options = {}) {
    this.options = {
      patternsFile: options.patternsFile || path.join(__dirname, 'learned_patterns.json'),
      minMatchScore: options.minMatchScore || 0.5,
      ...options
    };

    this.patterns = this.loadPatterns();
  }

  /**
   * Load patterns from storage
   * @returns {Array} Loaded patterns
   */
  loadPatterns() {
    try {
      if (!fs.existsSync(this.options.patternsFile)) {
        return [];
      }
      const data = fs.readFileSync(this.options.patternsFile, 'utf8');
      const stored = JSON.parse(data);
      return stored.patterns || [];
    } catch (error) {
      console.error(`Failed to load patterns: ${error.message}`);
      return [];
    }
  }

  /**
   * Save patterns to storage
   * @param {Array} patterns - Patterns to save
   */
  savePatterns(patterns) {
    try {
      const data = {
        patterns,
        lastUpdated: new Date().toISOString(),
        version: '1.0'
      };
      fs.writeFileSync(this.options.patternsFile, JSON.stringify(data, null, 2));
    } catch (error) {
      console.error(`Failed to save patterns: ${error.message}`);
    }
  }

  /**
   * Update patterns from pattern learner
   * @param {Array} patterns - New patterns from learner
   */
  updatePatterns(patterns) {
    this.patterns = patterns;
    this.savePatterns(patterns);
  }

  /**
   * Analyze code for potential issues
   * @param {string} code - Code to analyze
   * @param {Object} context - Additional context (filename, type, etc.)
   * @returns {Array} Detected issues
   */
  analyzeCode(code, context = {}) {
    const issues = [];

    for (const pattern of this.patterns) {
      const match = this.matchPattern(code, pattern, context);
      if (match && match.score >= this.options.minMatchScore) {
        issues.push({
          patternId: pattern.id,
          pattern: pattern.pattern,
          type: pattern.type,
          score: match.score,
          confidence: pattern.confidence,
          severity: pattern.severity,
          location: match.location,
          message: this.generateMessage(pattern, match)
        });
      }
    }

    // Sort by score descending
    return issues.sort((a, b) => b.score - a.score);
  }

  /**
   * Match a pattern against code
   * @param {string} code - Code to analyze
   * @param {Object} pattern - Pattern to match
   * @param {Object} context - Context information
   * @returns {Object|null} Match details or null
   */
  matchPattern(code, pattern, context = {}) {
    switch (pattern.type) {
      case 'message':
        return this.matchMessagePattern(code, pattern);
      case 'stack_trace':
        return this.matchStackPattern(code, pattern);
      case 'category':
        return this.matchCategoryPattern(code, pattern, context);
      case 'context_browser':
        return this.matchBrowserPattern(code, pattern, context);
      case 'context_selector':
        return this.matchSelectorPattern(code, pattern);
      default:
        return null;
    }
  }

  /**
   * Match message pattern against code
   * @param {string} code - Code
   * @param {Object} pattern - Pattern
   * @returns {Object|null} Match details
   */
  matchMessagePattern(code, pattern) {
    const tokens = pattern.pattern.split(':');
    let matchCount = 0;
    let lineNumber = 1;
    let matchedLine = '';

    const lines = code.split('\n');
    for (let i = 0; i < lines.length; i++) {
      const line = lines[i];
      const lineTokens = this.tokenize(line);

      for (const token of tokens) {
        if (lineTokens.includes(token)) {
          matchCount++;
          lineNumber = i + 1;
          matchedLine = line.trim();
        }
      }
    }

    const score = matchCount / tokens.length;
    if (score > 0.5) {
      return {
        score,
        location: { line: lineNumber, code: matchedLine },
        context: { matchedTokens: matchCount, totalTokens: tokens.length }
      };
    }

    return null;
  }

  /**
   * Match stack trace pattern
   * @param {string} code - Code
   * @param {Object} pattern - Pattern
   * @returns {Object|null} Match details
   */
  matchStackPattern(code, pattern) {
    if (code.includes(pattern.function) && code.includes(pattern.file)) {
      return {
        score: 0.9,
        location: { line: null, code: `Function: ${pattern.function} in ${pattern.file}` },
        context: { function: pattern.function, file: pattern.file }
      };
    }

    if (code.includes(pattern.function)) {
      return {
        score: 0.7,
        location: { line: null, code: `Function: ${pattern.function}` },
        context: { function: pattern.function }
      };
    }

    return null;
  }

  /**
   * Match category pattern
   * @param {string} code - Code
   * @param {Object} pattern - Pattern
   * @param {Object} context - Context
   * @returns {Object|null} Match details
   */
  matchCategoryPattern(code, pattern, context = {}) {
    const category = pattern.category;

    // Check for assertion-related patterns
    if (category === 'assertion' && code.includes('assert')) {
      return {
        score: 0.8,
        location: { line: null, code: 'Contains assertions' },
        context: { category }
      };
    }

    // Check for timeout-related patterns
    if (category === 'timeout' && (code.includes('timeout') || code.includes('wait'))) {
      return {
        score: 0.8,
        location: { line: null, code: 'Contains timeout/wait logic' },
        context: { category }
      };
    }

    // Check for element-related patterns
    if (
      (category === 'element_not_found' || category === 'stale_element') &&
      (code.includes('find_element') || code.includes('querySelector'))
    ) {
      return {
        score: 0.7,
        location: { line: null, code: 'Contains element query logic' },
        context: { category }
      };
    }

    // Check for click-related patterns
    if (category === 'click_failed' && code.includes('click')) {
      return {
        score: 0.75,
        location: { line: null, code: 'Contains click logic' },
        context: { category }
      };
    }

    return null;
  }

  /**
   * Match browser pattern
   * @param {string} code - Code
   * @param {Object} pattern - Pattern
   * @param {Object} context - Context
   * @returns {Object|null} Match details
   */
  matchBrowserPattern(code, pattern, context = {}) {
    if (context.browser === pattern.browser) {
      return {
        score: 0.9,
        location: { line: null, code: `Browser: ${pattern.browser}` },
        context: { browser: pattern.browser }
      };
    }

    if (code.includes(pattern.browser)) {
      return {
        score: 0.7,
        location: { line: null, code: `Mentions ${pattern.browser}` },
        context: { browser: pattern.browser }
      };
    }

    return null;
  }

  /**
   * Match selector pattern
   * @param {string} code - Code
   * @param {Object} pattern - Pattern
   * @returns {Object|null} Match details
   */
  matchSelectorPattern(code, pattern) {
    if (code.includes(pattern.selector)) {
      return {
        score: 0.95,
        location: { line: null, code: `Selector: ${pattern.selector}` },
        context: { selector: pattern.selector }
      };
    }

    return null;
  }

  /**
   * Tokenize code into meaningful tokens
   * @param {string} code - Code line
   * @returns {Array} Tokens
   */
  tokenize(code) {
    return code
      .toLowerCase()
      .split(/[\s\n\t,.:;'"()\[\]{}]/g)
      .filter(token => token.length > 1);
  }

  /**
   * Generate human-readable message for issue
   * @param {Object} pattern - Pattern
   * @param {Object} match - Match details
   * @returns {string} Message
   */
  generateMessage(pattern, match) {
    switch (pattern.type) {
      case 'message':
        return `Potential issue detected: Similar to previous failure pattern (confidence: ${(pattern.confidence * 100).toFixed(0)}%)`;
      case 'category':
        return `Detected ${pattern.category} risk: This code type has previously failed`;
      case 'context_browser':
        return `Browser-specific issue detected: ${pattern.browser} has shown this failure pattern`;
      case 'context_selector':
        return `Selector issue detected: "${pattern.selector}" has previously failed to locate elements`;
      case 'stack_trace':
        return `Function risk detected: ${pattern.function} appears in failure stack traces`;
      default:
        return 'Potential issue detected based on learned patterns';
    }
  }

  /**
   * Analyze test file for issues
   * @param {string} filePath - Path to test file
   * @returns {Array} Issues found
   */
  analyzeFile(filePath) {
    try {
      const code = fs.readFileSync(filePath, 'utf8');
      const context = {
        filename: path.basename(filePath),
        directory: path.dirname(filePath),
        type: path.extname(filePath).substring(1)
      };
      return this.analyzeCode(code, context);
    } catch (error) {
      console.error(`Failed to analyze file ${filePath}: ${error.message}`);
      return [];
    }
  }

  /**
   * Analyze directory of test files
   * @param {string} dirPath - Path to directory
   * @returns {Object} Analysis results by file
   */
  analyzeDirectory(dirPath) {
    const results = {};

    try {
      const files = fs.readdirSync(dirPath)
        .filter(f => f.startsWith('test_') || f.endsWith('_test.js') || f.endsWith('_test.py'));

      for (const file of files) {
        const filePath = path.join(dirPath, file);
        const stats = fs.statSync(filePath);

        if (stats.isFile()) {
          results[file] = this.analyzeFile(filePath);
        }
      }
    } catch (error) {
      console.error(`Failed to analyze directory ${dirPath}: ${error.message}`);
    }

    return results;
  }

  /**
   * Get matching patterns for a failure
   * @param {Object} failure - Failure record
   * @returns {Array} Matching patterns
   */
  getMatchingPatterns(failure) {
    const matches = [];

    for (const pattern of this.patterns) {
      const score = this.calculateFailureMatchScore(failure, pattern);
      if (score > 0.3) {
        matches.push({
          patternId: pattern.id,
          pattern: pattern.pattern,
          type: pattern.type,
          score,
          confidence: pattern.confidence,
          severity: pattern.severity
        });
      }
    }

    return matches.sort((a, b) => b.score - a.score);
  }

  /**
   * Calculate match score between failure and pattern
   * @param {Object} failure - Failure
   * @param {Object} pattern - Pattern
   * @returns {number} Score 0-1
   */
  calculateFailureMatchScore(failure, pattern) {
    let score = 0;

    switch (pattern.type) {
      case 'category':
        if (failure.category === pattern.category) score = 1.0;
        break;
      case 'message':
        {
          const tokens = pattern.pattern.split(':');
          const msg = failure.errorMessage.toLowerCase();
          const matches = tokens.filter(t => msg.includes(t)).length;
          score = matches / tokens.length;
        }
        break;
      case 'context_selector':
        if (failure.context?.selector === pattern.selector) score = 0.95;
        break;
    }

    return Math.min(score * pattern.confidence, 1);
  }

  /**
   * Get statistics
   * @returns {Object} Statistics
   */
  getStatistics() {
    const byType = {};
    let totalOccurrences = 0;

    for (const pattern of this.patterns) {
      if (!byType[pattern.type]) {
        byType[pattern.type] = 0;
      }
      byType[pattern.type]++;
      totalOccurrences += pattern.occurrences || 1;
    }

    return {
      totalPatterns: this.patterns.length,
      totalOccurrences,
      byType,
      avgConfidence: (this.patterns.reduce((sum, p) => sum + p.confidence, 0) / this.patterns.length || 0).toFixed(2)
    };
  }
}

module.exports = PatternMatcher;
