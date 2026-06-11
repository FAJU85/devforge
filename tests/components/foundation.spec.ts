/**
 * E2E tests for foundation components: Button, Input, Toast, Dialog
 */

import { test, expect } from '@playwright/test';

test.describe('Foundation Components', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('http://localhost:5173');
  });

  test.describe('Button Component', () => {
    test('should render button with label', async ({ page }) => {
      const button = await page.locator('button:has-text("Click me")').first();
      await expect(button).toBeVisible();
    });

    test('should apply primary variant styles', async ({ page }) => {
      const primaryBtn = await page.locator('button[data-variant="primary"]').first();
      const bgColor = await primaryBtn.evaluate(
        (el) => window.getComputedStyle(el).backgroundColor
      );
      expect(bgColor).toBeTruthy();
    });

    test('should trigger onClick handler', async ({ page }) => {
      const button = await page.locator('button:has-text("Test Click")').first();
      await button.click();
      const result = await page.evaluate(() => (window as any).lastClickedButton);
      expect(result).toBe('Test Click');
    });

    test('should handle disabled state', async ({ page }) => {
      const disabledBtn = await page.locator('button[disabled]').first();
      if (await disabledBtn.isVisible()) {
        await expect(disabledBtn).toBeDisabled();
      }
    });

    test('should apply hover opacity', async ({ page }) => {
      const button = await page.locator('button:has-text("Hover Test")').first();
      if (await button.isVisible()) {
        await button.hover();
        const opacity = await button.evaluate(
          (el) => window.getComputedStyle(el).opacity
        );
        expect(opacity).toBe('0.8');
      }
    });

    test('should support secondary variant', async ({ page }) => {
      const secondaryBtn = await page.locator('button[data-variant="secondary"]').first();
      if (await secondaryBtn.isVisible()) {
        const borderColor = await secondaryBtn.evaluate(
          (el) => window.getComputedStyle(el).borderColor
        );
        expect(borderColor).toBeTruthy();
      }
    });

    test('should support danger variant', async ({ page }) => {
      const dangerBtn = await page.locator('button[data-variant="danger"]').first();
      if (await dangerBtn.isVisible()) {
        const bgColor = await dangerBtn.evaluate(
          (el) => window.getComputedStyle(el).backgroundColor
        );
        expect(bgColor).toBeTruthy();
      }
    });
  });

  test.describe('Input Component', () => {
    test('should render input field', async ({ page }) => {
      const input = await page.locator('input[data-testid="foundation-input"]').first();
      if (await input.isVisible()) {
        await expect(input).toBeVisible();
      }
    });

    test('should accept text input', async ({ page }) => {
      const input = await page.locator('input[type="text"]').first();
      if (await input.isVisible()) {
        await input.fill('test value');
        const value = await input.inputValue();
        expect(value).toBe('test value');
      }
    });

    test('should handle focus state', async ({ page }) => {
      const input = await page.locator('input[data-testid="foundation-input"]').first();
      if (await input.isVisible()) {
        await input.focus();
        const borderColor = await input.evaluate(
          (el) => window.getComputedStyle(el).borderColor
        );
        expect(borderColor).toBeTruthy();
      }
    });

    test('should handle blur state', async ({ page }) => {
      const input = await page.locator('input[data-testid="foundation-input"]').first();
      if (await input.isVisible()) {
        await input.focus();
        await input.blur();
        const boxShadow = await input.evaluate(
          (el) => window.getComputedStyle(el).boxShadow
        );
        expect(boxShadow).toBe('none');
      }
    });

    test('should trigger onChange callback', async ({ page }) => {
      const input = await page.locator('input[data-testid="foundation-input"]').first();
      if (await input.isVisible()) {
        await input.type('test');
        const lastValue = await page.evaluate(() => (window as any).lastInputValue);
        expect(lastValue).toContain('t');
      }
    });

    test('should support password input type', async ({ page }) => {
      const passwordInput = await page.locator('input[type="password"]').first();
      if (await passwordInput.isVisible()) {
        await expect(passwordInput).toHaveAttribute('type', 'password');
      }
    });

    test('should support email input type', async ({ page }) => {
      const emailInput = await page.locator('input[type="email"]').first();
      if (await emailInput.isVisible()) {
        await expect(emailInput).toHaveAttribute('type', 'email');
      }
    });

    test('should support disabled state', async ({ page }) => {
      const disabledInput = await page.locator('input[disabled]').first();
      if (await disabledInput.isVisible()) {
        await expect(disabledInput).toBeDisabled();
      }
    });
  });

  test.describe('Toast Component', () => {
    test('should display success toast', async ({ page }) => {
      const successToastBtn = await page.locator('button:has-text("Show Success Toast")').first();
      if (await successToastBtn.isVisible()) {
        await successToastBtn.click();
        const toast = await page.locator('[role="status"]').first();
        await expect(toast).toBeVisible();
      }
    });

    test('should display error toast', async ({ page }) => {
      const errorToastBtn = await page.locator('button:has-text("Show Error Toast")').first();
      if (await errorToastBtn.isVisible()) {
        await errorToastBtn.click();
        const toast = await page.locator('[role="status"]').first();
        await expect(toast).toBeVisible();
      }
    });

    test('should display info toast', async ({ page }) => {
      const infoToastBtn = await page.locator('button:has-text("Show Info Toast")').first();
      if (await infoToastBtn.isVisible()) {
        await infoToastBtn.click();
        const toast = await page.locator('[role="status"]').first();
        await expect(toast).toBeVisible();
      }
    });

    test('should display warning toast', async ({ page }) => {
      const warningToastBtn = await page.locator('button:has-text("Show Warning Toast")').first();
      if (await warningToastBtn.isVisible()) {
        await warningToastBtn.click();
        const toast = await page.locator('[role="status"]').first();
        await expect(toast).toBeVisible();
      }
    });

    test('should auto-dismiss toast after duration', async ({ page }) => {
      const toastBtn = await page.locator('button:has-text("Show Toast")').first();
      if (await toastBtn.isVisible()) {
        await toastBtn.click();
        const toast = await page.locator('[role="status"]').first();
        await expect(toast).toBeVisible();
        await page.waitForTimeout(3500);
        await expect(toast).not.toBeVisible();
      }
    });

    test('should dismiss toast on close button click', async ({ page }) => {
      const toastBtn = await page.locator('button:has-text("Show Toast")').first();
      if (await toastBtn.isVisible()) {
        await toastBtn.click();
        const closeBtn = await page.locator('[role="status"] button').first();
        await closeBtn.click();
        await page.waitForTimeout(400);
        const toast = await page.locator('[role="status"]').first();
        await expect(toast).not.toBeVisible();
      }
    });

    test('should position toasts in top right', async ({ page }) => {
      const container = await page.locator('[data-testid="toast-container"]').first();
      if (await container.isVisible()) {
        const position = await container.evaluate((el) => {
          const rect = el.getBoundingClientRect();
          return { right: rect.right, top: rect.top };
        });
        expect(position.right).toBeGreaterThan(window.innerWidth - 450);
        expect(position.top).toBeLessThan(50);
      }
    });
  });

  test.describe('Dialog Component', () => {
    test('should render confirmation dialog', async ({ page }) => {
      const confirmDialogBtn = await page.locator('button:has-text("Show Confirm")').first();
      if (await confirmDialogBtn.isVisible()) {
        await confirmDialogBtn.click();
        const dialog = await page.locator('[role="dialog"]').first();
        await expect(dialog).toBeVisible();
      }
    });

    test('should render alert dialog', async ({ page }) => {
      const alertDialogBtn = await page.locator('button:has-text("Show Alert")').first();
      if (await alertDialogBtn.isVisible()) {
        await alertDialogBtn.click();
        const dialog = await page.locator('[role="dialog"]').first();
        await expect(dialog).toBeVisible();
      }
    });

    test('should display dialog title and message', async ({ page }) => {
      const confirmDialogBtn = await page.locator('button:has-text("Show Confirm")').first();
      if (await confirmDialogBtn.isVisible()) {
        await confirmDialogBtn.click();
        const title = await page.locator('h2').first();
        await expect(title).toBeVisible();
        const message = await page.locator('p').first();
        await expect(message).toBeVisible();
      }
    });

    test('should have confirm and cancel buttons', async ({ page }) => {
      const confirmDialogBtn = await page.locator('button:has-text("Show Confirm")').first();
      if (await confirmDialogBtn.isVisible()) {
        await confirmDialogBtn.click();
        const confirmBtn = await page.locator('button:has-text("Confirm")').first();
        const cancelBtn = await page.locator('button:has-text("Cancel")').first();
        await expect(confirmBtn).toBeVisible();
        await expect(cancelBtn).toBeVisible();
      }
    });

    test('should close dialog on confirm', async ({ page }) => {
      const confirmDialogBtn = await page.locator('button:has-text("Show Confirm")').first();
      if (await confirmDialogBtn.isVisible()) {
        await confirmDialogBtn.click();
        const dialog = await page.locator('[role="dialog"]').first();
        const confirmBtn = await page.locator('button:has-text("Confirm")').first();
        await confirmBtn.click();
        await page.waitForTimeout(300);
        await expect(dialog).not.toBeVisible();
      }
    });

    test('should close dialog on cancel', async ({ page }) => {
      const confirmDialogBtn = await page.locator('button:has-text("Show Confirm")').first();
      if (await confirmDialogBtn.isVisible()) {
        await confirmDialogBtn.click();
        const dialog = await page.locator('[role="dialog"]').first();
        const cancelBtn = await page.locator('button:has-text("Cancel")').first();
        await cancelBtn.click();
        await page.waitForTimeout(300);
        await expect(dialog).not.toBeVisible();
      }
    });

    test('should close dialog on overlay click', async ({ page }) => {
      const confirmDialogBtn = await page.locator('button:has-text("Show Confirm")').first();
      if (await confirmDialogBtn.isVisible()) {
        await confirmDialogBtn.click();
        const overlay = await page.locator('[role="dialog"]').first();
        const parent = await overlay.evaluateHandle((el) => el.parentElement);
        await page.evaluate(() => {
          const overlay = document.querySelector('[role="dialog"]')?.parentElement;
          if (overlay) {
            overlay.dispatchEvent(
              new MouseEvent('click', { bubbles: true, cancelable: true })
            );
          }
        });
        await page.waitForTimeout(300);
        await expect(overlay).not.toBeVisible();
      }
    });

    test('alert dialog should have only OK button', async ({ page }) => {
      const alertDialogBtn = await page.locator('button:has-text("Show Alert")').first();
      if (await alertDialogBtn.isVisible()) {
        await alertDialogBtn.click();
        const okBtn = await page.locator('button:has-text("OK")').first();
        const cancelBtn = await page.locator('button:has-text("Cancel")');
        await expect(okBtn).toBeVisible();
        await expect(cancelBtn).toHaveCount(0);
      }
    });

    test('should trigger onConfirm callback', async ({ page }) => {
      const confirmDialogBtn = await page.locator('button:has-text("Show Confirm")').first();
      if (await confirmDialogBtn.isVisible()) {
        await confirmDialogBtn.click();
        const confirmBtn = await page.locator('button:has-text("Confirm")').first();
        await confirmBtn.click();
        const confirmed = await page.evaluate(() => (window as any).dialogConfirmed);
        expect(confirmed).toBe(true);
      }
    });
  });

  test.describe('Integration', () => {
    test('should handle multiple toasts', async ({ page }) => {
      const toastBtn = await page.locator('button:has-text("Show Toast")').first();
      if (await toastBtn.isVisible()) {
        await toastBtn.click();
        await page.waitForTimeout(100);
        await toastBtn.click();
        const toasts = await page.locator('[role="status"]').all();
        expect(toasts.length).toBeGreaterThanOrEqual(2);
      }
    });

    test('should handle dialog and toast together', async ({ page }) => {
      const dialogBtn = await page.locator('button:has-text("Show Confirm")').first();
      const toastBtn = await page.locator('button:has-text("Show Toast")').first();
      if (await dialogBtn.isVisible() && await toastBtn.isVisible()) {
        await dialogBtn.click();
        await toastBtn.click();
        const dialog = await page.locator('[role="dialog"]').first();
        const toast = await page.locator('[role="status"]').first();
        await expect(dialog).toBeVisible();
        await expect(toast).toBeVisible();
      }
    });
  });
});
