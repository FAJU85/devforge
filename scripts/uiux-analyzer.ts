/**
 * UI/UX Screen Recorder & Bug Analyzer
 * Records a website session with Playwright, captures screenshots at key moments,
 * then uses Claude vision to detect UI/UX issues.
 *
 * Usage:
 *   npx tsx scripts/uiux-analyzer.ts <url> [--headless]
 *   npx tsx scripts/uiux-analyzer.ts https://vooom-devforge.hf.space/
 */

import { chromium, Browser, BrowserContext, Page } from '@playwright/test';
import Anthropic from '@anthropic-ai/sdk';
import * as fs from 'fs';
import * as path from 'path';

const OUTPUT_DIR = path.join(process.cwd(), 'uiux-reports');
const VIDEO_DIR = path.join(OUTPUT_DIR, 'videos');
const SCREENSHOT_DIR = path.join(OUTPUT_DIR, 'screenshots');

interface ScreenshotCapture {
  label: string;
  path: string;
  base64: string;
}

interface UiuxFinding {
  severity: 'critical' | 'major' | 'minor' | 'info';
  category: string;
  description: string;
  screenshot?: string;
}

interface AnalysisReport {
  url: string;
  timestamp: string;
  videoPath?: string;
  screenshots: string[];
  findings: UiuxFinding[];
  summary: string;
  consoleLogs?: string[];
  networkErrors?: string[];
  pageContent?: string;
}

async function captureScreenshot(page: Page, label: string, dir: string): Promise<ScreenshotCapture> {
  const filename = `${label.replace(/\s+/g, '-').toLowerCase()}-${Date.now()}.png`;
  const filepath = path.join(dir, filename);
  await page.screenshot({ path: filepath, fullPage: false });
  const base64 = fs.readFileSync(filepath).toString('base64');
  console.log(`  📸 Captured: ${label}`);
  return { label, path: filepath, base64 };
}

async function analyzeWithClaude(
  screenshots: ScreenshotCapture[],
  url: string
): Promise<{ findings: UiuxFinding[]; summary: string }> {
  const apiKey = process.env.ANTHROPIC_API_KEY;
  if (!apiKey) {
    console.warn('⚠️  ANTHROPIC_API_KEY not set — skipping AI analysis');
    return {
      findings: [{ severity: 'info', category: 'Setup', description: 'Set ANTHROPIC_API_KEY to enable AI analysis' }],
      summary: 'AI analysis skipped — no API key',
    };
  }

  const client = new Anthropic({ apiKey });

  const imageContent: Anthropic.ImageBlockParam[] = screenshots.map((s) => ({
    type: 'image',
    source: {
      type: 'base64',
      media_type: 'image/png',
      data: s.base64,
    },
  }));

  const labelList = screenshots.map((s, i) => `Image ${i + 1}: "${s.label}"`).join('\n');

  console.log(`  🤖 Sending ${screenshots.length} screenshots to Claude for analysis...`);

  const response = await client.messages.create({
    model: 'claude-sonnet-4-6',
    max_tokens: 2048,
    messages: [
      {
        role: 'user',
        content: [
          ...imageContent,
          {
            type: 'text',
            text: `You are a senior UX engineer performing a UI/UX audit of this website: ${url}

The screenshots are:
${labelList}

Analyze all screenshots and identify UI/UX bugs and issues. For each finding, provide:
- severity: "critical" | "major" | "minor" | "info"
- category: one of: Layout, Typography, Color/Contrast, Accessibility, Responsiveness, Navigation, Loading, Interaction, Content, Performance
- description: concise description of the issue and which screenshot it appears in

Respond ONLY with valid JSON in this exact format:
{
  "findings": [
    { "severity": "...", "category": "...", "description": "..." }
  ],
  "summary": "2-3 sentence overall assessment"
}`,
          },
        ],
      },
    ],
  });

  const text = response.content[0].type === 'text' ? response.content[0].text : '';

  try {
    const jsonMatch = text.match(/\{[\s\S]*\}/);
    if (!jsonMatch) throw new Error('No JSON found in response');
    return JSON.parse(jsonMatch[0]);
  } catch {
    return {
      findings: [{ severity: 'info', category: 'Analysis', description: text }],
      summary: 'Analysis completed',
    };
  }
}

async function recordAndAnalyze(url: string, headless = true): Promise<AnalysisReport> {
  fs.mkdirSync(VIDEO_DIR, { recursive: true });
  fs.mkdirSync(SCREENSHOT_DIR, { recursive: true });

  const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
  const sessionDir = path.join(SCREENSHOT_DIR, timestamp);
  fs.mkdirSync(sessionDir, { recursive: true });

  console.log(`\n🎬 Recording UI/UX session for: ${url}`);
  console.log(`   Mode: ${headless ? 'headless' : 'headed'}`);

  const browser: Browser = await chromium.launch({ headless, args: ['--ignore-certificate-errors'] });
  const context: BrowserContext = await browser.newContext({
    viewport: { width: 1280, height: 800 },
    recordVideo: { dir: VIDEO_DIR, size: { width: 1280, height: 800 } },
  });

  const page: Page = await context.newPage();

  const consoleLogs: string[] = [];
  const networkErrors: string[] = [];
  let pageBodyText = '';

  page.on('console', (msg) => {
    const text = `[${msg.type().toUpperCase()}] ${msg.text()}`;
    consoleLogs.push(text);
    console.log(`  💬 Console: ${text}`);
  });

  page.on('requestfailed', (request) => {
    const error = `Failed: ${request.method()} ${request.url()}`;
    networkErrors.push(error);
    console.log(`  ⚠️  Network: ${error}`);
  });

  const captures: ScreenshotCapture[] = [];

  try {
    // 1. Initial page load
    console.log('\n📡 Loading page...');
    await page.goto(url, { waitUntil: 'networkidle', timeout: 30000 });

    // Check page content
    pageBodyText = await page.evaluate(() => document.body.innerText);
    if (!pageBodyText || pageBodyText.trim().length === 0) {
      console.log('  ⚠️  Page body is empty');
    } else {
      console.log(`  ✓ Page body has content (${pageBodyText.length} chars)`);
    }

    captures.push(await captureScreenshot(page, 'initial-load', sessionDir));

    // 2. Wait for animations to settle
    await page.waitForTimeout(1500);
    captures.push(await captureScreenshot(page, 'settled-state', sessionDir));

    // 3. Scroll to 25%
    await page.evaluate(() => window.scrollTo(0, document.body.scrollHeight * 0.25));
    await page.waitForTimeout(500);
    captures.push(await captureScreenshot(page, 'scroll-25pct', sessionDir));

    // 4. Scroll to 50%
    await page.evaluate(() => window.scrollTo(0, document.body.scrollHeight * 0.5));
    await page.waitForTimeout(500);
    captures.push(await captureScreenshot(page, 'scroll-50pct', sessionDir));

    // 5. Scroll to bottom
    await page.evaluate(() => window.scrollTo(0, document.body.scrollHeight));
    await page.waitForTimeout(500);
    captures.push(await captureScreenshot(page, 'scroll-bottom', sessionDir));

    // 6. Back to top
    await page.evaluate(() => window.scrollTo(0, 0));
    await page.waitForTimeout(300);

    // 7. Hover over interactive elements
    const buttons = await page.locator('button, [role="button"], a[href]').all();
    if (buttons.length > 0) {
      try {
        await buttons[0].hover({ timeout: 2000 });
        await page.waitForTimeout(300);
        captures.push(await captureScreenshot(page, 'hover-first-interactive', sessionDir));
      } catch { /* element may not be hoverable */ }
    }

    // 8. Check for inputs
    const inputs = await page.locator('input, textarea').all();
    if (inputs.length > 0) {
      try {
        await inputs[0].click({ timeout: 2000 });
        await page.waitForTimeout(300);
        captures.push(await captureScreenshot(page, 'input-focused', sessionDir));
      } catch { /* input may not be focusable */ }
    }

    // 9. Mobile viewport check
    await page.setViewportSize({ width: 375, height: 812 });
    await page.waitForTimeout(500);
    captures.push(await captureScreenshot(page, 'mobile-375px', sessionDir));

    // 10. Tablet viewport
    await page.setViewportSize({ width: 768, height: 1024 });
    await page.waitForTimeout(500);
    captures.push(await captureScreenshot(page, 'tablet-768px', sessionDir));

    // Restore desktop
    await page.setViewportSize({ width: 1280, height: 800 });
    await page.waitForTimeout(300);
    captures.push(await captureScreenshot(page, 'desktop-restored', sessionDir));

  } finally {
    await context.close();
    await browser.close();
  }

  // Get video path
  const videoFiles = fs.readdirSync(VIDEO_DIR)
    .filter(f => f.endsWith('.webm'))
    .map(f => ({ f, t: fs.statSync(path.join(VIDEO_DIR, f)).mtime.getTime() }))
    .sort((a, b) => b.t - a.t);
  const videoPath = videoFiles.length > 0 ? path.join(VIDEO_DIR, videoFiles[0].f) : undefined;
  if (videoPath) console.log(`\n🎥 Video saved: ${videoPath}`);

  // AI analysis
  console.log('\n🔍 Analyzing screenshots with Claude...');
  const { findings, summary } = await analyzeWithClaude(captures, url);

  const report: AnalysisReport = {
    url,
    timestamp,
    videoPath,
    screenshots: captures.map(c => c.path),
    findings,
    summary,
    consoleLogs,
    networkErrors: networkErrors.length > 0 ? networkErrors : undefined,
    pageContent: pageBodyText && pageBodyText.length > 0 ? 'Page has content' : 'Page is empty',
  };

  // Save report
  const reportPath = path.join(OUTPUT_DIR, `report-${timestamp}.json`);
  fs.writeFileSync(reportPath, JSON.stringify(report, null, 2));

  // Print results
  console.log('\n' + '='.repeat(60));
  console.log('UI/UX ANALYSIS REPORT');
  console.log('='.repeat(60));
  console.log(`URL: ${url}`);
  console.log(`Screenshots: ${captures.length}`);
  console.log(`\nSUMMARY:\n${summary}`);
  console.log('\nFINDINGS:');

  const bySeverity = { critical: 0, major: 0, minor: 0, info: 0 };
  for (const f of findings) {
    bySeverity[f.severity]++;
    const icon = { critical: '🔴', major: '🟠', minor: '🟡', info: '🔵' }[f.severity];
    console.log(`  ${icon} [${f.severity.toUpperCase()}] ${f.category}: ${f.description}`);
  }

  console.log(`\nTOTALS: 🔴${bySeverity.critical} critical  🟠${bySeverity.major} major  🟡${bySeverity.minor} minor  🔵${bySeverity.info} info`);
  console.log(`\nReport saved: ${reportPath}`);
  console.log('='.repeat(60));

  return report;
}

// CLI entry point
const url = process.argv[2];
if (!url) {
  console.error('Usage: npx tsx scripts/uiux-analyzer.ts <url> [--headed]');
  console.error('Example: npx tsx scripts/uiux-analyzer.ts https://vooom-devforge.hf.space/');
  process.exit(1);
}

const headed = process.argv.includes('--headed');
recordAndAnalyze(url, !headed).catch(err => {
  console.error('Error:', err.message);
  process.exit(1);
});
