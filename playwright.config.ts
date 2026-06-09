import { defineConfig, devices } from '@playwright/test';

export default defineConfig({
  testDir: './e2e',
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  workers: process.env.CI ? 1 : undefined,
  reporter: 'html',

  use: {
    baseURL: 'http://localhost:8000',
    trace: 'on-first-retry',
  },

  projects: [
    {
      name: 'chromium',
      use: {
        ...devices['Desktop Chrome'],
        // Sandboxes that can't reach cdn.playwright.dev can point this at any
        // system Chromium (e.g. a Sparticuz/chromium build from GitHub releases)
        ...(process.env.CHROME_EXECUTABLE
          ? { launchOptions: { executablePath: process.env.CHROME_EXECUTABLE, args: ['--no-sandbox', '--disable-gpu'] } }
          : {}),
      },
    },
  ],

  webServer: {
    command: 'uvicorn main:app --host 0.0.0.0 --port 8000',
    url: 'http://localhost:8000',
    reuseExistingServer: !process.env.CI,
    stdout: 'ignore',
    stderr: 'pipe',
    timeout: 30_000,
  },
});
