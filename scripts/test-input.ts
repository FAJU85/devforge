/**
 * Test if the textarea is actually usable
 */

import { chromium, Browser, BrowserContext, Page } from '@playwright/test';

async function testInput(url: string): Promise<void> {
  console.log(`\n✍️  Testing textarea interaction at: ${url}\n`);

  const browser: Browser = await chromium.launch({ headless: true, args: ['--ignore-certificate-errors'] });
  const context: BrowserContext = await browser.newContext({
    viewport: { width: 1280, height: 800 },
  });

  const page: Page = await context.newPage();

  try {
    await page.goto(url, { waitUntil: 'networkidle', timeout: 30000 });
    await page.waitForTimeout(2000);

    // Find the textarea
    const textarea = page.locator('textarea');
    const textareaCount = await textarea.count();

    if (textareaCount === 0) {
      console.log('❌ No textarea found');
      return;
    }

    console.log(`✅ Found ${textareaCount} textarea(s)`);

    // Try to focus the textarea
    try {
      await textarea.first().focus();
      console.log('✅ Textarea focused successfully');
    } catch (e) {
      console.log(`❌ Failed to focus: ${e}`);
      return;
    }

    // Try to type in the textarea
    try {
      await textarea.first().fill('Hello world! Testing the input box.');
      console.log('✅ Successfully typed in textarea');

      // Check the value
      const value = await textarea.first().inputValue();
      console.log(`   Text entered: "${value}"`);
    } catch (e) {
      console.log(`❌ Failed to type: ${e}`);
    }

    // Try to click the Send button
    try {
      const sendButton = page.locator('button:has-text("Send")');
      if (await sendButton.count() > 0) {
        await sendButton.click();
        console.log('✅ Send button clicked');
      } else {
        console.log('⚠️  Send button not found');
      }
    } catch (e) {
      console.log(`❌ Failed to click Send: ${e}`);
    }

    // Take a screenshot after interaction
    await page.screenshot({ path: '/tmp/interaction-screenshot.png' });
    console.log('\n📸 Screenshot saved after interaction');

  } catch (error) {
    console.error('Test failed:', error);
  } finally {
    await context.close();
    await browser.close();
  }
}

const url = process.argv[2] || 'http://localhost:5173/';
testInput(url).catch(err => {
  console.error('Error:', err.message);
  process.exit(1);
});
