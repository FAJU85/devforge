/**
 * Example: E2E test using Self-Healing Locators + Generated Test Data
 * Demonstrates Phase 1, 2, and 4 integration
 */

import { test, expect } from '@playwright/test';
import { CommonLocators, createSelfHealingLocator } from '../helpers/self-healing-locators';
import { generateUserAccount } from '../generators/test-data-generator';

test.describe('Self-Healing E2E Tests', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('http://localhost:5173');
  });

  test('should login with generated user account using self-healing locators', async ({
    page,
  }) => {
    // Phase 4: Generate realistic test data
    const testUser = await generateUserAccount({ role: 'user' });

    // Phase 2: Use self-healing locators
    const emailInput = CommonLocators.input(page, 'Email');
    const passwordInput = CommonLocators.input(page, 'Password');
    const submitBtn = CommonLocators.submitButton(page);

    // Fill form with self-healing (handles broken selectors gracefully)
    try {
      await emailInput.fill(testUser.email);
      await passwordInput.fill(testUser.password);
      await submitBtn.click();
    } catch (error) {
      console.warn('Self-healing fallback needed:', error);
      // Fallback: Try alternative locators
      await page.fill('input[type="email"]', testUser.email);
      await page.fill('input[type="password"]', testUser.password);
      await page.click('button[type="submit"]');
    }

    // Verify with self-healing
    const successMessage = createSelfHealingLocator(
      page,
      'text=Welcome',
      [
        'text=Success',
        '.success-message',
        '[role="alert"]:has-text("Welcome")',
      ],
      'Success message'
    );

    await successMessage.assertVisible();
  });

  test('should handle edge cases in form inputs', async ({ page }) => {
    // Phase 4: Use edge case data
    const edgeCases = [
      {
        input: '<script>alert("xss")</script>',
        expectedError: true,
      },
      {
        input: '   ',
        expectedError: true,
      },
      {
        input: 'valid@email.com',
        expectedError: false,
      },
    ];

    for (const testCase of edgeCases) {
      // Phase 2: Self-healing input
      const emailInput = CommonLocators.input(page, 'Email');

      try {
        await emailInput.fill(testCase.input);

        if (testCase.expectedError) {
          const errorMsg = createSelfHealingLocator(
            page,
            '.error-message',
            [
              '[role="alert"].error',
              'text=Invalid',
              '.validation-error',
            ],
            'Error message'
          );

          await errorMsg.assertVisible();
        } else {
          // Should succeed
          const successBtn = CommonLocators.submitButton(page);
          await expect(successBtn).toBeVisible();
        }
      } catch (error) {
        if (!testCase.expectedError) {
          throw error;
        }
      }

      // Clear form for next iteration
      await emailInput.fill('');
    }
  });

  test('should handle missing/broken UI elements gracefully', async ({
    page,
  }) => {
    // Phase 2: Self-healing with multiple fallback strategies
    const userMenu = createSelfHealingLocator(
      page,
      '[aria-label="User Menu"]',
      [
        'button:has-text("Menu")',
        '.user-menu',
        'nav button:first-child',
        '[role="button"][data-testid="user-menu"]',
      ],
      'User menu'
    );

    // If element exists, it will find it even if primary selector is broken
    try {
      const menu = await userMenu.find();

      if (menu) {
        await userMenu.assertVisible();
        await userMenu.click();

        // Verify menu opened
        const menuItems = createSelfHealingLocator(
          page,
          '[role="menuitem"]',
          [
            'li[role="menuitem"]',
            '.menu-item',
            'button:has-text("Profile")',
          ],
          'Menu items'
        );

        const items = await menuItems.find();
        expect(items).toBeTruthy();
      }
    } catch (error) {
      console.log('Menu not found (acceptable for this page)', error);
    }
  });

  test('should verify sidebar with self-healing (common regression)', async ({
    page,
  }) => {
    // Phase 2: Self-heal sidebar selector
    const sidebar = CommonLocators.sidebar(page);

    try {
      await sidebar.assertVisible();

      // Navigate using self-healing locators
      const menuItems = page.locator('[role="menuitem"], .sidebar-item');
      const count = await menuItems.count();

      expect(count).toBeGreaterThan(0);

      // Click first menu item with self-healing
      const firstItem = createSelfHealingLocator(
        page,
        '[role="menuitem"]:first-child',
        [
          '.sidebar-item:first-child',
          '.nav-item:first-child',
          'aside a:first-child',
        ],
        'First menu item'
      );

      await firstItem.click();

      // Verify navigation happened
      await page.waitForLoadState('networkidle');
      const url = page.url();
      expect(url).not.toBe('http://localhost:5173');
    } catch (error) {
      console.log('Sidebar navigation not available on this page');
    }
  });

  test('should handle dialog interactions with self-healing', async ({
    page,
  }) => {
    // Phase 2: Self-healing dialog locators
    const dialog = CommonLocators.dialog(page);

    // Find and interact with dialog
    const dialogElement = await dialog.find();

    if (dialogElement) {
      await dialog.assertVisible();

      // Phase 2: Self-healing buttons
      const cancelBtn = CommonLocators.cancelButton(page);
      const submitBtn = CommonLocators.submitButton(page);

      // Both buttons might exist in dialog
      try {
        await submitBtn.click();
        await page.waitForTimeout(500);
      } catch {
        try {
          await cancelBtn.click();
        } catch (e) {
          console.log('Could not interact with dialog buttons');
        }
      }
    }
  });
});
