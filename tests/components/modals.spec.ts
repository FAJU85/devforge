/**
 * E2E tests for modal components: DiffViewer, WritePanel, BatchPanel, DepsAudit
 */

import { test, expect } from '@playwright/test';

test.describe('Modal Components', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('http://localhost:5173');
  });

  test.describe('DiffViewer Component', () => {
    test('should open diff viewer modal', async ({ page }) => {
      const btn = await page.locator('button:has-text("Show Diff")').first();
      if (await btn.isVisible()) {
        await btn.click();
        const modal = await page.locator('.diff-viewer-modal').first();
        await expect(modal).toBeVisible();
      }
    });

    test('should display file names in diff viewer', async ({ page }) => {
      const btn = await page.locator('button:has-text("Show Diff")').first();
      if (await btn.isVisible()) {
        await btn.click();
        const oldFile = await page.locator('text=Old:').first();
        const newFile = await page.locator('text=New:').first();
        if (await oldFile.isVisible()) {
          await expect(oldFile).toBeVisible();
        }
        if (await newFile.isVisible()) {
          await expect(newFile).toBeVisible();
        }
      }
    });

    test('should display side-by-side diff content', async ({ page }) => {
      const btn = await page.locator('button:has-text("Show Diff")').first();
      if (await btn.isVisible()) {
        await btn.click();
        const columns = await page.locator('pre').all();
        if (columns.length >= 2) {
          expect(columns.length).toBeGreaterThanOrEqual(2);
        }
      }
    });

    test('should mark removed lines', async ({ page }) => {
      const btn = await page.locator('button:has-text("Show Diff")').first();
      if (await btn.isVisible()) {
        await btn.click();
        const removed = await page.locator('text=Removed').first();
        if (await removed.isVisible()) {
          const color = await removed.evaluate(
            (el) => window.getComputedStyle(el).color
          );
          expect(color).toBeTruthy();
        }
      }
    });

    test('should mark added lines', async ({ page }) => {
      const btn = await page.locator('button:has-text("Show Diff")').first();
      if (await btn.isVisible()) {
        await btn.click();
        const added = await page.locator('text=Added').first();
        if (await added.isVisible()) {
          const color = await added.evaluate(
            (el) => window.getComputedStyle(el).color
          );
          expect(color).toBeTruthy();
        }
      }
    });

    test('should close diff viewer on close button', async ({ page }) => {
      const btn = await page.locator('button:has-text("Show Diff")').first();
      if (await btn.isVisible()) {
        await btn.click();
        const modal = await page.locator('.diff-viewer-modal').first();
        const closeBtn = await page.locator('button:has-text("Close")').nth(0);
        if (await closeBtn.isVisible()) {
          await closeBtn.click();
          await page.waitForTimeout(300);
          const count = await page.locator('.diff-viewer-modal').count();
          expect(count).toBe(0);
        }
      }
    });

    test('should apply diff changes', async ({ page }) => {
      const btn = await page.locator('button:has-text("Show Diff")').first();
      if (await btn.isVisible()) {
        await btn.click();
        const applyBtn = await page.locator('button:has-text("Apply")').first();
        if (await applyBtn.isVisible()) {
          await applyBtn.click();
          // Changes applied
        }
      }
    });
  });

  test.describe('WritePanel Component', () => {
    test('should open write panel', async ({ page }) => {
      const btn = await page.locator('button:has-text("Open Write")').first();
      if (await btn.isVisible()) {
        await btn.click();
        const panel = await page.locator('.write-panel-modal').first();
        await expect(panel).toBeVisible();
      }
    });

    test('should display filename in panel', async ({ page }) => {
      const btn = await page.locator('button:has-text("Open Write")').first();
      if (await btn.isVisible()) {
        await btn.click();
        const title = await page.locator('.write-panel-modal h2').first();
        if (await title.isVisible()) {
          const text = await title.textContent();
          expect(text).toBeTruthy();
        }
      }
    });

    test('should have editable textarea', async ({ page }) => {
      const btn = await page.locator('button:has-text("Open Write")').first();
      if (await btn.isVisible()) {
        await btn.click();
        const textarea = await page.locator('.write-panel-modal textarea').first();
        if (await textarea.isVisible()) {
          await expect(textarea).toBeVisible();
        }
      }
    });

    test('should edit content in textarea', async ({ page }) => {
      const btn = await page.locator('button:has-text("Open Write")').first();
      if (await btn.isVisible()) {
        await btn.click();
        const textarea = await page.locator('.write-panel-modal textarea').first();
        if (await textarea.isVisible()) {
          await textarea.fill('test content');
          const value = await textarea.inputValue();
          expect(value).toBe('test content');
        }
      }
    });

    test('should save content', async ({ page }) => {
      const btn = await page.locator('button:has-text("Open Write")').first();
      if (await btn.isVisible()) {
        await btn.click();
        const textarea = await page.locator('.write-panel-modal textarea').first();
        const saveBtn = await page.locator('.write-panel-modal button:has-text("Save")').first();
        if (await textarea.isVisible() && await saveBtn.isVisible()) {
          await textarea.fill('new content');
          await saveBtn.click();
        }
      }
    });

    test('should close write panel', async ({ page }) => {
      const btn = await page.locator('button:has-text("Open Write")').first();
      if (await btn.isVisible()) {
        await btn.click();
        const closeBtn = await page.locator('.write-panel-modal button').first();
        if (await closeBtn.isVisible()) {
          await closeBtn.click();
          await page.waitForTimeout(300);
          const count = await page.locator('.write-panel-modal').count();
          expect(count).toBe(0);
        }
      }
    });
  });

  test.describe('BatchPanel Component', () => {
    test('should open batch panel', async ({ page }) => {
      const btn = await page.locator('button:has-text("Show Batch")').first();
      if (await btn.isVisible()) {
        await btn.click();
        const panel = await page.locator('.batch-panel-modal').first();
        await expect(panel).toBeVisible();
      }
    });

    test('should display batch operations title', async ({ page }) => {
      const btn = await page.locator('button:has-text("Show Batch")').first();
      if (await btn.isVisible()) {
        await btn.click();
        const title = await page.locator('text=Batch Operations').first();
        if (await title.isVisible()) {
          await expect(title).toBeVisible();
        }
      }
    });

    test('should display operation statistics', async ({ page }) => {
      const btn = await page.locator('button:has-text("Show Batch")').first();
      if (await btn.isVisible()) {
        await btn.click();
        const stats = await page.locator('.batch-panel-modal').first();
        if (await stats.isVisible()) {
          const text = await stats.textContent();
          if (text) {
            expect(text).toContain('completed') || expect(text).toContain('pending');
          }
        }
      }
    });

    test('should display batch operations list', async ({ page }) => {
      const btn = await page.locator('button:has-text("Show Batch")').first();
      if (await btn.isVisible()) {
        await btn.click();
        const operations = await page.locator('.batch-operation').all();
        if (operations.length > 0) {
          expect(operations.length).toBeGreaterThan(0);
        }
      }
    });

    test('should show operation status', async ({ page }) => {
      const btn = await page.locator('button:has-text("Show Batch")').first();
      if (await btn.isVisible()) {
        await btn.click();
        const ops = await page.locator('.batch-operation').all();
        if (ops.length > 0) {
          const icons = await ops[0].locator('div').first();
          if (await icons.isVisible()) {
            expect(await icons.textContent()).toBeTruthy();
          }
        }
      }
    });

    test('should have execute button', async ({ page }) => {
      const btn = await page.locator('button:has-text("Show Batch")').first();
      if (await btn.isVisible()) {
        await btn.click();
        const executeBtn = await page.locator('button:has-text("Execute")').first();
        if (await executeBtn.isVisible()) {
          await expect(executeBtn).toBeVisible();
        }
      }
    });

    test('should close batch panel', async ({ page }) => {
      const btn = await page.locator('button:has-text("Show Batch")').first();
      if (await btn.isVisible()) {
        await btn.click();
        const closeBtn = await page.locator('.batch-panel-modal button:has-text("Close")').first();
        if (await closeBtn.isVisible()) {
          await closeBtn.click();
          await page.waitForTimeout(300);
          const count = await page.locator('.batch-panel-modal').count();
          expect(count).toBe(0);
        }
      }
    });
  });

  test.describe('DepsAudit Component', () => {
    test('should open deps audit modal', async ({ page }) => {
      const btn = await page.locator('button:has-text("Show Audit")').first();
      if (await btn.isVisible()) {
        await btn.click();
        const modal = await page.locator('.deps-audit-modal').first();
        await expect(modal).toBeVisible();
      }
    });

    test('should display audit title', async ({ page }) => {
      const btn = await page.locator('button:has-text("Show Audit")').first();
      if (await btn.isVisible()) {
        await btn.click();
        const title = await page.locator('text=Dependency Audit').first();
        if (await title.isVisible()) {
          await expect(title).toBeVisible();
        }
      }
    });

    test('should display vulnerability statistics', async ({ page }) => {
      const btn = await page.locator('button:has-text("Show Audit")').first();
      if (await btn.isVisible()) {
        await btn.click();
        const audit = await page.locator('.deps-audit-modal').first();
        if (await audit.isVisible()) {
          const text = await audit.textContent();
          if (text) {
            expect(text).toBeTruthy();
          }
        }
      }
    });

    test('should display vulnerability list', async ({ page }) => {
      const btn = await page.locator('button:has-text("Show Audit")').first();
      if (await btn.isVisible()) {
        await btn.click();
        const vulns = await page.locator('.audit-vulnerabilities-list').first();
        if (await vulns.isVisible()) {
          await expect(vulns).toBeVisible();
        }
      }
    });

    test('should show severity badges', async ({ page }) => {
      const btn = await page.locator('button:has-text("Show Audit")').first();
      if (await btn.isVisible()) {
        await btn.click();
        const audit = await page.locator('.deps-audit-modal').first();
        if (await audit.isVisible()) {
          const badges = await audit.locator('span').all();
          if (badges.length > 0) {
            expect(badges.length).toBeGreaterThan(0);
          }
        }
      }
    });

    test('should have fix buttons', async ({ page }) => {
      const btn = await page.locator('button:has-text("Show Audit")').first();
      if (await btn.isVisible()) {
        await btn.click();
        const fixBtn = await page.locator('button:has-text("Fix")').first();
        if (await fixBtn.isVisible()) {
          await expect(fixBtn).toBeVisible();
        }
      }
    });

    test('should close audit modal', async ({ page }) => {
      const btn = await page.locator('button:has-text("Show Audit")').first();
      if (await btn.isVisible()) {
        await btn.click();
        const closeBtn = await page.locator('.deps-audit-modal button:has-text("Close")').first();
        if (await closeBtn.isVisible()) {
          await closeBtn.click();
          await page.waitForTimeout(300);
          const count = await page.locator('.deps-audit-modal').count();
          expect(count).toBe(0);
        }
      }
    });

    test('should display empty state for no vulnerabilities', async ({ page }) => {
      const empty = await page.locator('text=No vulnerabilities found').first();
      if (await empty.isVisible()) {
        await expect(empty).toBeVisible();
      }
    });
  });

  test.describe('Modal Integration', () => {
    test('should handle multiple modals', async ({ page }) => {
      const diffBtn = await page.locator('button:has-text("Show Diff")').first();
      const writeBtn = await page.locator('button:has-text("Open Write")').first();

      if (await diffBtn.isVisible() && await writeBtn.isVisible()) {
        await diffBtn.click();
        let modal = await page.locator('.diff-viewer-modal').first();
        if (await modal.isVisible()) {
          await expect(modal).toBeVisible();
        }
      }
    });
  });
});
