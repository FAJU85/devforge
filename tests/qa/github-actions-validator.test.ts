import { describe, it, expect } from 'vitest';
import * as fs from 'fs';
import * as path from 'path';

describe('GitHub Actions Validation', () => {
  const workflowDir = path.join(process.cwd(), '.github/workflows');
  const workflowFiles = fs.readdirSync(workflowDir).filter(f => f.endsWith('.yml'));

  it('should have Node.js 24 opt-in for deprecated actions', () => {
    workflowFiles.forEach(file => {
      const content = fs.readFileSync(path.join(workflowDir, file), 'utf-8');

      // If workflow uses checkout@v4 or setup-python@v5, must have Node.js 24 opt-in
      const hasDeprecatedActions = content.includes('actions/checkout@v4') ||
                                   content.includes('actions/setup-python@v5');

      if (hasDeprecatedActions) {
        expect(content).toMatch(/FORCE_JAVASCRIPT_ACTIONS_TO_NODE24:\s*true/,
          `${file} uses deprecated actions but doesn't opt into Node.js 24`);
      }
    });
  });

  it('should not use deprecated action versions', () => {
    workflowFiles.forEach(file => {
      const content = fs.readFileSync(path.join(workflowDir, file), 'utf-8');

      // Check for outdated action versions
      expect(content).not.toMatch(/actions\/checkout@v[0-3]\b/,
        `${file} uses outdated actions/checkout version`);
      expect(content).not.toMatch(/actions\/setup-node@v[0-3]\b/,
        `${file} uses outdated actions/setup-node version`);
      expect(content).not.toMatch(/actions\/setup-python@v[0-4]\b/,
        `${file} uses outdated actions/setup-python version`);
    });
  });

  it('should have proper error handling in test gates', () => {
    const syncToHf = fs.readFileSync(path.join(workflowDir, 'sync-to-hf.yml'), 'utf-8');

    // Test gate should have coverage requirement
    expect(syncToHf).toContain('gate:');
    expect(syncToHf).toContain('pytest');
  });

  it('should have frontend build in CI', () => {
    const ci = fs.readFileSync(path.join(workflowDir, 'ci.yml'), 'utf-8');

    // Should build frontend
    expect(ci).toContain('test-frontend');
    expect(ci).toContain('npm run build');
    expect(ci).toContain('npm run test:unit:run');
  });

  it('should have Playwright E2E tests setup correctly', () => {
    const playwright = fs.readFileSync(path.join(workflowDir, 'playwright.yml'), 'utf-8');

    // Should build before testing
    expect(playwright).toContain('npm run build');
    expect(playwright).toContain('npx playwright install');
    expect(playwright).toContain('npx playwright test');
  });

  it('should upload test artifacts for debugging', () => {
    const playwright = fs.readFileSync(path.join(workflowDir, 'playwright.yml'), 'utf-8');

    // Should save playwright report
    expect(playwright).toContain('playwright-report');
    expect(playwright).toContain('upload-artifact');
  });

  it('should handle HF Space build failures gracefully', () => {
    const syncToHf = fs.readFileSync(path.join(workflowDir, 'sync-to-hf.yml'), 'utf-8');

    // Should have rollback capability
    expect(syncToHf).toContain('Rollback');
  });
});
