/**
 * Test HF Space functionality
 */

import { chromium, Browser, BrowserContext, Page } from '@playwright/test';

async function testHFSpace(url: string): Promise<void> {
  console.log(`\n🧪 Testing HF Space: ${url}`);

  const browser: Browser = await chromium.launch({ headless: true, args: ['--ignore-certificate-errors'] });
  const context: BrowserContext = await browser.newContext({
    viewport: { width: 1280, height: 800 },
  });

  const page: Page = await context.newPage();

  try {
    console.log('\n📡 Loading page...');
    await page.goto(url, { waitUntil: 'networkidle', timeout: 30000 });

    // Check if JavaScript is running by looking for specific DOM elements or classes
    console.log('\n🔍 Checking DOM structure...');

    // Check for sidebar
    const sidebarExists = await page.locator('.sidebar-section').count();
    console.log(`  Sidebar section: ${sidebarExists > 0 ? '✅ Found' : '❌ Not found'}`);

    // Check for main content area
    const mainSectionExists = await page.locator('.main-section').count();
    console.log(`  Main section: ${mainSectionExists > 0 ? '✅ Found' : '❌ Not found'}`);

    // Try to find interactive elements
    const buttons = await page.locator('button').count();
    const inputs = await page.locator('input').count();
    console.log(`  Buttons found: ${buttons}`);
    console.log(`  Inputs found: ${inputs}`);

    // Check for chat window
    const chatWindow = await page.locator('[role="main"]').count();
    console.log(`  Chat window (role=main): ${chatWindow > 0 ? '✅ Found' : '❌ Not found'}`);

    // Try to click a button to see if JavaScript event handlers work
    const clickableButtons = await page.locator('button:visible').count();
    if (clickableButtons > 0) {
      console.log(`\n💬 Testing interactivity...`);
      const firstButton = page.locator('button:visible').first();
      const buttonText = await firstButton.textContent();
      console.log(`  First button: "${buttonText}"`);

      try {
        await firstButton.click({ timeout: 2000 });
        console.log('  ✅ Button click successful');
      } catch (e) {
        console.log(`  ❌ Button click failed: ${e}`);
      }
    }

    // Check for console errors
    const consoleMessages: string[] = [];
    page.on('console', (msg) => {
      const text = `[${msg.type().toUpperCase()}] ${msg.text()}`;
      consoleMessages.push(text);
      if (msg.type() === 'error') {
        console.log(`  ⚠️  Console Error: ${text}`);
      }
    });

    // Wait a bit for any console messages
    await page.waitForTimeout(1000);

    // Check JavaScript execution
    const jsResult = await page.evaluate(() => {
      return {
        hasAppElement: document.getElementById('app') ? true : false,
        appHTML: document.getElementById('app')?.innerHTML.substring(0, 200) || 'Not found',
        sidebarClass: document.querySelector('.sidebar-section') ? 'Found' : 'Not found',
        mainClass: document.querySelector('.main-section') ? 'Found' : 'Not found',
      };
    });

    console.log('\n📊 JavaScript Evaluation Results:');
    console.log(`  #app element: ${jsResult.hasAppElement ? '✅ Found' : '❌ Not found'}`);
    console.log(`  App innerHTML length: ${jsResult.appHTML.length}`);
    console.log(`  Sidebar class: ${jsResult.sidebarClass}`);
    console.log(`  Main class: ${jsResult.mainClass}`);

  } catch (error) {
    console.error('Test failed:', error);
  } finally {
    await context.close();
    await browser.close();
  }
}

const url = process.argv[2] || 'https://vooom-devforge.hf.space/';
testHFSpace(url).catch(err => {
  console.error('Error:', err.message);
  process.exit(1);
});
