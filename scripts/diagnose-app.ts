/**
 * Diagnostic script to inspect app DOM and functionality
 */

import { chromium, Browser, BrowserContext, Page } from '@playwright/test';

async function diagnoseApp(url: string): Promise<void> {
  console.log(`\n🔍 Diagnosing app at: ${url}\n`);

  const browser: Browser = await chromium.launch({ headless: true, args: ['--ignore-certificate-errors'] });
  const context: BrowserContext = await browser.newContext({
    viewport: { width: 1280, height: 800 },
  });

  const page: Page = await context.newPage();

  try {
    await page.goto(url, { waitUntil: 'networkidle', timeout: 30000 });

    // Wait for page to fully render
    await page.waitForTimeout(2000);

    // Get detailed DOM info
    const domInfo = await page.evaluate(() => {
      const app = document.getElementById('app');
      return {
        appExists: !!app,
        appChildren: app?.children.length || 0,
        appHTML: app?.innerHTML.substring(0, 500) || 'N/A',
        textareaCount: document.querySelectorAll('textarea').length,
        inputCount: document.querySelectorAll('input').length,
        buttonCount: document.querySelectorAll('button').length,
        inputBoxContainers: document.querySelectorAll('.input-box-container').length,
        chatWindowCount: document.querySelectorAll('.chat-window').length,
        messagesContainer: !!document.querySelector('.messages-container'),
        bodyHTML: document.body.innerHTML.substring(0, 300),
      };
    });

    console.log('📊 DOM Structure:');
    console.log(`  #app element: ${domInfo.appExists ? '✅ Exists' : '❌ Missing'}`);
    console.log(`  App children: ${domInfo.appChildren}`);
    console.log(`  Textareas: ${domInfo.textareaCount}`);
    console.log(`  Inputs: ${domInfo.inputCount}`);
    console.log(`  Buttons: ${domInfo.buttonCount}`);
    console.log(`  InputBox containers: ${domInfo.inputBoxContainers}`);
    console.log(`  Chat windows: ${domInfo.chatWindowCount}`);
    console.log(`  Messages container: ${domInfo.messagesContainer ? '✅ Found' : '❌ Not found'}`);

    // Check for errors
    const errorLogs: string[] = [];
    page.on('console', (msg) => {
      if (msg.type() === 'error') {
        errorLogs.push(msg.text());
      }
    });

    // Wait a bit and capture any errors
    await page.waitForTimeout(1000);

    if (errorLogs.length > 0) {
      console.log('\n⚠️  JavaScript Errors:');
      errorLogs.forEach(err => console.log(`  - ${err}`));
    } else {
      console.log('\n✅ No JavaScript errors detected');
    }

    // Try to find and inspect textarea
    const textareaInfo = await page.evaluate(() => {
      const textarea = document.querySelector('textarea');
      if (!textarea) return null;
      return {
        visible: textarea.offsetHeight > 0 && textarea.offsetWidth > 0,
        disabled: textarea.disabled,
        placeholder: textarea.placeholder,
        parent: textarea.parentElement?.className || 'unknown',
      };
    });

    if (textareaInfo) {
      console.log('\n📝 Textarea found:');
      console.log(`  Visible: ${textareaInfo.visible ? '✅' : '❌'}`);
      console.log(`  Disabled: ${textareaInfo.disabled ? '🔒' : '✅'}`);
      console.log(`  Placeholder: ${textareaInfo.placeholder}`);
      console.log(`  Parent class: ${textareaInfo.parent}`);
    } else {
      console.log('\n❌ No textarea found in DOM');
    }

    // Try to take a screenshot showing the app
    await page.screenshot({ path: '/tmp/diagnostic-screenshot.png' });
    console.log('\n📸 Screenshot saved to /tmp/diagnostic-screenshot.png');

  } catch (error) {
    console.error('Diagnostic failed:', error);
  } finally {
    await context.close();
    await browser.close();
  }
}

const url = process.argv[2] || 'http://localhost:5173/';
diagnoseApp(url).catch(err => {
  console.error('Error:', err.message);
  process.exit(1);
});
