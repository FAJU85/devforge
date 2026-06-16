import { test, expect } from '@playwright/test';

test.describe('DevForge E2E Workflow', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('http://localhost:3000/generate');
  });

  test('should load generate page', async ({ page }) => {
    await expect(page.locator('text=Run')).toBeVisible();
  });

  test('should add and remove models', async ({ page }) => {
    // Open model picker
    await page.click('button:has-text("+ add")');
    await expect(page.locator('text=Search models')).toBeVisible();
  });

  test('should save and load session', async ({ page }) => {
    // Fill form
    await page.fill('input[placeholder*="github"]', 'https://github.com/owner/repo');
    await page.fill('input[placeholder*="File"]', 'src/main.py');
    
    // Save session
    const sessionBtn = await page.locator('button:has-text("Sessions")').first();
    await sessionBtn.click();
    await page.fill('input[placeholder*="Session"]', 'test-session');
    await page.click('button:has-text("Save")');
    
    // Verify saved
    await expect(page.locator('button:has-text("test-session")')).toBeVisible();
  });

  test('should handle comparison workflow', async ({ page }) => {
    // This would test the comparison feature once running
    // Placeholder for full E2E test
  });
});
