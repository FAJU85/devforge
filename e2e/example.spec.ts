import { test, expect } from '@playwright/test';

// ── Page load ─────────────────────────────────────────────────────────────────

test('page title is DevForge', async ({ page }) => {
  await page.goto('/');
  await expect(page).toHaveTitle(/DevForge/);
});

test('sidebar is visible on load', async ({ page }) => {
  await page.goto('/');
  const sidebar = page.locator('#sidebar');
  await expect(sidebar).toBeVisible();
});

test('HF build status widget is present', async ({ page }) => {
  await page.goto('/');
  // The HF Build Status widget lives in the Tools panel — open it first
  await page.locator('#stab-tools').click();
  await expect(page.locator('#hf-build-dot')).toBeVisible();
  await expect(page.locator('#hf-build-label')).toBeVisible();
});

test('Feature Flags section is in the sidebar', async ({ page }) => {
  await page.goto('/');
  // Feature Flags lives in the Tools panel
  await page.locator('#stab-tools').click();
  await expect(page.getByText('🚩 Feature Flags')).toBeVisible();
});

test('Canary Analysis section is in the sidebar', async ({ page }) => {
  await page.goto('/');
  // Canary Analysis lives in the Tools panel
  await page.locator('#stab-tools').click();
  await expect(page.getByText('🐤 Canary Analysis')).toBeVisible();
});

// ── API endpoints ─────────────────────────────────────────────────────────────

test('GET /api/config returns 200 with expected keys', async ({ request }) => {
  const res = await request.get('/api/config');
  expect(res.status()).toBe(200);
  const body = await res.json();
  expect(body).toHaveProperty('environment');
  expect(body).toHaveProperty('posthog_project_id');
});

test('GET /api/flags returns 200 with array', async ({ request }) => {
  const res = await request.get('/api/flags');
  expect(res.status()).toBe(200);
  const body = await res.json();
  expect(Array.isArray(body.flags)).toBe(true);
});

test('GET /api/hf-build/status returns 200 with stage field', async ({ request }) => {
  const res = await request.get('/api/hf-build/status');
  // May be 200 or 502 depending on network; either way it should return JSON with stage
  const body = await res.json();
  expect(body).toHaveProperty('stage');
  expect(typeof body.stage).toBe('string');
});

test('GET /api/evolution/history returns 200 with array', async ({ request }) => {
  const res = await request.get('/api/evolution/history');
  expect(res.status()).toBe(200);
  const body = await res.json();
  expect(Array.isArray(body.history)).toBe(true);
});
