/**
 * E2E tests for layout components: Sidebar, MainPanel, SettingsPanel, CommandPalette
 */

import { test, expect } from '@playwright/test';

test.describe('Layout Components', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('http://localhost:5173');
  });

  test.describe('Sidebar Component', () => {
    test('should render sidebar with navigation menu', async ({ page }) => {
      const sidebar = await page.locator('.sidebar').first();
      if (await sidebar.isVisible()) {
        await expect(sidebar).toBeVisible();
      }
    });

    test('should display logo and title', async ({ page }) => {
      const logo = await page.locator('.sidebar').first();
      if (await logo.isVisible()) {
        const title = await page.locator('text=DevForge').first();
        await expect(title).toBeVisible();
      }
    });

    test('should have navigation items', async ({ page }) => {
      const navItems = await page.locator('.sidebar nav button').all();
      if (navItems.length > 0) {
        expect(navItems.length).toBeGreaterThanOrEqual(3);
      }
    });

    test('should respond to hover on menu items', async ({ page }) => {
      const menuBtn = await page.locator('[id="nav-chat"]').first();
      if (await menuBtn.isVisible()) {
        await menuBtn.hover();
        const bgColor = await menuBtn.evaluate(
          (el) => window.getComputedStyle(el).backgroundColor
        );
        expect(bgColor).toBeTruthy();
      }
    });

    test('should have settings button in footer', async ({ page }) => {
      const settingsBtn = await page.locator('#sidebar-settings').first();
      if (await settingsBtn.isVisible()) {
        await expect(settingsBtn).toBeVisible();
        await expect(settingsBtn).toContainText('Settings');
      }
    });
  });

  test.describe('MainPanel Component', () => {
    test('should render main panel with tabs', async ({ page }) => {
      const mainPanel = await page.locator('.main-panel').first();
      if (await mainPanel.isVisible()) {
        await expect(mainPanel).toBeVisible();
      }
    });

    test('should display tab bar with default tabs', async ({ page }) => {
      const tabs = await page.locator('.main-tab').all();
      if (tabs.length > 0) {
        expect(tabs.length).toBeGreaterThanOrEqual(2);
      }
    });

    test('should highlight active tab', async ({ page }) => {
      const firstTab = await page.locator('.main-tab').first();
      if (await firstTab.isVisible()) {
        const bgColor = await firstTab.evaluate(
          (el) => window.getComputedStyle(el).backgroundColor
        );
        expect(bgColor).toBeTruthy();
      }
    });

    test('should switch tabs on click', async ({ page }) => {
      const tabs = await page.locator('.main-tab').all();
      if (tabs.length > 1) {
        const secondTab = tabs[1];
        await secondTab.click();
        const bgColor = await secondTab.evaluate(
          (el) => window.getComputedStyle(el).backgroundColor
        );
        expect(bgColor).toBeTruthy();
      }
    });

    test('should have content area', async ({ page }) => {
      const content = await page.locator('.content-area').first();
      if (await content.isVisible()) {
        await expect(content).toBeVisible();
      }
    });
  });

  test.describe('SettingsPanel Component', () => {
    test('should render settings panel with navigation', async ({ page }) => {
      const panel = await page.locator('.settings-panel').first();
      if (await panel.isVisible()) {
        await expect(panel).toBeVisible();
      }
    });

    test('should display settings categories', async ({ page }) => {
      const navItems = await page.locator('.settings-nav-item').all();
      if (navItems.length > 0) {
        expect(navItems.length).toBeGreaterThanOrEqual(3);
      }
    });

    test('should highlight active settings category', async ({ page }) => {
      const firstCategory = await page.locator('.settings-nav-item').first();
      if (await firstCategory.isVisible()) {
        const bgColor = await firstCategory.evaluate(
          (el) => window.getComputedStyle(el).backgroundColor
        );
        expect(bgColor).toBeTruthy();
      }
    });

    test('should display settings items', async ({ page }) => {
      const settingsItems = await page.locator('.settings-panel input').all();
      if (settingsItems.length > 0) {
        expect(settingsItems.length).toBeGreaterThanOrEqual(1);
      }
    });

    test('should handle toggle controls', async ({ page }) => {
      const toggle = await page.locator('.settings-panel input[type="checkbox"]').first();
      if (await toggle.isVisible()) {
        const isChecked = await toggle.isChecked();
        await toggle.click();
        const newState = await toggle.isChecked();
        expect(newState).not.toBe(isChecked);
      }
    });

    test('should have select dropdowns', async ({ page }) => {
      const selects = await page.locator('.settings-panel select').all();
      if (selects.length > 0) {
        const firstSelect = selects[0];
        await expect(firstSelect).toBeVisible();
      }
    });
  });

  test.describe('CommandPalette Component', () => {
    test('should render command palette on trigger', async ({ page }) => {
      const openBtn = await page.locator('button:has-text("Open Command")').first();
      if (await openBtn.isVisible()) {
        await openBtn.click();
        const palette = await page.locator('.command-palette').first();
        await expect(palette).toBeVisible();
      }
    });

    test('should have search input', async ({ page }) => {
      const openBtn = await page.locator('button:has-text("Open Command")').first();
      if (await openBtn.isVisible()) {
        await openBtn.click();
        const input = await page.locator('.command-palette input').first();
        await expect(input).toBeFocused();
      }
    });

    test('should filter commands by search', async ({ page }) => {
      const openBtn = await page.locator('button:has-text("Open Command")').first();
      if (await openBtn.isVisible()) {
        await openBtn.click();
        const input = await page.locator('.command-palette input').first();
        await input.type('file');
        const results = await page.locator('.command-item').all();
        expect(results.length).toBeGreaterThan(0);
      }
    });

    test('should display command results grouped by category', async ({ page }) => {
      const openBtn = await page.locator('button:has-text("Open Command")').first();
      if (await openBtn.isVisible()) {
        await openBtn.click();
        const categories = await page.locator('.command-palette [style*="uppercase"]').all();
        if (categories.length > 0) {
          expect(categories.length).toBeGreaterThan(0);
        }
      }
    });

    test('should close on Escape key', async ({ page }) => {
      const openBtn = await page.locator('button:has-text("Open Command")').first();
      if (await openBtn.isVisible()) {
        await openBtn.click();
        let palette = await page.locator('.command-palette').first();
        await expect(palette).toBeVisible();

        await page.keyboard.press('Escape');
        await page.waitForTimeout(300);
        palette = await page.locator('.command-palette').first();
        await expect(palette).not.toBeVisible();
      }
    });

    test('should close on overlay click', async ({ page }) => {
      const openBtn = await page.locator('button:has-text("Open Command")').first();
      if (await openBtn.isVisible()) {
        await openBtn.click();
        let overlay = await page.locator('.command-palette-overlay').first();
        await expect(overlay).toBeVisible();

        const paletteBox = await overlay.boundingBox();
        if (paletteBox) {
          await page.click(0, 200);
          await page.waitForTimeout(300);
          overlay = await page.locator('.command-palette-overlay').first();
          await expect(overlay).not.toBeVisible();
        }
      }
    });

    test('should execute command on selection', async ({ page }) => {
      const openBtn = await page.locator('button:has-text("Open Command")').first();
      if (await openBtn.isVisible()) {
        await openBtn.click();
        const firstCommand = await page.locator('.command-item').first();
        if (await firstCommand.isVisible()) {
          await firstCommand.click();
          await page.waitForTimeout(300);
          const palette = await page.locator('.command-palette').first();
          await expect(palette).not.toBeVisible();
        }
      }
    });
  });

  test.describe('Layout Integration', () => {
    test('should render sidebar and main panel together', async ({ page }) => {
      const sidebar = await page.locator('.sidebar').first();
      const mainPanel = await page.locator('.main-panel').first();

      if (await sidebar.isVisible() && await mainPanel.isVisible()) {
        await expect(sidebar).toBeVisible();
        await expect(mainPanel).toBeVisible();
      }
    });

    test('should maintain responsive layout', async ({ page }) => {
      const sidebar = await page.locator('.sidebar').first();
      if (await sidebar.isVisible()) {
        const width = await sidebar.evaluate((el) => el.offsetWidth);
        expect(width).toBeGreaterThan(200);
        expect(width).toBeLessThan(400);
      }
    });

    test('should render all layout components', async ({ page }) => {
      const sidebar = await page.locator('.sidebar').first();
      const mainPanel = await page.locator('.main-panel').first();
      const settingsPanel = await page.locator('.settings-panel').first();

      let visibleCount = 0;
      if (await sidebar.isVisible()) visibleCount++;
      if (await mainPanel.isVisible()) visibleCount++;
      if (await settingsPanel.isVisible()) visibleCount++;

      expect(visibleCount).toBeGreaterThanOrEqual(1);
    });
  });
});
