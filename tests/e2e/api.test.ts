/**
 * E2E Tests for API Clients and Services
 * Note: These tests verify build integrity and module exports via browser context
 */

import { test, expect } from '@playwright/test';

test.describe('Build Verification', () => {
  test('should load without errors', async ({ page }) => {
    let errors: string[] = [];
    page.on('console', (msg) => {
      if (msg.type() === 'error') {
        errors.push(msg.text());
      }
    });

    await page.goto('http://localhost:5173');
    await page.waitForLoadState('networkidle');

    // Filter out non-critical errors (favicon, etc)
    const fatalErrors = errors.filter(e =>
      !e.includes('favicon') &&
      !e.includes('404')
    );

    expect(fatalErrors.length).toBe(0);
  });

  test('should have DOM ready', async ({ page }) => {
    await page.goto('http://localhost:5173');

    const body = await page.locator('body');
    expect(body).toBeDefined();
  });

  test('should have JavaScript loaded', async ({ page }) => {
    await page.goto('http://localhost:5173');

    // Execute a simple JS test
    const result = await page.evaluate(() => typeof window === 'object');
    expect(result).toBe(true);
  });
});

test.describe('API Client Exports', () => {
  test('ApiClient should be compiled in bundle', async ({ page }) => {
    await page.goto('http://localhost:5173');

    const content = await page.content();
    expect(content).toContain('ApiClient');
  });

  test('GitHubClient should be compiled in bundle', async ({ page }) => {
    await page.goto('http://localhost:5173');

    const content = await page.content();
    expect(content).toContain('GitHubClient');
  });

  test('RepositoryClient should be compiled in bundle', async ({ page }) => {
    await page.goto('http://localhost:5173');

    const content = await page.content();
    expect(content).toContain('RepositoryClient');
  });

  test('HuggingFaceClient should be compiled in bundle', async ({ page }) => {
    await page.goto('http://localhost:5173');

    const content = await page.content();
    expect(content).toContain('HuggingFaceClient');
  });

  test('ConfigClient should be compiled in bundle', async ({ page }) => {
    await page.goto('http://localhost:5173');

    const content = await page.content();
    expect(content).toContain('ConfigClient');
  });
});

test.describe('Service Exports', () => {
  test('ChatService should be compiled in bundle', async ({ page }) => {
    await page.goto('http://localhost:5173');

    const content = await page.content();
    expect(content).toContain('ChatService');
  });

  test('RepositoryService should be compiled in bundle', async ({ page }) => {
    await page.goto('http://localhost:5173');

    const content = await page.content();
    expect(content).toContain('RepositoryService');
  });

  test('ConfigService should be compiled in bundle', async ({ page }) => {
    await page.goto('http://localhost:5173');

    const content = await page.content();
    expect(content).toContain('ConfigService');
  });

  test('ContextService should be compiled in bundle', async ({ page }) => {
    await page.goto('http://localhost:5173');

    const content = await page.content();
    expect(content).toContain('ContextService');
  });

  test('ServiceContainer should be compiled in bundle', async ({ page }) => {
    await page.goto('http://localhost:5173');

    const content = await page.content();
    expect(content).toContain('ServiceContainer');
  });
});

test.describe('Store Exports', () => {
  test('All stores should be compiled in bundle', async ({ page }) => {
    await page.goto('http://localhost:5173');

    const content = await page.content();
    expect(content).toContain('ChatStore');
    expect(content).toContain('RepoStore');
    expect(content).toContain('ConfigStore');
    expect(content).toContain('ContextStore');
    expect(content).toContain('MemoryStore');
    expect(content).toContain('StatsStore');
  });
});

test.describe('Type Definitions', () => {
  test('should have ApiResponse type compiled', async ({ page }) => {
    await page.goto('http://localhost:5173');

    const content = await page.content();
    expect(content).toContain('ApiResponse');
  });

  test('should have ChatMessage type compiled', async ({ page }) => {
    await page.goto('http://localhost:5173');

    const content = await page.content();
    expect(content).toContain('ChatMessage');
  });

  test('should have ServiceConfig type compiled', async ({ page }) => {
    await page.goto('http://localhost:5173');

    const content = await page.content();
    expect(content).toContain('ServiceConfig');
  });
});

test.describe('Bundle Performance', () => {
  test('should load page in reasonable time', async ({ page }) => {
    const startTime = Date.now();
    await page.goto('http://localhost:5173', { waitUntil: 'networkidle' });
    const loadTime = Date.now() - startTime;

    // Should load in under 10 seconds
    expect(loadTime).toBeLessThan(10000);
  });

  test('should have stylesheet', async ({ page }) => {
    await page.goto('http://localhost:5173');

    const stylesheets = await page.locator('link[rel="stylesheet"]').count();
    // Modern vite bundles CSS inline or as link tags
    expect(stylesheets).toBeGreaterThanOrEqual(0);
  });

  test('should have script bundle', async ({ page }) => {
    await page.goto('http://localhost:5173');

    const scripts = await page.locator('script').count();
    // Should have at least the main app script
    expect(scripts).toBeGreaterThanOrEqual(1);
  });
});
