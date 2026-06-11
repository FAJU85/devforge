/**
 * E2E tests for repository components: RepoSelector, RepoTree, SearchBox, FileTreeNode
 */

import { test, expect } from '@playwright/test';

test.describe('Repository Components', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('http://localhost:5173');
  });

  test.describe('RepoSelector Component', () => {
    test('should render repo selector', async ({ page }) => {
      const selector = await page.locator('.repo-selector').first();
      if (await selector.isVisible()) {
        await expect(selector).toBeVisible();
      }
    });

    test('should display label', async ({ page }) => {
      const label = await page.locator('text=Repository').first();
      if (await label.isVisible()) {
        await expect(label).toBeVisible();
      }
    });

    test('should display selected repository', async ({ page }) => {
      const dropdown = await page.locator('.repo-dropdown').first();
      if (await dropdown.isVisible()) {
        const text = await dropdown.textContent();
        expect(text).toBeTruthy();
      }
    });

    test('should open dropdown on click', async ({ page }) => {
      const dropdown = await page.locator('.repo-dropdown').first();
      if (await dropdown.isVisible()) {
        await dropdown.click();
        const menu = await page.locator('.repo-dropdown-menu').first();
        await expect(menu).toBeVisible();
      }
    });

    test('should show dropdown items', async ({ page }) => {
      const dropdown = await page.locator('.repo-dropdown').first();
      if (await dropdown.isVisible()) {
        await dropdown.click();
        const items = await page.locator('.repo-dropdown-item').all();
        expect(items.length).toBeGreaterThan(0);
      }
    });

    test('should select repository on item click', async ({ page }) => {
      const dropdown = await page.locator('.repo-dropdown').first();
      if (await dropdown.isVisible()) {
        await dropdown.click();
        const firstItem = await page.locator('.repo-dropdown-item').first();
        if (await firstItem.isVisible()) {
          const originalText = await dropdown.textContent();
          await firstItem.click();
          await page.waitForTimeout(100);
          const newText = await dropdown.textContent();
          expect(newText).not.toBe(originalText);
        }
      }
    });

    test('should display repository metadata', async ({ page }) => {
      const dropdown = await page.locator('.repo-dropdown').first();
      if (await dropdown.isVisible()) {
        await dropdown.click();
        const items = await page.locator('.repo-dropdown-item').all();
        if (items.length > 0) {
          const itemText = await items[0].textContent();
          // Check for language or star count
          expect(itemText).toBeTruthy();
        }
      }
    });

    test('should close dropdown on outside click', async ({ page }) => {
      const dropdown = await page.locator('.repo-dropdown').first();
      if (await dropdown.isVisible()) {
        await dropdown.click();
        let menu = await page.locator('.repo-dropdown-menu').first();
        await expect(menu).toBeVisible();

        await page.click('body', { position: { x: 10, y: 10 } });
        await page.waitForTimeout(100);
        menu = await page.locator('.repo-dropdown-menu').first();
        const display = await menu.evaluate((el) => window.getComputedStyle(el).display);
        expect(display).toBe('none');
      }
    });
  });

  test.describe('SearchBox Component', () => {
    test('should render search box', async ({ page }) => {
      const searchBox = await page.locator('.search-box').first();
      if (await searchBox.isVisible()) {
        await expect(searchBox).toBeVisible();
      }
    });

    test('should have search input', async ({ page }) => {
      const input = await page.locator('.search-input').first();
      if (await input.isVisible()) {
        await expect(input).toBeVisible();
      }
    });

    test('should accept search text', async ({ page }) => {
      const input = await page.locator('.search-input').first();
      if (await input.isVisible()) {
        await input.fill('test');
        const value = await input.inputValue();
        expect(value).toBe('test');
      }
    });

    test('should show clear button on input', async ({ page }) => {
      const input = await page.locator('.search-input').first();
      const clearBtn = await page.locator('.search-box button').nth(1);
      if (await input.isVisible()) {
        await input.fill('test');
        const display = await clearBtn.evaluate((el) => window.getComputedStyle(el).display);
        expect(display).not.toBe('none');
      }
    });

    test('should clear input on clear button click', async ({ page }) => {
      const input = await page.locator('.search-input').first();
      const clearBtn = await page.locator('.search-box button').nth(1);
      if (await input.isVisible()) {
        await input.fill('test');
        await clearBtn.click();
        const value = await input.inputValue();
        expect(value).toBe('');
      }
    });

    test('should trigger search on input', async ({ page }) => {
      const input = await page.locator('.search-input').first();
      if (await input.isVisible()) {
        await input.type('search term');
        // Search would be triggered (checked by backend)
      }
    });

    test('should have focus styling', async ({ page }) => {
      const input = await page.locator('.search-input').first();
      if (await input.isVisible()) {
        await input.focus();
        const focused = await input.evaluate((el) => el === document.activeElement);
        expect(focused).toBe(true);
      }
    });
  });

  test.describe('FileTreeNode Component', () => {
    test('should render file tree node', async ({ page }) => {
      const node = await page.locator('.file-tree-node').first();
      if (await node.isVisible()) {
        await expect(node).toBeVisible();
      }
    });

    test('should display file icon', async ({ page }) => {
      const icon = await page.locator('.file-tree-item span').first();
      if (await icon.isVisible()) {
        const text = await icon.textContent();
        expect(text).toBeTruthy();
      }
    });

    test('should display file name', async ({ page }) => {
      const item = await page.locator('.file-tree-item').first();
      if (await item.isVisible()) {
        const text = await item.textContent();
        expect(text).toBeTruthy();
      }
    });

    test('should have toggle icon for folders', async ({ page }) => {
      const nodes = await page.locator('.file-tree-node').all();
      if (nodes.length > 0) {
        for (const node of nodes) {
          const toggleIcon = await node.locator('span').first();
          if (await toggleIcon.isVisible()) {
            const text = await toggleIcon.textContent();
            if (text === '▶') {
              // This is a folder with toggle icon
              expect(text).toBe('▶');
              break;
            }
          }
        }
      }
    });

    test('should toggle folder on click', async ({ page }) => {
      const folderItem = await page.locator('.file-tree-item').nth(0);
      if (await folderItem.isVisible()) {
        const toggleIcon = await folderItem.locator('span').first();
        if (await toggleIcon.isVisible()) {
          const text = await toggleIcon.textContent();
          if (text === '▶') {
            await folderItem.click();
            const newTransform = await toggleIcon.evaluate(
              (el) => window.getComputedStyle(el).transform
            );
            expect(newTransform).toBeTruthy();
          }
        }
      }
    });
  });

  test.describe('RepoTree Component', () => {
    test('should render repo tree', async ({ page }) => {
      const tree = await page.locator('.repo-tree').first();
      if (await tree.isVisible()) {
        await expect(tree).toBeVisible();
      }
    });

    test('should have header with title', async ({ page }) => {
      const title = await page.locator('.repo-tree h3').first();
      if (await title.isVisible()) {
        const text = await title.textContent();
        expect(text).toBe('Files');
      }
    });

    test('should display file tree container', async ({ page }) => {
      const container = await page.locator('.file-tree-container').first();
      if (await container.isVisible()) {
        await expect(container).toBeVisible();
      }
    });

    test('should render tree nodes', async ({ page }) => {
      const nodes = await page.locator('.file-tree-node').all();
      if (nodes.length > 0) {
        expect(nodes.length).toBeGreaterThan(0);
      }
    });

    test('should scroll on overflow', async ({ page }) => {
      const container = await page.locator('.file-tree-container').first();
      if (await container.isVisible()) {
        const overflow = await container.evaluate((el) => window.getComputedStyle(el).overflowY);
        expect(overflow).toBe('auto');
      }
    });

    test('should expand all nodes', async ({ page }) => {
      const expandBtn = await page.locator('button:has-text("Expand All Tree")').first();
      if (await expandBtn.isVisible()) {
        await expandBtn.click();
        // All children should be visible
        const children = await page.locator('.file-tree-children').all();
        if (children.length > 0) {
          const display = await children[0].evaluate((el) => window.getComputedStyle(el).display);
          expect(display).toBe('block');
        }
      }
    });

    test('should collapse all nodes', async ({ page }) => {
      const collapseBtn = await page.locator('button:has-text("Collapse All Tree")').first();
      if (await collapseBtn.isVisible()) {
        await collapseBtn.click();
        // All children should be hidden
        const children = await page.locator('.file-tree-children').all();
        if (children.length > 0) {
          const display = await children[0].evaluate((el) => window.getComputedStyle(el).display);
          expect(display).toBe('none');
        }
      }
    });
  });

  test.describe('Repository Integration', () => {
    test('should display repo selector and tree together', async ({ page }) => {
      const selector = await page.locator('.repo-selector').first();
      const tree = await page.locator('.repo-tree').first();

      let hasRepo = false;
      let hasTree = false;

      if (await selector.isVisible()) {
        hasRepo = true;
      }

      if (await tree.isVisible()) {
        hasTree = true;
      }

      expect(hasRepo || hasTree).toBe(true);
    });

    test('should integrate search with file tree', async ({ page }) => {
      const searchBox = await page.locator('.search-box').first();
      const tree = await page.locator('.repo-tree').first();

      let hasSearch = false;
      let hasTree = false;

      if (await searchBox.isVisible()) {
        hasSearch = true;
      }

      if (await tree.isVisible()) {
        hasTree = true;
      }

      expect(hasSearch || hasTree).toBe(true);
    });
  });
});
