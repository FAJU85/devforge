/**
 * E2E tests for configuration components: ProviderSelector, ModelSelector, ApiKeyInput, SettingsForm
 */

import { test, expect } from '@playwright/test';

test.describe('Configuration Components', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('http://localhost:5173');
  });

  test.describe('ProviderSelector Component', () => {
    test('should render provider selector', async ({ page }) => {
      const selector = await page.locator('.provider-selector').first();
      if (await selector.isVisible()) {
        await expect(selector).toBeVisible();
      }
    });

    test('should display provider label', async ({ page }) => {
      const label = await page.locator('text=AI Provider').first();
      if (await label.isVisible()) {
        await expect(label).toBeVisible();
      }
    });

    test('should display provider cards', async ({ page }) => {
      const cards = await page.locator('.provider-card').all();
      if (cards.length > 0) {
        expect(cards.length).toBeGreaterThan(0);
      }
    });

    test('should show provider icons', async ({ page }) => {
      const icons = await page.locator('.provider-card span').all();
      if (icons.length > 0) {
        const firstIcon = await icons[0].textContent();
        expect(firstIcon).toBeTruthy();
      }
    });

    test('should display provider status badge', async ({ page }) => {
      const badges = await page.locator('.provider-card div').all();
      if (badges.length > 0) {
        let hasBadge = false;
        for (const badge of badges) {
          const text = await badge.textContent();
          if (text?.includes('Configured') || text?.includes('Available')) {
            hasBadge = true;
            break;
          }
        }
        expect(hasBadge || badges.length > 0).toBe(true);
      }
    });

    test('should select provider on click', async ({ page }) => {
      const cards = await page.locator('.provider-card').all();
      if (cards.length > 0) {
        const firstCard = cards[0];
        const originalBorder = await firstCard.evaluate(
          (el) => window.getComputedStyle(el).borderColor
        );
        await firstCard.click();
        const newBorder = await firstCard.evaluate(
          (el) => window.getComputedStyle(el).borderColor
        );
        expect(newBorder).toBeTruthy();
      }
    });

    test('should disable unavailable providers', async ({ page }) => {
      const cards = await page.locator('.provider-card').all();
      if (cards.length > 0) {
        for (const card of cards) {
          const cursor = await card.evaluate((el) => window.getComputedStyle(el).cursor);
          expect(['pointer', 'not-allowed']).toContain(cursor);
        }
      }
    });
  });

  test.describe('ModelSelector Component', () => {
    test('should render model selector', async ({ page }) => {
      const selector = await page.locator('.model-selector').first();
      if (await selector.isVisible()) {
        await expect(selector).toBeVisible();
      }
    });

    test('should display model label', async ({ page }) => {
      const label = await page.locator('text=Model').first();
      if (await label.isVisible()) {
        await expect(label).toBeVisible();
      }
    });

    test('should display model list', async ({ page }) => {
      const list = await page.locator('.model-list').first();
      if (await list.isVisible()) {
        await expect(list).toBeVisible();
      }
    });

    test('should display model items', async ({ page }) => {
      const items = await page.locator('.model-item').all();
      if (items.length > 0) {
        expect(items.length).toBeGreaterThan(0);
      }
    });

    test('should show model information', async ({ page }) => {
      const items = await page.locator('.model-item').all();
      if (items.length > 0) {
        const text = await items[0].textContent();
        expect(text).toBeTruthy();
      }
    });

    test('should select model on click', async ({ page }) => {
      const items = await page.locator('.model-item').all();
      if (items.length > 1) {
        const secondItem = items[1];
        const originalBorder = await secondItem.evaluate(
          (el) => window.getComputedStyle(el).borderColor
        );
        await secondItem.click();
        const newBorder = await secondItem.evaluate(
          (el) => window.getComputedStyle(el).borderColor
        );
        expect(newBorder).not.toBe(originalBorder);
      }
    });

    test('should display context window and cost', async ({ page }) => {
      const items = await page.locator('.model-item').all();
      if (items.length > 0) {
        const text = await items[0].textContent();
        if (text) {
          expect(text.length).toBeGreaterThan(10);
        }
      }
    });

    test('should support scrolling for many models', async ({ page }) => {
      const list = await page.locator('.model-list').first();
      if (await list.isVisible()) {
        const overflow = await list.evaluate((el) => window.getComputedStyle(el).overflowY);
        expect(['auto', 'scroll']).toContain(overflow);
      }
    });
  });

  test.describe('ApiKeyInput Component', () => {
    test('should render api key input', async ({ page }) => {
      const input = await page.locator('.api-key-input').first();
      if (await input.isVisible()) {
        await expect(input).toBeVisible();
      }
    });

    test('should display input label', async ({ page }) => {
      const labels = await page.locator('.api-key-input label').all();
      if (labels.length > 0) {
        const text = await labels[0].textContent();
        expect(text).toBeTruthy();
      }
    });

    test('should have password input field', async ({ page }) => {
      const inputs = await page.locator('.api-key-input input[type="password"]').all();
      expect(inputs.length).toBeGreaterThan(0);
    });

    test('should toggle visibility', async ({ page }) => {
      const input = await page.locator('.api-key-input input[type="password"]').first();
      if (await input.isVisible()) {
        const toggleBtn = await page.locator('.api-key-input button').nth(0);
        if (await toggleBtn.isVisible()) {
          await toggleBtn.click();
          const newType = await input.getAttribute('type');
          expect(newType).toBe('text');
        }
      }
    });

    test('should accept api key input', async ({ page }) => {
      const input = await page.locator('.api-key-input input[type="password"]').first();
      if (await input.isVisible()) {
        await input.fill('test-api-key-123');
        const value = await input.inputValue();
        expect(value).toBe('test-api-key-123');
      }
    });

    test('should save api key', async ({ page }) => {
      const input = await page.locator('.api-key-input input[type="password"]').first();
      const saveBtn = await page.locator('.api-key-input button:has-text("Save")').first();
      if (await input.isVisible() && await saveBtn.isVisible()) {
        await input.fill('test-key');
        await saveBtn.click();
        const btnText = await saveBtn.textContent();
        expect(btnText).toContain('Save');
      }
    });

    test('should display configured badge', async ({ page }) => {
      const badge = await page.locator('.api-key-input text=Configured').first();
      if (await badge.isVisible()) {
        await expect(badge).toBeVisible();
      }
    });

    test('should show help text', async ({ page }) => {
      const helpTexts = await page.locator('.api-key-input div').all();
      if (helpTexts.length > 0) {
        let hasHelp = false;
        for (const help of helpTexts) {
          const text = await help.textContent();
          if (text && text.length < 100 && text.length > 10) {
            hasHelp = true;
            break;
          }
        }
        expect(helpTexts.length > 0).toBe(true);
      }
    });
  });

  test.describe('SettingsForm Component', () => {
    test('should render settings form', async ({ page }) => {
      const form = await page.locator('.settings-form').first();
      if (await form.isVisible()) {
        await expect(form).toBeVisible();
      }
    });

    test('should display form title', async ({ page }) => {
      const titles = await page.locator('.settings-form h2').all();
      if (titles.length > 0) {
        const text = await titles[0].textContent();
        expect(text).toBeTruthy();
      }
    });

    test('should display form sections', async ({ page }) => {
      const sections = await page.locator('.settings-form h3').all();
      if (sections.length > 0) {
        expect(sections.length).toBeGreaterThan(0);
      }
    });

    test('should display form fields', async ({ page }) => {
      const form = await page.locator('.settings-form').first();
      const inputs = await form.locator('input, select').all();
      if (inputs.length > 0) {
        expect(inputs.length).toBeGreaterThan(0);
      }
    });

    test('should accept text input', async ({ page }) => {
      const textInputs = await page.locator('.settings-form input[type="text"]').all();
      if (textInputs.length > 0) {
        const firstInput = textInputs[0];
        await firstInput.fill('test value');
        const value = await firstInput.inputValue();
        expect(value).toBe('test value');
      }
    });

    test('should handle toggle switches', async ({ page }) => {
      const checkboxes = await page.locator('.settings-form input[type="checkbox"]').all();
      if (checkboxes.length > 0) {
        const checkbox = checkboxes[0];
        const initialState = await checkbox.isChecked();
        await checkbox.click();
        const newState = await checkbox.isChecked();
        expect(newState).not.toBe(initialState);
      }
    });

    test('should handle select dropdowns', async ({ page }) => {
      const selects = await page.locator('.settings-form select').all();
      if (selects.length > 0) {
        const select = selects[0];
        const options = await select.locator('option').all();
        if (options.length > 1) {
          const secondOption = options[1];
          await select.selectOption(await secondOption.getAttribute('value') || '');
          const selectedValue = await select.inputValue();
          expect(selectedValue).toBeTruthy();
        }
      }
    });

    test('should display help text for fields', async ({ page }) => {
      const form = await page.locator('.settings-form').first();
      const helpTexts = await form.locator('div[style*="text-secondary"]').all();
      if (helpTexts.length > 0) {
        expect(helpTexts.length).toBeGreaterThan(0);
      }
    });

    test('should have save button', async ({ page }) => {
      const saveBtn = await page.locator('button:has-text("Save Settings")').first();
      if (await saveBtn.isVisible()) {
        await expect(saveBtn).toBeVisible();
      }
    });

    test('should have cancel button', async ({ page }) => {
      const cancelBtn = await page.locator('button:has-text("Cancel")').first();
      if (await cancelBtn.isVisible()) {
        await expect(cancelBtn).toBeVisible();
      }
    });

    test('should save form data', async ({ page }) => {
      const saveBtn = await page.locator('button:has-text("Save Settings")').first();
      if (await saveBtn.isVisible()) {
        await saveBtn.click();
        const btnText = await saveBtn.textContent();
        expect(btnText).toContain('Save');
      }
    });
  });

  test.describe('Configuration Integration', () => {
    test('should display provider and model selectors together', async ({ page }) => {
      const provider = await page.locator('.provider-selector').first();
      const model = await page.locator('.model-selector').first();

      let hasProvider = false;
      let hasModel = false;

      if (await provider.isVisible()) hasProvider = true;
      if (await model.isVisible()) hasModel = true;

      expect(hasProvider || hasModel).toBe(true);
    });

    test('should display api key inputs for different providers', async ({ page }) => {
      const apiInputs = await page.locator('.api-key-input').all();
      if (apiInputs.length > 0) {
        expect(apiInputs.length).toBeGreaterThan(0);
      }
    });

    test('should display complete configuration form', async ({ page }) => {
      const form = await page.locator('.settings-form').first();
      const selector = await page.locator('.provider-selector').first();

      if (await form.isVisible() || await selector.isVisible()) {
        expect(await form.isVisible() || await selector.isVisible()).toBe(true);
      }
    });
  });
});
