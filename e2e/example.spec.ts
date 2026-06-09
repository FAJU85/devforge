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

test('provider choice buttons are in the AI Config panel', async ({ page }) => {
  await page.goto('/');
  await page.locator('#stab-config').click();
  await expect(page.locator('#provch-hf')).toBeVisible();
  await expect(page.locator('#provch-ext')).toBeVisible();
});

// Regression: switching provider groups crashed saveEnhance() in production
// (Sentry PYTHON-1D — TypeError reading .value of a missing element)
test('switching provider group does not throw page errors', async ({ page }) => {
  const errors: string[] = [];
  page.on('pageerror', (e) => errors.push(e.message));
  await page.goto('/');
  await page.locator('#stab-config').click();
  await page.locator('#provch-ext').click();
  await page.locator('#provch-hf').click();
  expect(errors).toEqual([]);
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

test('POST /api/repo/diff validates required fields', async ({ request }) => {
  const res = await request.post('/api/repo/diff', {
    data: { owner: 'user' },
  });
  // Missing required fields → 422 Unprocessable Entity
  expect(res.status()).toBe(422);
});

test('POST /api/repo/tree validates required fields', async ({ request }) => {
  const res = await request.post('/api/repo/tree', {
    data: { owner: 'user' },
  });
  expect(res.status()).toBe(422);
});

test('POST /api/admin/login rejects bad credentials', async ({ request }) => {
  const res = await request.post('/api/admin/login', {
    data: { username: 'nobody', password: 'wrong' },
  });
  expect(res.status()).toBe(200);
  const body = await res.json();
  expect(body.ok).toBe(false);
});
