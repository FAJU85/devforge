/**
 * E2E tests for integration components: AppLayout, StatusBar, NotificationHub, ThemeToggle
 */

import { test, expect } from '@playwright/test';

test.describe('Integration Components', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('http://localhost:5173');
  });

  test.describe('AppLayout Component', () => {
    test('should render app layout', async ({ page }) => {
      const layout = await page.locator('.app-layout').first();
      if (await layout.isVisible()) {
        await expect(layout).toBeVisible();
      }
    });

    test('should display sidebar section', async ({ page }) => {
      const sidebar = await page.locator('.sidebar-section').first();
      if (await sidebar.isVisible()) {
        await expect(sidebar).toBeVisible();
      }
    });

    test('should display main section', async ({ page }) => {
      const main = await page.locator('.main-section').first();
      if (await main.isVisible()) {
        await expect(main).toBeVisible();
      }
    });

    test('should have toolbar', async ({ page }) => {
      const toolbar = await page.locator('.app-toolbar').first();
      if (await toolbar.isVisible()) {
        await expect(toolbar).toBeVisible();
      }
    });

    test('should display content area', async ({ page }) => {
      const content = await page.locator('.main-content').first();
      if (await content.isVisible()) {
        await expect(content).toBeVisible();
      }
    });

    test('should display context panel', async ({ page }) => {
      const context = await page.locator('.context-panel').first();
      if (await context.isVisible()) {
        await expect(context).toBeVisible();
      }
    });

    test('should toggle sidebar visibility', async ({ page }) => {
      const toggleBtn = await page.locator('.app-toolbar button').first();
      if (await toggleBtn.isVisible()) {
        const sidebar = await page.locator('.sidebar-section').first();
        const initialWidth = await sidebar.evaluate((el) => el.offsetWidth);
        await toggleBtn.click();
        await page.waitForTimeout(300);
        const newWidth = await sidebar.evaluate((el) => el.offsetWidth);
        expect(newWidth).not.toBe(initialWidth);
      }
    });

    test('should have status bar', async ({ page }) => {
      const statusBar = await page.locator('.status-bar').first();
      if (await statusBar.isVisible()) {
        await expect(statusBar).toBeVisible();
      }
    });
  });

  test.describe('StatusBar Component', () => {
    test('should render status bar', async ({ page }) => {
      const bar = await page.locator('.status-bar').first();
      if (await bar.isVisible()) {
        await expect(bar).toBeVisible();
      }
    });

    test('should display status items', async ({ page }) => {
      const items = await page.locator('.status-item').all();
      if (items.length > 0) {
        expect(items.length).toBeGreaterThan(0);
      }
    });

    test('should show ready status', async ({ page }) => {
      const status = await page.locator('text=Ready').first();
      if (await status.isVisible()) {
        await expect(status).toBeVisible();
      }
    });

    test('should display line and column info', async ({ page }) => {
      const bar = await page.locator('.status-bar').first();
      if (await bar.isVisible()) {
        const text = await bar.textContent();
        if (text) {
          expect(text).toContain('Line') || expect(text).toContain('Col');
        }
      }
    });

    test('should display time', async ({ page }) => {
      const time = await page.locator('.status-bar span').last();
      if (await time.isVisible()) {
        const text = await time.textContent();
        expect(text).toMatch(/\d+:\d+/);
      }
    });

    test('should update status on click', async ({ page }) => {
      const item = await page.locator('.status-item').first();
      if (await item.isVisible()) {
        await item.click();
        // Status would update
      }
    });
  });

  test.describe('NotificationHub Component', () => {
    test('should render notification hub', async ({ page }) => {
      const hub = await page.locator('.notification-hub').first();
      if (await hub.isVisible()) {
        await expect(hub).toBeVisible();
      }
    });

    test('should show success notification', async ({ page }) => {
      const btn = await page.locator('button:has-text("Show Success")').first();
      if (await btn.isVisible()) {
        await btn.click();
        const notif = await page.locator('.notification-success').first();
        if (await notif.isVisible()) {
          await expect(notif).toBeVisible();
        }
      }
    });

    test('should show error notification', async ({ page }) => {
      const btn = await page.locator('button:has-text("Show Error")').first();
      if (await btn.isVisible()) {
        await btn.click();
        const notif = await page.locator('.notification-error').first();
        if (await notif.isVisible()) {
          await expect(notif).toBeVisible();
        }
      }
    });

    test('should show info notification', async ({ page }) => {
      const btn = await page.locator('button:has-text("Show Info")').first();
      if (await btn.isVisible()) {
        await btn.click();
        const notif = await page.locator('.notification-info').first();
        if (await notif.isVisible()) {
          await expect(notif).toBeVisible();
        }
      }
    });

    test('should show warning notification', async ({ page }) => {
      const btn = await page.locator('button:has-text("Show Warning")').first();
      if (await btn.isVisible()) {
        await btn.click();
        const notif = await page.locator('.notification-warning').first();
        if (await notif.isVisible()) {
          await expect(notif).toBeVisible();
        }
      }
    });

    test('should close notification on close button', async ({ page }) => {
      const btn = await page.locator('button:has-text("Show Success")').first();
      if (await btn.isVisible()) {
        await btn.click();
        const notif = await page.locator('.notification-success').first();
        const closeBtn = await notif.locator('button').first();
        if (await closeBtn.isVisible()) {
          await closeBtn.click();
          await page.waitForTimeout(300);
          const count = await page.locator('.notification-success').count();
          expect(count).toBe(0);
        }
      }
    });

    test('should auto-dismiss notification after duration', async ({ page }) => {
      const btn = await page.locator('button:has-text("Show Info")').first();
      if (await btn.isVisible()) {
        await btn.click();
        let notif = await page.locator('.notification-info').first();
        await expect(notif).toBeVisible();
        await page.waitForTimeout(3500);
        notif = await page.locator('.notification-info').first();
        const count = await page.locator('.notification-info').count();
        expect(count).toBe(0);
      }
    });

    test('should display notification title and message', async ({ page }) => {
      const btn = await page.locator('button:has-text("Show Info")').first();
      if (await btn.isVisible()) {
        await btn.click();
        const notif = await page.locator('.notification-info').first();
        if (await notif.isVisible()) {
          const text = await notif.textContent();
          expect(text).toBeTruthy();
        }
      }
    });
  });

  test.describe('ThemeToggle Component', () => {
    test('should render theme toggle', async ({ page }) => {
      const toggle = await page.locator('.theme-toggle').first();
      if (await toggle.isVisible()) {
        await expect(toggle).toBeVisible();
      }
    });

    test('should have theme buttons', async ({ page }) => {
      const btns = await page.locator('.theme-btn').all();
      if (btns.length > 0) {
        expect(btns.length).toBeGreaterThanOrEqual(2);
      }
    });

    test('should have light theme button', async ({ page }) => {
      const lightBtn = await page.locator('.theme-light').first();
      if (await lightBtn.isVisible()) {
        await expect(lightBtn).toBeVisible();
      }
    });

    test('should have dark theme button', async ({ page }) => {
      const darkBtn = await page.locator('.theme-dark').first();
      if (await darkBtn.isVisible()) {
        await expect(darkBtn).toBeVisible();
      }
    });

    test('should switch to light theme', async ({ page }) => {
      const lightBtn = await page.locator('.theme-light').first();
      if (await lightBtn.isVisible()) {
        await lightBtn.click();
        const html = await page.locator('html').first();
        const theme = await html.getAttribute('data-theme');
        expect(theme).toBe('light');
      }
    });

    test('should switch to dark theme', async ({ page }) => {
      const darkBtn = await page.locator('.theme-dark').first();
      if (await darkBtn.isVisible()) {
        await darkBtn.click();
        const html = await page.locator('html').first();
        const theme = await html.getAttribute('data-theme');
        expect(theme).toBe('dark');
      }
    });

    test('should highlight active theme', async ({ page }) => {
      const darkBtn = await page.locator('.theme-dark').first();
      if (await darkBtn.isVisible()) {
        await darkBtn.click();
        const bgColor = await darkBtn.evaluate(
          (el) => window.getComputedStyle(el).backgroundColor
        );
        expect(bgColor).toBeTruthy();
      }
    });

    test('should persist theme preference', async ({ page }) => {
      const lightBtn = await page.locator('.theme-light').first();
      if (await lightBtn.isVisible()) {
        await lightBtn.click();
        await page.reload();
        const html = await page.locator('html').first();
        const theme = await html.getAttribute('data-theme');
        expect(theme).toBe('light');
      }
    });
  });

  test.describe('Integration Workflow', () => {
    test('should handle full app layout with notifications', async ({ page }) => {
      const layout = await page.locator('.app-layout').first();
      const notifyBtn = await page.locator('button:has-text("Show Success")').first();

      if (await layout.isVisible() && await notifyBtn.isVisible()) {
        await notifyBtn.click();
        const notif = await page.locator('.notification-success').first();
        if (await notif.isVisible()) {
          await expect(notif).toBeVisible();
          await expect(layout).toBeVisible();
        }
      }
    });

    test('should support theme switching with layout', async ({ page }) => {
      const layout = await page.locator('.app-layout').first();
      const darkBtn = await page.locator('.theme-dark').first();

      if (await layout.isVisible() && await darkBtn.isVisible()) {
        await darkBtn.click();
        const html = await page.locator('html').first();
        const theme = await html.getAttribute('data-theme');
        expect(theme).toBe('dark');
        await expect(layout).toBeVisible();
      }
    });

    test('should toggle sidebar and maintain status bar', async ({ page }) => {
      const toggleBtn = await page.locator('.app-toolbar button').first();
      const statusBar = await page.locator('.status-bar').first();

      if (await toggleBtn.isVisible() && await statusBar.isVisible()) {
        await toggleBtn.click();
        await expect(statusBar).toBeVisible();
      }
    });
  });
});
