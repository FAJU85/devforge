/**
 * Suggestion Generator - Generates fix suggestions based on learned patterns
 * Creates actionable recommendations to resolve failures
 */

class SuggestionGenerator {
  constructor(options = {}) {
    this.options = {
      minSuggestionConfidence: options.minSuggestionConfidence || 0.5,
      ...options
    };

    this.suggestions = [];
    this.feedbackLog = [];
  }

  /**
   * Generate suggestions for a failure
   * @param {Object} failure - Failure record
   * @param {Array} matchingPatterns - Array of matching patterns from PatternMatcher
   * @returns {Array} Generated suggestions
   */
  generateSuggestions(failure, matchingPatterns = []) {
    const suggestions = [];

    // Generate suggestions based on matching patterns
    for (const match of matchingPatterns) {
      const patternSuggestions = this.generatePatternSuggestions(failure, match);
      suggestions.push(...patternSuggestions);
    }

    // Generate category-specific suggestions
    const categorySuggestions = this.generateCategorySuggestions(failure);
    suggestions.push(...categorySuggestions);

    // Sort by confidence and rank
    const ranked = this.rankSuggestions(suggestions);

    return ranked;
  }

  /**
   * Generate suggestions based on matched pattern
   * @param {Object} failure - Failure record
   * @param {Object} match - Matched pattern
   * @returns {Array} Suggestions
   */
  generatePatternSuggestions(failure, match) {
    const suggestions = [];
    const baseConfidence = match.confidence * match.score;

    switch (match.type) {
      case 'message': {
        suggestions.push({
          type: 'similar_failure',
          title: 'Similar failure pattern detected',
          description: `This error message matches a previously occurring pattern: "${match.pattern}"`,
          action: 'Review previous failures and their fixes',
          confidence: baseConfidence,
          priority: 'medium',
          category: failure.category
        });
        break;
      }

      case 'stack_trace': {
        suggestions.push({
          type: 'function_risk',
          title: `Function "${match.pattern}" has failure history`,
          description: `The function ${match.pattern} appears in multiple failure stack traces`,
          action: 'Examine and refactor this function for robustness',
          confidence: baseConfidence,
          priority: 'high',
          category: failure.category
        });
        break;
      }

      case 'category': {
        suggestions.push(
          ...this.generateCategorySpecificSuggestions(failure.category, baseConfidence)
        );
        break;
      }

      case 'context_browser': {
        suggestions.push({
          type: 'browser_specific',
          title: `Browser-specific issue: ${match.context.browser}`,
          description: `This test has failed on ${match.context.browser} browser before`,
          action: `Test and debug specifically on ${match.context.browser}`,
          confidence: baseConfidence,
          priority: 'medium',
          browser: match.context.browser
        });
        break;
      }

      case 'context_selector': {
        suggestions.push({
          type: 'selector_issue',
          title: `Selector may be unstable: ${match.context.selector}`,
          description: `This selector has previously failed to locate elements`,
          action: `Use a more robust selector or add explicit waits`,
          confidence: baseConfidence,
          priority: 'high',
          selector: match.context.selector
        });
        break;
      }
    }

    return suggestions;
  }

  /**
   * Generate category-specific suggestions
   * @param {string} category - Error category
   * @param {number} confidence - Base confidence
   * @returns {Array} Suggestions
   */
  generateCategorySpecificSuggestions(category, confidence) {
    const suggestions = [];

    switch (category) {
      case 'assertion':
        suggestions.push({
          type: 'assertion_failure',
          title: 'Assertion failed',
          description: 'The test assertion did not pass',
          action: 'Review expected vs actual values. Verify test assumptions.',
          confidence,
          priority: 'high'
        });
        break;

      case 'timeout':
        suggestions.push({
          type: 'timeout_issue',
          title: 'Operation timed out',
          description: 'Wait time exceeded. Element might be slow to load or not appear.',
          action: 'Increase timeout, add explicit wait for element, or check page load performance',
          confidence,
          priority: 'high',
          code: `// Increase wait time
driver.implicitly_wait(15)

// Or use explicit wait
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

wait = WebDriverWait(driver, 15)
wait.until(EC.presence_of_element_located((By.ID, "element_id")))`
        });
        break;

      case 'element_not_found':
        suggestions.push({
          type: 'element_not_found',
          title: 'Element not found',
          description: 'The selector did not match any element on the page',
          action: 'Verify selector is correct, check DOM structure, add waits for dynamic content',
          confidence,
          priority: 'critical',
          code: `// Use explicit wait for element
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

element = WebDriverWait(driver, 10).until(
    EC.presence_of_element_located((By.ID, "element_id"))
)`
        });
        break;

      case 'stale_element':
        suggestions.push({
          type: 'stale_element',
          title: 'Element reference is stale',
          description: 'Element was found but became detached from DOM',
          action: 'Re-find element after DOM changes, or wait for stability',
          confidence,
          priority: 'high',
          code: `// Re-find element if DOM changed
from selenium.webdriver.support import expected_conditions as EC

# Instead of storing element reference, re-find it
button = WebDriverWait(driver, 10).until(
    EC.element_to_be_clickable((By.ID, "button_id"))
)
button.click()`
        });
        break;

      case 'element_obscured':
        suggestions.push({
          type: 'element_obscured',
          title: 'Element is obscured or not clickable',
          description: 'Element exists but is blocked or not interactive',
          action: 'Wait for element to be clickable, scroll to element, close overlays',
          confidence,
          priority: 'high',
          code: `# Wait for element to be clickable
from selenium.webdriver.support import expected_conditions as EC

element = WebDriverWait(driver, 10).until(
    EC.element_to_be_clickable((By.ID, "element_id"))
)
element.click()

# Or scroll element into view
driver.execute_script("arguments[0].scrollIntoView(true);", element)`
        });
        break;

      case 'network':
        suggestions.push({
          type: 'network_error',
          title: 'Network or connection error',
          description: 'Failed to communicate with server or load resources',
          action: 'Check network connectivity, API endpoints, server status',
          confidence,
          priority: 'high'
        });
        break;

      case 'code_error':
        suggestions.push({
          type: 'code_error',
          title: 'Code syntax or type error',
          description: 'Error in test code itself, not the application',
          action: 'Review test code for syntax errors, missing imports, or incorrect logic',
          confidence,
          priority: 'critical'
        });
        break;
    }

    return suggestions;
  }

  /**
   * Generate general category suggestions
   * @param {Object} failure - Failure record
   * @returns {Array} Suggestions
   */
  generateCategorySuggestions(failure) {
    return this.generateCategorySpecificSuggestions(failure.category, 0.7);
  }

  /**
   * Rank suggestions by priority and confidence
   * @param {Array} suggestions - Suggestions to rank
   * @returns {Array} Ranked suggestions
   */
  rankSuggestions(suggestions) {
    const priorityOrder = { critical: 0, high: 1, medium: 2, low: 3 };

    return suggestions
      .filter(s => s.confidence >= this.options.minSuggestionConfidence)
      .sort((a, b) => {
        // First by priority
        const priorityDiff = priorityOrder[a.priority] - priorityOrder[b.priority];
        if (priorityDiff !== 0) return priorityDiff;

        // Then by confidence
        return b.confidence - a.confidence;
      });
  }

  /**
   * Record feedback on a suggestion
   * @param {string} suggestionId - ID of suggestion
   * @param {string} feedback - 'helpful', 'not_helpful', 'fixed'
   * @returns {Object} Feedback record
   */
  recordFeedback(suggestionId, feedback) {
    const feedbackRecord = {
      id: this.generateId(),
      suggestionId,
      feedback,
      timestamp: new Date().toISOString()
    };

    this.feedbackLog.push(feedbackRecord);
    return feedbackRecord;
  }

  /**
   * Get suggestions for a test file
   * @param {string} filePath - Path to test file
   * @param {Array} matchingPatterns - Matching patterns
   * @returns {Array} Suggestions
   */
  getSuggestionsForFile(filePath, matchingPatterns = []) {
    const suggestions = [];

    // General test best practices
    suggestions.push({
      type: 'best_practice',
      title: 'Use explicit waits instead of implicit waits',
      description: 'Explicit waits are more reliable than implicit waits',
      action: 'Replace implicit waits with WebDriverWait and expected conditions',
      confidence: 0.8,
      priority: 'medium'
    });

    suggestions.push({
      type: 'best_practice',
      title: 'Add error handling and retry logic',
      description: 'Transient failures can be handled with retries',
      action: 'Implement retry decorators for flaky tests',
      confidence: 0.7,
      priority: 'low'
    });

    // Add specific pattern-based suggestions
    for (const pattern of matchingPatterns) {
      suggestions.push({
        type: 'code_issue',
        title: `Potential issue detected: ${pattern.pattern}`,
        description: `Pattern matches code in ${filePath}`,
        action: 'Review and test this code path',
        confidence: pattern.score,
        priority: 'medium'
      });
    }

    return this.rankSuggestions(suggestions);
  }

  /**
   * Generate summary of suggestions
   * @param {Array} suggestions - Array of suggestions
   * @returns {Object} Summary
   */
  getSuggestionSummary(suggestions) {
    const byType = {};
    const byPriority = { critical: [], high: [], medium: [], low: [] };
    let totalConfidence = 0;

    for (const suggestion of suggestions) {
      // Count by type
      byType[suggestion.type] = (byType[suggestion.type] || 0) + 1;

      // Group by priority
      if (byPriority[suggestion.priority]) {
        byPriority[suggestion.priority].push(suggestion);
      }

      totalConfidence += suggestion.confidence;
    }

    return {
      total: suggestions.length,
      byType,
      byPriority: {
        critical: byPriority.critical.length,
        high: byPriority.high.length,
        medium: byPriority.medium.length,
        low: byPriority.low.length
      },
      avgConfidence: suggestions.length > 0
        ? (totalConfidence / suggestions.length).toFixed(2)
        : 0,
      mostCommonType: Object.keys(byType).reduce((a, b) => byType[a] > byType[b] ? a : b, null)
    };
  }

  /**
   * Get feedback statistics
   * @returns {Object} Feedback statistics
   */
  getFeedbackStatistics() {
    const stats = {
      helpful: 0,
      not_helpful: 0,
      fixed: 0,
      total: this.feedbackLog.length
    };

    for (const feedback of this.feedbackLog) {
      if (feedback.feedback === 'helpful') stats.helpful++;
      else if (feedback.feedback === 'not_helpful') stats.not_helpful++;
      else if (feedback.feedback === 'fixed') stats.fixed++;
    }

    const helpful = stats.helpful + stats.fixed;
    const successRate = stats.total > 0
      ? ((helpful / stats.total) * 100).toFixed(2)
      : '0';

    return {
      ...stats,
      successRate: `${successRate}%`,
      feedbackLog: this.feedbackLog
    };
  }

  /**
   * Generate unique ID
   * @returns {string} Unique ID
   */
  generateId() {
    return `suggestion_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
  }
}

module.exports = SuggestionGenerator;
