/**
 * Pattern Learner - Extracts patterns from collected test failures
 * Analyzes failures to identify recurring patterns and root causes
 */

const crypto = require('crypto');

class PatternLearner {
  constructor(options = {}) {
    this.options = {
      minOccurrences: options.minOccurrences || 2,
      minConfidence: options.minConfidence || 0.6,
      ...options
    };

    this.patterns = [];
  }

  /**
   * Learn patterns from a collection of failures
   * @param {Array} failures - Array of failure records
   * @returns {Array} Extracted patterns
   */
  learn(failures) {
    if (!failures || failures.length === 0) {
      return [];
    }

    // Extract patterns from different angles
    const patterns = [
      ...this.extractMessagePatterns(failures),
      ...this.extractStackTracePatterns(failures),
      ...this.extractContextPatterns(failures),
      ...this.extractCategoryPatterns(failures)
    ];

    // Deduplicate and merge similar patterns
    const mergedPatterns = this.mergePatterns(patterns);

    // Filter by confidence threshold
    this.patterns = mergedPatterns.filter(
      p => p.confidence >= this.options.minConfidence && p.occurrences >= this.options.minOccurrences
    );

    return this.patterns;
  }

  /**
   * Extract patterns from error messages
   * @param {Array} failures - Failure records
   * @returns {Array} Message patterns
   */
  extractMessagePatterns(failures) {
    const patterns = {};

    for (const failure of failures) {
      const tokens = this.tokenizeMessage(failure.errorMessage);
      const patterns_found = this.findPatterns(tokens);

      for (const pattern of patterns_found) {
        const key = pattern;
        if (!patterns[key]) {
          patterns[key] = {
            type: 'message',
            pattern: key,
            failures: [],
            confidence: 0,
            occurrences: 0,
            severity: 'medium'
          };
        }
        patterns[key].failures.push(failure.id);
        patterns[key].occurrences++;
      }
    }

    return Object.values(patterns);
  }

  /**
   * Extract patterns from stack traces
   * @param {Array} failures - Failure records
   * @returns {Array} Stack trace patterns
   */
  extractStackTracePatterns(failures) {
    const patterns = {};

    for (const failure of failures) {
      if (!failure.stackTrace) continue;

      const lines = failure.stackTrace.split('\n');

      // Extract function names and file locations
      for (const line of lines) {
        const match = line.match(/at\s+(\w+)\s+\((.+?):\d+:\d+\)/);
        if (match) {
          const [, funcName, filePath] = match;
          const key = `${funcName}:${filePath.split('/').pop()}`;

          if (!patterns[key]) {
            patterns[key] = {
              type: 'stack_trace',
              pattern: key,
              function: funcName,
              file: filePath,
              failures: [],
              confidence: 0,
              occurrences: 0,
              severity: 'high'
            };
          }
          patterns[key].failures.push(failure.id);
          patterns[key].occurrences++;
        }
      }
    }

    return Object.values(patterns);
  }

  /**
   * Extract patterns from context information
   * @param {Array} failures - Failure records
   * @returns {Array} Context patterns
   */
  extractContextPatterns(failures) {
    const patterns = {};

    for (const failure of failures) {
      const context = failure.context || {};

      // Browser-related patterns
      if (context.browser) {
        const key = `browser:${context.browser}`;
        if (!patterns[key]) {
          patterns[key] = {
            type: 'context_browser',
            pattern: key,
            browser: context.browser,
            failures: [],
            confidence: 0,
            occurrences: 0,
            severity: 'low'
          };
        }
        patterns[key].failures.push(failure.id);
        patterns[key].occurrences++;
      }

      // Timeout-related patterns
      if (context.timeout) {
        const key = `timeout:${context.timeout}`;
        if (!patterns[key]) {
          patterns[key] = {
            type: 'context_timeout',
            pattern: key,
            timeout: context.timeout,
            failures: [],
            confidence: 0,
            occurrences: 0,
            severity: 'medium'
          };
        }
        patterns[key].failures.push(failure.id);
        patterns[key].occurrences++;
      }

      // Selector-related patterns
      if (context.selector) {
        const key = `selector:${context.selector}`;
        if (!patterns[key]) {
          patterns[key] = {
            type: 'context_selector',
            pattern: key,
            selector: context.selector,
            failures: [],
            confidence: 0,
            occurrences: 0,
            severity: 'medium'
          };
        }
        patterns[key].failures.push(failure.id);
        patterns[key].occurrences++;
      }
    }

    return Object.values(patterns);
  }

  /**
   * Extract patterns from error categories
   * @param {Array} failures - Failure records
   * @returns {Array} Category patterns
   */
  extractCategoryPatterns(failures) {
    const patterns = {};

    for (const failure of failures) {
      const key = `category:${failure.category}`;

      if (!patterns[key]) {
        patterns[key] = {
          type: 'category',
          pattern: key,
          category: failure.category,
          failures: [],
          confidence: 0,
          occurrences: 0,
          severity: failure.severity
        };
      }
      patterns[key].failures.push(failure.id);
      patterns[key].occurrences++;
    }

    return Object.values(patterns);
  }

  /**
   * Tokenize error message into meaningful tokens
   * @param {string} message - Error message
   * @returns {Array} Tokens
   */
  tokenizeMessage(message) {
    // Split by common delimiters and clean up
    return message
      .toLowerCase()
      .split(/[\s\n\t,.:;'"()\[\]{}]/g)
      .filter(token => token.length > 2 && !this.isCommonWord(token));
  }

  /**
   * Find significant patterns in token list
   * @param {Array} tokens - Tokens
   * @returns {Array} Patterns
   */
  findPatterns(tokens) {
    const patterns = [];

    // Single token patterns
    for (const token of tokens) {
      patterns.push(token);
    }

    // Two-token patterns (bigrams)
    for (let i = 0; i < tokens.length - 1; i++) {
      patterns.push(`${tokens[i]}:${tokens[i + 1]}`);
    }

    return patterns;
  }

  /**
   * Check if word is too common to be meaningful
   * @param {string} word - Word to check
   * @returns {boolean} True if common word
   */
  isCommonWord(word) {
    const commonWords = [
      'the', 'and', 'or', 'is', 'it', 'in', 'to', 'of', 'a', 'an',
      'error', 'failed', 'test', 'expected', 'actual', 'undefined', 'null'
    ];
    return commonWords.includes(word);
  }

  /**
   * Merge similar patterns
   * @param {Array} patterns - Array of patterns
   * @returns {Array} Merged patterns
   */
  mergePatterns(patterns) {
    const merged = {};

    for (const pattern of patterns) {
      const key = `${pattern.type}:${pattern.pattern}`;

      if (!merged[key]) {
        merged[key] = {
          ...pattern,
          id: this.generatePatternId(pattern),
          confidence: 0
        };
      } else {
        // Merge failure lists
        merged[key].failures = [
          ...new Set([...merged[key].failures, ...pattern.failures])
        ];
        merged[key].occurrences = merged[key].failures.length;
      }

      // Calculate confidence based on occurrences
      merged[key].confidence = Math.min(1, merged[key].occurrences * 0.2);
    }

    return Object.values(merged);
  }

  /**
   * Match a new failure against learned patterns
   * @param {Object} failure - Failure to match
   * @returns {Array} Matching patterns with scores
   */
  matchFailure(failure) {
    const matches = [];

    for (const pattern of this.patterns) {
      const score = this.calculateMatchScore(failure, pattern);
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

    // Sort by score descending
    return matches.sort((a, b) => b.score - a.score);
  }

  /**
   * Calculate similarity score between failure and pattern
   * @param {Object} failure - Failure record
   * @param {Object} pattern - Pattern
   * @returns {number} Score 0-1
   */
  calculateMatchScore(failure, pattern) {
    let score = 0;
    let factors = 0;

    switch (pattern.type) {
      case 'message': {
        const messageTokens = this.tokenizeMessage(failure.errorMessage);
        const patternTokens = pattern.pattern.split(':');
        const matches = patternTokens.filter(t => messageTokens.includes(t)).length;
        score = matches / patternTokens.length;
        factors = 1;
        break;
      }

      case 'stack_trace': {
        if (failure.stackTrace.includes(pattern.function)) {
          score = 0.8;
        }
        factors = 1;
        break;
      }

      case 'category': {
        if (failure.category === pattern.category) {
          score = 1;
        }
        factors = 1;
        break;
      }

      case 'context_browser': {
        if (failure.context?.browser === pattern.browser) {
          score = 0.9;
        }
        factors = 1;
        break;
      }

      case 'context_selector': {
        if (failure.context?.selector === pattern.selector) {
          score = 0.95;
        }
        factors = 1;
        break;
      }

      default:
        factors = 1;
    }

    return score;
  }

  /**
   * Generate unique pattern ID
   * @param {Object} pattern - Pattern
   * @returns {string} Unique ID
   */
  generatePatternId(pattern) {
    const str = `${pattern.type}:${pattern.pattern}`;
    return `pattern_${crypto.createHash('md5').update(str).digest('hex').substring(0, 8)}`;
  }

  /**
   * Get patterns sorted by frequency
   * @returns {Array} Sorted patterns
   */
  getPatternsByFrequency() {
    return [...this.patterns].sort((a, b) => b.occurrences - a.occurrences);
  }

  /**
   * Get patterns sorted by confidence
   * @returns {Array} Sorted patterns
   */
  getPatternsByConfidence() {
    return [...this.patterns].sort((a, b) => b.confidence - a.confidence);
  }

  /**
   * Get patterns by type
   * @param {string} type - Pattern type
   * @returns {Array} Filtered patterns
   */
  getPatternsByType(type) {
    return this.patterns.filter(p => p.type === type);
  }

  /**
   * Get top N patterns
   * @param {number} n - Number of patterns
   * @returns {Array} Top patterns
   */
  getTopPatterns(n = 10) {
    return this.getPatternsByFrequency().slice(0, n);
  }

  /**
   * Get pattern statistics
   * @returns {Object} Statistics
   */
  getStatistics() {
    const typeStats = {};

    for (const pattern of this.patterns) {
      if (!typeStats[pattern.type]) {
        typeStats[pattern.type] = { count: 0, avgConfidence: 0 };
      }
      typeStats[pattern.type].count++;
      typeStats[pattern.type].avgConfidence += pattern.confidence;
    }

    // Calculate averages
    for (const type in typeStats) {
      typeStats[type].avgConfidence =
        (typeStats[type].avgConfidence / typeStats[type].count).toFixed(2);
    }

    return {
      totalPatterns: this.patterns.length,
      byType: typeStats,
      topPatterns: this.getTopPatterns(5).map(p => ({
        id: p.id,
        pattern: p.pattern,
        occurrences: p.occurrences,
        confidence: p.confidence
      }))
    };
  }
}

module.exports = PatternLearner;
