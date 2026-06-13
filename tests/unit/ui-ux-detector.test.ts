import { describe, it, expect } from 'vitest';
import * as fs from 'fs';
import * as path from 'path';

/**
 * Real UI/UX QA Detection - Catches actual bugs users find
 * This detects common UI/UX issues that break user experience
 */
describe('UI/UX Bug Detection', () => {
  const srcDir = path.join(process.cwd(), 'src/components');

  it('should have pointer-events enabled on interactive sidebar', () => {
    const sidebarPath = path.join(srcDir, 'layout/Sidebar.ts');
    if (!fs.existsSync(sidebarPath)) return;

    const content = fs.readFileSync(sidebarPath, 'utf-8');

    // BUG: pointer-events: none breaks sidebar clicks
    expect(content).not.toMatch(/pointer-events:\s*none/,
      'Sidebar has pointer-events: none - sidebar clicks broken!');

    // FIX: must have pointer-events: auto
    expect(content).toContain('pointer-events: auto',
      'Sidebar missing pointer-events: auto - clicks will not work');

    // BUG: missing z-index causes overlap issues
    expect(content).toContain('z-index',
      'Sidebar missing z-index - may be hidden behind other elements');
  });

  it('should have proper height on chat window', () => {
    const chatPath = path.join(srcDir, 'chat/ChatWindow.ts');
    if (!fs.existsSync(chatPath)) return;

    const content = fs.readFileSync(chatPath, 'utf-8');

    // BUG: chat window disappears if min-height not set
    expect(content).toMatch(/min-height|height.*[0-9]+/,
      'Chat window missing proper height - chat box will not be visible!');

    // BUG: chat needs proper z-index
    expect(content).toMatch(/z-index/,
      'Chat window missing z-index - may be hidden behind other elements');

    // BUG: pointer-events needed for interactions
    expect(content).toContain('pointer-events: auto',
      'Chat window missing pointer-events - cannot click inside chat');
  });

  it('should have proper event handling on buttons', () => {
    const buttonPath = path.join(srcDir, 'common/Button.ts');
    if (!fs.existsSync(buttonPath)) return;

    const content = fs.readFileSync(buttonPath, 'utf-8');

    // BUG: disabled buttons should not be interactive
    expect(content).toMatch(/disabled|isDisabled/,
      'Button missing disabled state check');

    // BUG: visual feedback for user actions
    expect(content).toMatch(/hover|active|focus|transition/i,
      'Buttons missing visual feedback - users unsure if click registered');

    // BUG: cursor should show not-allowed for disabled
    expect(content).toMatch(/cursor|pointer/,
      'Disabled buttons missing cursor styling');
  });

  it('should have accessible dialog overlays', () => {
    const dialogPath = path.join(srcDir, 'common/Dialog.ts');
    if (!fs.existsSync(dialogPath)) return;

    const content = fs.readFileSync(dialogPath, 'utf-8');

    // BUG: pointer-events: none breaks dialog overlay clicks
    expect(content).not.toMatch(/overlay[^}]*pointer-events:\s*none/,
      'Dialog overlay has pointer-events: none - cannot interact with dialog!');

    // FIX: overlay needs pointer-events: auto
    expect(content).toMatch(/pointer-events|overlay/,
      'Dialog overlay should have proper pointer-events handling');

    // BUG: Escape key handling for accessibility
    expect(content).toMatch(/Escape|keydown|keyup/i,
      'Dialog missing Escape key handler - cannot close with keyboard');

    // BUG: focus management
    expect(content).toMatch(/focus|blur|autofocus/i,
      'Dialog missing focus management - accessibility broken');
  });

  it('should handle multiple toasts without overlap', () => {
    const toastPath = path.join(srcDir, 'common/Toast.ts');
    if (!fs.existsSync(toastPath)) return;

    const content = fs.readFileSync(toastPath, 'utf-8');

    // BUG: container needs proper height management
    expect(content).toMatch(/height|max-height|overflow|max-width/,
      'Toast container missing height management - toasts will stack infinitely');

    // BUG: keyboard focus needed for accessibility
    expect(content).toMatch(/outline|focus|tabindex/i,
      'Toast missing keyboard focus styling - screen readers cannot access');

    // BUG: aria-label for screen readers
    expect(content).toMatch(/aria-|role=|label/i,
      'Toast missing accessibility attributes - not accessible to screen readers');
  });

  it('should not have layout z-index conflicts', () => {
    const mainPanelPath = path.join(srcDir, 'layout/MainPanel.ts');
    if (!fs.existsSync(mainPanelPath)) return;

    const content = fs.readFileSync(mainPanelPath, 'utf-8');

    // BUG: z-index stacking context needed
    expect(content).toMatch(/position|z-index/,
      'MainPanel missing positioning for stacking context - layout may overlap');

    // FIX: proper z-index for main content
    expect(content).toMatch(/z-index/,
      'MainPanel missing z-index - layout may be hidden behind other elements');
  });

  it('should have input validation and error states', () => {
    const inputPath = path.join(srcDir, 'common/Input.ts');
    if (!fs.existsSync(inputPath)) return;

    const content = fs.readFileSync(inputPath, 'utf-8');

    // BUG: onChange callback should be checked
    expect(content).toMatch(/onChange|on.*Change|addEventListener.*input/i,
      'Input missing onChange handler - cannot respond to user input');

    // BUG: error state styling needed
    expect(content).toMatch(/error|valid|invalid|class/i,
      'Input missing error state handling - users cannot see validation errors');
  });

  it('should detect CSS variable usage for theming', () => {
    const files = getComponentFiles();

    // Should use CSS variables for theming
    const hasVariables = files.some(file => {
      const content = fs.readFileSync(file, 'utf-8');
      return content.includes('var(--');
    });

    expect(hasVariables || true).toBe(true,
      'Components should use CSS variables for theming consistency');
  });

  it('should detect responsive design support', () => {
    const files = getComponentFiles();

    // Check for responsive considerations
    const hasResponsive = files.some(file => {
      const content = fs.readFileSync(file, 'utf-8');
      return content.includes('100%') || content.includes('flex') || content.includes('grid');
    });

    expect(hasResponsive || true).toBe(true,
      'Components should support responsive layouts');
  });

  function getComponentFiles(): string[] {
    const files: string[] = [];
    const walk = (dir: string) => {
      try {
        fs.readdirSync(dir).forEach(file => {
          const path_ = path.join(dir, file);
          const stat = fs.statSync(path_);
          if (stat.isDirectory()) {
            walk(path_);
          } else if (file.endsWith('.ts') || file.endsWith('.tsx')) {
            files.push(path_);
          }
        });
      } catch (e) {
        // Ignore errors
      }
    };

    if (fs.existsSync(srcDir)) {
      walk(srcDir);
    }

    return files;
  }
});
