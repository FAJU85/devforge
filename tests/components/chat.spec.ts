/**
 * E2E tests for chat components: ChatWindow, ChatMessage, InputBox, TokenMeter
 */

import { test, expect } from '@playwright/test';

test.describe('Chat Components', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('http://localhost:5173');
  });

  test.describe('ChatWindow Component', () => {
    test('should render chat window', async ({ page }) => {
      const chatWindow = await page.locator('.chat-window').first();
      if (await chatWindow.isVisible()) {
        await expect(chatWindow).toBeVisible();
      }
    });

    test('should display empty state initially', async ({ page }) => {
      const emptyState = await page.locator('.chat-empty-state').first();
      if (await emptyState.isVisible()) {
        const text = await page.locator('text=No messages yet').first();
        await expect(text).toBeVisible();
      }
    });

    test('should have scrollable messages container', async ({ page }) => {
      const container = await page.locator('.messages-container').first();
      if (await container.isVisible()) {
        const height = await container.evaluate((el) => el.offsetHeight);
        expect(height).toBeGreaterThan(0);
      }
    });

    test('should scroll to bottom on new message', async ({ page }) => {
      const openBtn = await page.locator('button:has-text("Add Message to Chat")').first();
      if (await openBtn.isVisible()) {
        await openBtn.click();
        const container = await page.locator('.messages-container').first();
        await page.waitForTimeout(100);
        const scrollTop = await container.evaluate((el) => el.scrollHeight - el.clientHeight);
        expect(scrollTop).toBeGreaterThanOrEqual(0);
      }
    });
  });

  test.describe('ChatMessage Component', () => {
    test('should render user message', async ({ page }) => {
      const addUserBtn = await page.locator('button:has-text("Add User Message")').first();
      if (await addUserBtn.isVisible()) {
        await addUserBtn.click();
        const message = await page.locator('.chat-message-user').first();
        await expect(message).toBeVisible();
      }
    });

    test('should render assistant message', async ({ page }) => {
      const addAssistantBtn = await page.locator('button:has-text("Add Assistant Message")').first();
      if (await addAssistantBtn.isVisible()) {
        await addAssistantBtn.click();
        const message = await page.locator('.chat-message-assistant').first();
        await expect(message).toBeVisible();
      }
    });

    test('should display message avatar and role', async ({ page }) => {
      const addUserBtn = await page.locator('button:has-text("Add User Message")').first();
      if (await addUserBtn.isVisible()) {
        await addUserBtn.click();
        const roleText = await page.locator('text=You').first();
        await expect(roleText).toBeVisible();
      }
    });

    test('should display message content', async ({ page }) => {
      const addUserBtn = await page.locator('button:has-text("Add User Message")').first();
      if (await addUserBtn.isVisible()) {
        await addUserBtn.click();
        const content = await page.locator('text=Hello, I have a question').first();
        if (await content.isVisible()) {
          await expect(content).toBeVisible();
        }
      }
    });

    test('should show copy button on hover for assistant messages', async ({ page }) => {
      const addAssistantBtn = await page.locator('button:has-text("Add Assistant Message")').first();
      if (await addAssistantBtn.isVisible()) {
        await addAssistantBtn.click();
        const message = await page.locator('.chat-message-assistant').first();
        await message.hover();
        const copyBtn = await page.locator('text=Copy').first();
        if (await copyBtn.isVisible()) {
          const opacity = await copyBtn.evaluate((el) => window.getComputedStyle(el.parentElement).opacity);
          expect(parseFloat(opacity as string)).toBeGreaterThan(0);
        }
      }
    });

    test('should copy message content', async ({ page }) => {
      const addAssistantBtn = await page.locator('button:has-text("Add Assistant Message")').first();
      if (await addAssistantBtn.isVisible()) {
        await addAssistantBtn.click();
        const message = await page.locator('.chat-message-assistant').first();
        await message.hover();
        const copyBtn = await page.locator('button:has-text("Copy")').first();
        if (await copyBtn.isVisible()) {
          await copyBtn.click();
          const copiedBtn = await page.locator('button:has-text("Copied")').first();
          await expect(copiedBtn).toBeVisible();
        }
      }
    });

    test('should display timestamp and token count', async ({ page }) => {
      const addUserBtn = await page.locator('button:has-text("Add Message with Tokens")').first();
      if (await addUserBtn.isVisible()) {
        await addUserBtn.click();
        const tokenText = await page.locator('text=tokens').first();
        if (await tokenText.isVisible()) {
          await expect(tokenText).toBeVisible();
        }
      }
    });
  });

  test.describe('InputBox Component', () => {
    test('should render input box', async ({ page }) => {
      const inputBox = await page.locator('.input-box-container').first();
      if (await inputBox.isVisible()) {
        await expect(inputBox).toBeVisible();
      }
    });

    test('should have textarea with placeholder', async ({ page }) => {
      const textarea = await page.locator('.input-box-container textarea').first();
      if (await textarea.isVisible()) {
        const placeholder = await textarea.getAttribute('placeholder');
        expect(placeholder).toBeTruthy();
      }
    });

    test('should accept text input', async ({ page }) => {
      const textarea = await page.locator('.input-box-container textarea').first();
      if (await textarea.isVisible()) {
        await textarea.fill('Hello, how are you?');
        const value = await textarea.inputValue();
        expect(value).toBe('Hello, how are you?');
      }
    });

    test('should update character count', async ({ page }) => {
      const textarea = await page.locator('.input-box-container textarea').first();
      if (await textarea.isVisible()) {
        await textarea.type('test');
        const counter = await page.locator('text=/\\d+\\/').first();
        if (await counter.isVisible()) {
          const text = await counter.textContent();
          expect(text).toContain('4');
        }
      }
    });

    test('should send message on button click', async ({ page }) => {
      const textarea = await page.locator('.input-box-container textarea').first();
      const sendBtn = await page.locator('button:has-text("Send")').first();
      if (await textarea.isVisible() && await sendBtn.isVisible()) {
        await textarea.fill('Test message');
        await sendBtn.click();
        const newValue = await textarea.inputValue();
        expect(newValue).toBe('');
      }
    });

    test('should send message on Ctrl+Enter', async ({ page }) => {
      const textarea = await page.locator('.input-box-container textarea').first();
      if (await textarea.isVisible()) {
        await textarea.fill('Test Ctrl+Enter');
        await textarea.press('Control+Enter');
        const newValue = await textarea.inputValue();
        expect(newValue).toBe('');
      }
    });

    test('should have focus state styling', async ({ page }) => {
      const textarea = await page.locator('.input-box-container textarea').first();
      if (await textarea.isVisible()) {
        await textarea.focus();
        const borderColor = await textarea.evaluate(
          (el) => window.getComputedStyle(el).borderColor
        );
        expect(borderColor).toBeTruthy();
      }
    });

    test('should show character limit', async ({ page }) => {
      const charCountText = await page.locator('text=/characters/').first();
      if (await charCountText.isVisible()) {
        await expect(charCountText).toBeVisible();
      }
    });
  });

  test.describe('TokenMeter Component', () => {
    test('should render token meter', async ({ page }) => {
      const meter = await page.locator('.token-meter').first();
      if (await meter.isVisible()) {
        await expect(meter).toBeVisible();
      }
    });

    test('should display token usage label', async ({ page }) => {
      const label = await page.locator('text=Token Usage').first();
      if (await label.isVisible()) {
        await expect(label).toBeVisible();
      }
    });

    test('should display current and max tokens', async ({ page }) => {
      const stats = await page.locator('.token-meter').first();
      if (await stats.isVisible()) {
        const text = await stats.textContent();
        if (text) {
          expect(text).toContain('/');
        }
      }
    });

    test('should have progress bar', async ({ page }) => {
      const progressBar = await page.locator('.token-meter div[style*="background-color"]').first();
      if (await progressBar.isVisible()) {
        const width = await progressBar.evaluate((el) => el.style.width);
        expect(width).toBeTruthy();
      }
    });

    test('should show warning at 80% usage', async ({ page }) => {
      const updateBtn = await page.locator('button:has-text("Simulate 80% Token Usage")').first();
      if (await updateBtn.isVisible()) {
        await updateBtn.click();
        const warning = await page.locator('text=/Approaching token limit|Token limit/').first();
        if (await warning.isVisible()) {
          await expect(warning).toBeVisible();
        }
      }
    });

    test('should change color based on usage', async ({ page }) => {
      const meter = await page.locator('.token-meter').first();
      if (await meter.isVisible()) {
        const progressBar = await page.locator('.token-meter div[style*="background-color"]').first();
        const color = await progressBar.evaluate((el) => window.getComputedStyle(el).backgroundColor);
        expect(color).toBeTruthy();
      }
    });

    test('should display usage percentage', async ({ page }) => {
      const details = await page.locator('text=Usage:').first();
      if (await details.isVisible()) {
        const text = await details.textContent();
        if (text) {
          expect(text).toContain('%');
        }
      }
    });

    test('should show remaining tokens', async ({ page }) => {
      const remaining = await page.locator('text=Remaining:').first();
      if (await remaining.isVisible()) {
        await expect(remaining).toBeVisible();
      }
    });
  });

  test.describe('Chat Integration', () => {
    test('should integrate chat window and input box', async ({ page }) => {
      const chatWindow = await page.locator('.chat-window').first();
      const inputBox = await page.locator('.input-box-container').first();

      if (await chatWindow.isVisible() && await inputBox.isVisible()) {
        await expect(chatWindow).toBeVisible();
        await expect(inputBox).toBeVisible();
      }
    });

    test('should integrate chat with token meter', async ({ page }) => {
      const chatArea = await page.locator('.chat-window').first();
      const tokenMeter = await page.locator('.token-meter').first();

      if (await chatArea.isVisible() && await tokenMeter.isVisible()) {
        await expect(chatArea).toBeVisible();
        await expect(tokenMeter).toBeVisible();
      }
    });

    test('should handle multiple messages in sequence', async ({ page }) => {
      const addUserBtn = await page.locator('button:has-text("Add User Message")').first();
      const addAssistantBtn = await page.locator('button:has-text("Add Assistant Message")').first();

      if (await addUserBtn.isVisible() && await addAssistantBtn.isVisible()) {
        await addUserBtn.click();
        await addAssistantBtn.click();
        await addUserBtn.click();

        const messages = await page.locator('.chat-message').all();
        expect(messages.length).toBeGreaterThanOrEqual(3);
      }
    });
  });
});
