/**
 * Self-Healing Locators for Playwright
 * Intelligently recovers from broken selectors using multiple strategies
 */

import { Page, Locator, expect } from '@playwright/test';

export interface LocatorStrategy {
  primary: string;
  fallbacks: string[];
  description: string;
}

/**
 * Smart locator that tries multiple selection strategies
 */
export class SelfHealingLocator {
  private page: Page;
  private strategies: LocatorStrategy[];
  private lastSuccessfulLocator?: string;

  constructor(page: Page, strategies: LocatorStrategy[]) {
    this.page = page;
    this.strategies = strategies;
  }

  /**
   * Find element using primary locator, fallback to alternatives
   */
  async find(): Promise<Locator | null> {
    // Try last successful locator first (cache)
    if (this.lastSuccessfulLocator) {
      const cached = this.page.locator(this.lastSuccessfulLocator);
      if (await cached.isVisible().catch(() => false)) {
        return cached;
      }
    }

    // Try all strategies in order
    for (const strategy of this.strategies) {
      const primary = this.page.locator(strategy.primary);

      // Try primary selector
      if (await primary.isVisible().catch(() => false)) {
        this.lastSuccessfulLocator = strategy.primary;
        return primary;
      }

      // Try fallback selectors
      for (const fallback of strategy.fallbacks) {
        const fallbackLocator = this.page.locator(fallback);
        if (await fallbackLocator.isVisible().catch(() => false)) {
          this.lastSuccessfulLocator = fallback;
          console.warn(
            `Self-healing: Using fallback for ${strategy.description}: ${fallback}`
          );
          return fallbackLocator;
        }
      }
    }

    console.error(
      `Self-healing failed for: ${this.strategies.map((s) => s.description).join(', ')}`
    );
    return null;
  }

  /**
   * Click element with self-healing
   */
  async click(options?: { timeout?: number }): Promise<void> {
    const locator = await this.find();
    if (!locator) {
      throw new Error('Element not found with any locator strategy');
    }
    await locator.click(options);
  }

  /**
   * Fill text with self-healing
   */
  async fill(text: string, options?: { timeout?: number }): Promise<void> {
    const locator = await this.find();
    if (!locator) {
      throw new Error('Element not found with any locator strategy');
    }
    await locator.fill(text, options);
  }

  /**
   * Get text with self-healing
   */
  async getText(): Promise<string> {
    const locator = await this.find();
    if (!locator) {
      throw new Error('Element not found with any locator strategy');
    }
    return locator.textContent();
  }

  /**
   * Assert visibility with self-healing
   */
  async assertVisible(): Promise<void> {
    const locator = await this.find();
    if (!locator) {
      throw new Error('Element not found with any locator strategy');
    }
    await expect(locator).toBeVisible();
  }
}

/**
 * Pre-built locator strategies for common UI elements
 */
export const CommonLocators = {
  submitButton: (page: Page): SelfHealingLocator =>
    new SelfHealingLocator(page, [
      {
        primary: 'button[type="submit"]',
        fallbacks: [
          'button:has-text("Submit")',
          'button:has-text("Send")',
          'button[aria-label*="submit"]',
          '.submit-btn',
        ],
        description: 'Submit button',
      },
    ]),

  cancelButton: (page: Page): SelfHealingLocator =>
    new SelfHealingLocator(page, [
      {
        primary: 'button:has-text("Cancel")',
        fallbacks: [
          'button[aria-label*="cancel"]',
          '.cancel-btn',
          'button:has-text("Close")',
        ],
        description: 'Cancel button',
      },
    ]),

  input: (page: Page, label?: string): SelfHealingLocator =>
    new SelfHealingLocator(page, [
      ...(label
        ? [
            {
              primary: `input[aria-label="${label}"]`,
              fallbacks: [
                `label:has-text("${label}") ~ input`,
                `input[placeholder="${label}"]`,
              ],
              description: `Input for ${label}`,
            },
          ]
        : []),
      {
        primary: 'input[type="text"]',
        fallbacks: [
          'textarea',
          'input[type="email"]',
          'input[type="password"]',
        ],
        description: 'Text input',
      },
    ]),

  dialog: (page: Page): SelfHealingLocator =>
    new SelfHealingLocator(page, [
      {
        primary: '[role="dialog"]',
        fallbacks: [
          '.dialog',
          '.modal',
          '[class*="dialog"]',
          '[class*="modal"]',
        ],
        description: 'Dialog',
      },
    ]),

  toast: (page: Page): SelfHealingLocator =>
    new SelfHealingLocator(page, [
      {
        primary: '[role="alert"]',
        fallbacks: [
          '.toast',
          '.notification',
          '[class*="toast"]',
          '[class*="notification"]',
        ],
        description: 'Toast/Notification',
      },
    ]),

  sidebar: (page: Page): SelfHealingLocator =>
    new SelfHealingLocator(page, [
      {
        primary: '[role="navigation"]',
        fallbacks: [
          'aside',
          '.sidebar',
          '[class*="sidebar"]',
          '[class*="nav"]',
        ],
        description: 'Sidebar',
      },
    ]),
};

/**
 * Helper to create custom self-healing locator
 */
export function createSelfHealingLocator(
  page: Page,
  primary: string,
  fallbacks: string[],
  description: string
): SelfHealingLocator {
  return new SelfHealingLocator(page, [
    {
      primary,
      fallbacks,
      description,
    },
  ]);
}

/**
 * Wait for element with self-healing (useful for dynamic content)
 */
export async function waitForElementWithHealing(
  page: Page,
  strategies: LocatorStrategy[],
  timeout: number = 5000
): Promise<Locator | null> {
  const healer = new SelfHealingLocator(page, strategies);

  const startTime = Date.now();
  while (Date.now() - startTime < timeout) {
    const locator = await healer.find();
    if (locator) {
      return locator;
    }
    await page.waitForTimeout(100);
  }

  return null;
}

export default {
  SelfHealingLocator,
  CommonLocators,
  createSelfHealingLocator,
  waitForElementWithHealing,
};
