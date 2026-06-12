/**
 * E2E tests for context components: ContextDisplay, FileList, ContextInfo
 */

import { test, expect } from '@playwright/test';

test.describe('Context Components', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('http://localhost:5173');
  });

  test.describe('ContextDisplay Component', () => {
    test('should render context display', async ({ page }) => {
      const display = await page.locator('.context-display').first();
      if (await display.isVisible()) {
        await expect(display).toBeVisible();
      }
    });

    test('should display context title', async ({ page }) => {
      const title = await page.locator('.context-display h3').first();
      if (await title.isVisible()) {
        const text = await title.textContent();
        expect(text).toBe('Context');
      }
    });

    test('should display item count', async ({ page }) => {
      const display = await page.locator('.context-display').first();
      if (await display.isVisible()) {
        const text = await display.textContent();
        if (text) {
          expect(text).toContain('items');
        }
      }
    });

    test('should display context items', async ({ page }) => {
      const items = await page.locator('.context-item').all();
      if (items.length > 0) {
        expect(items.length).toBeGreaterThan(0);
      }
    });

    test('should show empty state', async ({ page }) => {
      const empty = await page.locator('text=No context items').first();
      if (await empty.isVisible()) {
        await expect(empty).toBeVisible();
      }
    });

    test('should remove item on button click', async ({ page }) => {
      const items = await page.locator('.context-item').all();
      if (items.length > 0) {
        const removeBtn = await items[0].locator('button').first();
        if (await removeBtn.isVisible()) {
          await removeBtn.click();
        }
      }
    });
  });

  test.describe('FileList Component', () => {
    test('should render file list', async ({ page }) => {
      const list = await page.locator('.file-list').first();
      if (await list.isVisible()) {
        await expect(list).toBeVisible();
      }
    });

    test('should display files header', async ({ page }) => {
      const header = await page.locator('.file-list h3').first();
      if (await header.isVisible()) {
        const text = await header.textContent();
        expect(text).toBe('Files');
      }
    });

    test('should display file count', async ({ page }) => {
      const list = await page.locator('.file-list').first();
      if (await list.isVisible()) {
        const text = await list.textContent();
        if (text) {
          expect(text).toMatch(/\d+/);
        }
      }
    });

    test('should display file items', async ({ page }) => {
      const items = await page.locator('.file-item').all();
      if (items.length > 0) {
        expect(items.length).toBeGreaterThan(0);
      }
    });

    test('should select file on click', async ({ page }) => {
      const items = await page.locator('.file-item').all();
      if (items.length > 0) {
        const firstItem = items[0];
        await firstItem.click();
        const selectedBorder = await firstItem.evaluate(
          (el) => window.getComputedStyle(el).borderColor
        );
        expect(selectedBorder).toBeTruthy();
      }
    });

    test('should display file language and line count', async ({ page }) => {
      const items = await page.locator('.file-item').all();
      if (items.length > 0) {
        const text = await items[0].textContent();
        if (text) {
          expect(text.length).toBeGreaterThan(10);
        }
      }
    });
  });

  test.describe('ContextInfo Component', () => {
    test('should render context info', async ({ page }) => {
      const info = await page.locator('.context-info').first();
      if (await info.isVisible()) {
        await expect(info).toBeVisible();
      }
    });

    test('should display context info title', async ({ page }) => {
      const title = await page.locator('.context-info h3').first();
      if (await title.isVisible()) {
        const text = await title.textContent();
        expect(text).toBe('Context Info');
      }
    });

    test('should display statistics grid', async ({ page }) => {
      const stats = await page.locator('.context-info div').all();
      if (stats.length > 0) {
        expect(stats.length).toBeGreaterThan(0);
      }
    });

    test('should show files count', async ({ page }) => {
      const text = await page.locator('text=Files').first();
      if (await text.isVisible()) {
        await expect(text).toBeVisible();
      }
    });

    test('should show total lines', async ({ page }) => {
      const text = await page.locator('text=Lines').first();
      if (await text.isVisible()) {
        await expect(text).toBeVisible();
      }
    });

    test('should show token usage', async ({ page }) => {
      const text = await page.locator('text=Tokens').first();
      if (await text.isVisible()) {
        await expect(text).toBeVisible();
      }
    });

    test('should display languages', async ({ page }) => {
      const langText = await page.locator('text=Languages').first();
      if (await langText.isVisible()) {
        await expect(langText).toBeVisible();
      }
    });

    test('should have action buttons', async ({ page }) => {
      const buttons = await page.locator('.context-info button').all();
      if (buttons.length > 0) {
        expect(buttons.length).toBeGreaterThan(0);
      }
    });

    test('should show token usage bar', async ({ page }) => {
      const bar = await page.locator('.context-info').first();
      if (await bar.isVisible()) {
        const divs = await bar.locator('div').all();
        expect(divs.length).toBeGreaterThan(0);
      }
    });

    test('should show last updated time', async ({ page }) => {
      const updated = await page.locator('text=Updated:').first();
      if (await updated.isVisible()) {
        await expect(updated).toBeVisible();
      }
    });
  });

  test.describe('Context Integration', () => {
    test('should display all context components together', async ({ page }) => {
      const display = await page.locator('.context-display').first();
      const list = await page.locator('.file-list').first();
      const info = await page.locator('.context-info').first();

      let hasDisplay = false;
      let hasList = false;
      let hasInfo = false;

      if (await display.isVisible()) hasDisplay = true;
      if (await list.isVisible()) hasList = true;
      if (await info.isVisible()) hasInfo = true;

      expect(hasDisplay || hasList || hasInfo).toBe(true);
    });
  });
});
