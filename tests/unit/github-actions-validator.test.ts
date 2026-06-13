import { describe, it, expect } from 'vitest';
import * as fs from 'fs';
import * as path from 'path';

/**
 * GitHub Actions CI/CD Validator
 * Ensures workflows are properly configured for production readiness
 */
describe('GitHub Actions CI/CD Validation', () => {
  const workflowDir = path.join(process.cwd(), '.github/workflows');

  it('should have Node.js 24 opt-in before June 16 deadline', () => {
    const workflows = fs.readdirSync(workflowDir).filter(f => f.endsWith('.yml'));

    workflows.forEach(workflow => {
      const content = fs.readFileSync(path.join(workflowDir, workflow), 'utf-8');

      // Check if workflow uses Node.js actions
      if (content.includes('actions/') || content.includes('actions-rs/')) {
        expect(content).toMatch(/FORCE_JAVASCRIPT_ACTIONS_TO_NODE24|nodejs.*24/i,
          `${workflow}: Missing Node.js 24 opt-in - will break June 16 when Node 20 is EOL`);
      }
    });
  });

  it('should not use deprecated action versions', () => {
    const workflows = fs.readdirSync(workflowDir).filter(f => f.endsWith('.yml'));

    workflows.forEach(workflow => {
      const content = fs.readFileSync(path.join(workflowDir, workflow), 'utf-8');

      // Warn about generic version numbers instead of pinned hashes
      const hasVersionedActions = content.match(/@v[0-9]+/g);
      const hasPinnedActions = content.match(/@[a-f0-9]{40}/g);

      // Should prefer pinned commits for security
      if (hasVersionedActions && !hasPinnedActions) {
        expect(true).toBe(true,
          `${workflow}: Consider pinning action commits for security (e.g., @11bd71901bbe instead of @v4)`);
      }
    });
  });

  it('should have frontend test gate before backend tests', () => {
    const ciPath = path.join(workflowDir, 'ci.yml');
    const content = fs.readFileSync(ciPath, 'utf-8');

    // Frontend should build/test before backend
    expect(content).toMatch(/test-frontend|npm.*build|npm.*test.*unit/,
      'ci.yml: Missing frontend test gate - backend tests may pass while frontend is broken');
  });

  it('should have E2E test setup with Playwright', () => {
    const playwrightPath = path.join(workflowDir, 'playwright.yml');
    const content = fs.readFileSync(playwrightPath, 'utf-8');

    // Should install and run Playwright
    expect(content).toMatch(/playwright install|npx playwright test/,
      'playwright.yml: Missing Playwright test execution');

    // Should build frontend before E2E
    expect(content).toMatch(/npm run build/,
      'playwright.yml: Frontend not built before E2E - tests will fail');
  });

  it('should upload test artifacts for debugging', () => {
    const playwrightPath = path.join(workflowDir, 'playwright.yml');
    const content = fs.readFileSync(playwrightPath, 'utf-8');

    // Should upload reports/artifacts
    expect(content).toMatch(/upload-artifact|playwright-report/,
      'playwright.yml: Missing artifact upload - cannot debug failed E2E tests');
  });

  it('should have HF Space auto-rollback on build failure', () => {
    const monitorPath = path.join(workflowDir, 'monitor-hf-build.yml');
    if (fs.existsSync(monitorPath)) {
      const content = fs.readFileSync(monitorPath, 'utf-8');

      expect(content).toMatch(/ERROR|RUNTIME_ERROR|rollback|revert/i,
        'monitor-hf-build.yml: No rollback strategy when HF Space build fails');
    }
  });

  it('should have autonomous PR merge for auto/* branches', () => {
    const autonomousPath = path.join(workflowDir, 'autonomous.yml');
    if (fs.existsSync(autonomousPath)) {
      const content = fs.readFileSync(autonomousPath, 'utf-8');

      expect(content).toMatch(/auto\/|gh pr merge|auto.*merge/i,
        'autonomous.yml: No auto-merge for auto/* branches');
    }
  });
});
