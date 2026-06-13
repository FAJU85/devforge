/**
 * Pattern Suggester
 * Analyzes test failures and suggests fixes based on learned patterns
 * Used by reporters and CLI to provide actionable recommendations
 */

const PatternMatcher = require('./pattern_matcher');

class PatternSuggester {
  constructor() {
    this.matcher = new PatternMatcher();
    this.loadPatterns();
  }

  loadPatterns() {
    this.patterns = this.matcher.patterns || [];
  }

  /**
   * Analyze a failure and get suggestions
   * @param {Object} failure - The failure object with testName, errorMessage, stackTrace, etc.
   * @returns {Array} Array of suggestions with scores
   */
  analyze(failure) {
    if (!failure || !failure.errorMessage) {
      return [];
    }

    const matches = [];
    const text = `${failure.errorMessage} ${failure.stackTrace || ''}`.toLowerCase();

    // Score each pattern against this failure
    for (const pattern of this.patterns) {
      const score = this.scorePattern(pattern, failure, text);
      if (score > 0) {
        matches.push({
          pattern: pattern.pattern,
          type: pattern.type,
          score: score,
          confidence: pattern.confidence,
          occurrences: pattern.occurrences,
          severity: pattern.severity,
          suggestion: this.generateSuggestion(pattern, failure),
        });
      }
    }

    // Sort by score descending
    matches.sort((a, b) => b.score - a.score);

    return matches;
  }

  /**
   * Score how well a pattern matches a failure
   * @private
   */
  scorePattern(pattern, failure, text) {
    let score = 0;

    // Check if pattern text matches error message
    const patternLower = String(pattern.pattern).toLowerCase();

    // Exact substring match (highest score)
    if (text.includes(patternLower)) {
      score += 0.8 * pattern.confidence;
    }

    // Partial word match (medium score)
    if (this.hasWordMatch(text, patternLower)) {
      score += 0.4 * pattern.confidence;
    }

    // Category match (low score but useful for context)
    if (pattern.type === 'category' && failure.category === pattern.pattern) {
      score += 0.3 * pattern.confidence;
    }

    // Boost by occurrence frequency (popular patterns are more likely)
    if (pattern.occurrences && pattern.occurrences > 1) {
      score += Math.min(0.1, pattern.occurrences * 0.01);
    }

    return Math.min(1.0, score);
  }

  /**
   * Check if any significant words in the pattern appear in the text
   * @private
   */
  hasWordMatch(text, pattern) {
    const words = pattern
      .split(/[\s\-_:]+/)
      .filter(w => w.length > 3); // Only significant words

    return words.some(word => {
      const regex = new RegExp(`\\b${word}\\b`);
      return regex.test(text);
    });
  }

  /**
   * Generate a human-readable suggestion from a pattern
   * @private
   */
  generateSuggestion(pattern, failure) {
    const base = {
      problem: '',
      solution: '',
      references: '',
    };

    // Generate suggestions based on pattern type and content
    const patternText = String(pattern.pattern).toLowerCase();

    if (patternText.includes('timeout')) {
      base.problem = 'Test appears to be timing out';
      base.solution = [
        'Increase timeout: `test.setTimeout(10000)` or `test.slow()`',
        'Check for race conditions or infinite loops',
        'Verify async operations complete properly',
        'Add explicit wait conditions instead of just delays',
      ];
    } else if (patternText.includes('expected') && patternText.includes('received')) {
      base.problem = 'Assertion mismatch between expected and received values';
      base.solution = [
        'Check the assertion logic',
        'Verify test data setup is correct',
        'Log the actual vs expected values during debugging',
        'Consider using deep equality checks for objects',
      ];
    } else if (patternText.includes('not found') || patternText.includes('404')) {
      base.problem = 'Element or resource not found';
      base.solution = [
        'Verify selectors are correct',
        'Check if element is actually rendered in the DOM',
        'Wait for element to appear: `await page.waitForSelector(...)`',
        'Check network tab for failed API calls',
      ];
    } else if (patternText.includes('pointer-event') || patternText.includes('click')) {
      base.problem = 'Click or interaction event not working';
      base.solution = [
        'Check if element is visible and not overlapped',
        'Verify pointer-events CSS is not blocking interaction',
        'Use `force: true` if element is temporarily hidden',
        'Scroll to element before clicking',
      ];
    } else if (patternText.includes('stale')) {
      base.problem = 'Element reference became stale';
      base.solution = [
        'Re-query elements after DOM changes',
        'Avoid storing element references across navigation',
        'Re-fetch element handle before interacting',
      ];
    } else if (pattern.type === 'stack_trace') {
      base.problem = 'Error detected in stack trace';
      base.solution = [
        'Review the file and line number in the error',
        'Check for null/undefined references',
        'Verify function parameters are correct',
        'Look for async/await timing issues',
      ];
    } else if (pattern.severity === 'critical') {
      base.problem = 'Critical error detected (seen in previous failures)';
      base.solution = [
        `This pattern appears in ${pattern.occurrences || 1} test failure(s)`,
        'Review related test failures for common cause',
        'Check recent code changes that might have introduced regression',
      ];
    } else {
      base.problem = 'Common test failure pattern detected';
      base.solution = [
        `Seen in ${pattern.occurrences || 1} previous failure(s)`,
        'Review test logs for details',
        'Consider enabling verbose logging for this test',
      ];
    }

    return base;
  }

  /**
   * Get top suggestions for a failure
   * @param {Object} failure
   * @param {number} topN - Number of suggestions to return
   * @returns {Array} Top N suggestions
   */
  getTopSuggestions(failure, topN = 3) {
    const suggestions = this.analyze(failure);
    return suggestions.slice(0, topN);
  }

  /**
   * Format suggestions for CLI output
   */
  formatForCLI(suggestions) {
    if (suggestions.length === 0) {
      return '  No matching patterns found. Run more tests to build pattern database.';
    }

    let output = '';
    suggestions.forEach((s, idx) => {
      const confPercent = Math.round(s.confidence * 100);
      const scorePercent = Math.round(s.score * 100);

      output += `\n  ${idx + 1}. Pattern Match (${scorePercent}% relevance, ${confPercent}% confidence)\n`;
      output += `     Type: ${s.type}\n`;
      output += `     Pattern: ${s.pattern.substring(0, 60)}\n`;
      output += `     Seen: ${s.occurrences}x in test runs\n`;

      if (s.suggestion && s.suggestion.problem) {
        output += `\n     Problem: ${s.suggestion.problem}\n`;
      }

      if (s.suggestion && s.suggestion.solution) {
        output += `     Solutions:\n`;
        const solutions = Array.isArray(s.suggestion.solution)
          ? s.suggestion.solution
          : [s.suggestion.solution];
        solutions.forEach(sol => {
          output += `       • ${sol}\n`;
        });
      }
    });

    return output;
  }

  /**
   * Generate a summary report
   */
  generateReport() {
    const totalPatterns = this.patterns.length;
    const highConfidence = this.patterns.filter(p => p.confidence >= 0.8).length;
    const criticalPatterns = this.patterns.filter(p => p.severity === 'critical').length;

    return {
      totalPatterns,
      highConfidencePatterns: highConfidence,
      criticalPatterns,
      averageConfidence: totalPatterns > 0
        ? (this.patterns.reduce((sum, p) => sum + (p.confidence || 0), 0) / totalPatterns * 100).toFixed(0)
        : 0,
      mostCommon: this.patterns
        .sort((a, b) => (b.occurrences || 0) - (a.occurrences || 0))
        .slice(0, 5)
        .map(p => ({
          pattern: p.pattern.substring(0, 50),
          occurrences: p.occurrences,
          severity: p.severity,
        })),
    };
  }
}

module.exports = PatternSuggester;
