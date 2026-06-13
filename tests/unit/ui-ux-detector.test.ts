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
    const content = fs.readFileSync(sidebarPath, 'utf-8');

    // BUG: pointer-events: none breaks sidebar clicks
    expect(content).not.toMatch(/pointer-events:\s*none/,
      'Sidebar has pointer-events: none - sidebar clicks broken!');

    // FIX: must have pointer-events: auto
    expect(content).toContain('pointer-events: auto',
      'Sidebar missing pointer-events: auto - clicks will not work');

    // BUG: missing z-index causes overlap issues
    expect(content).toContain('z-index: 100',
      'Sidebar missing z-index: 100 - may be hidden behind other elements');
  });

  it('should have proper height on chat window', () => {
    const chatPath = path.join(srcDir, 'chat/ChatWindow.ts');
    const content = fs.readFileSync(chatPath, 'utf-8');

    // BUG: chat window disappears if min-height not set
    expect(content).toContain('min-height: 400px',
      'Chat window missing min-height - chat box will not be visible!');

    // BUG: chat needs proper z-index
    expect(content).toMatch(/z-index:\s*[1-9]/,
      'Chat window missing z-index - may be hidden behind other elements');

    // BUG: pointer-events needed for interactions
    expect(content).toContain('pointer-events: auto',
      'Chat window missing pointer-events - cannot click inside chat');
  });

  it('should have proper event handling on buttons', () => {
    const buttonPath = path.join(srcDir, 'common/Button.ts');
    const content = fs.readFileSync(buttonPath, 'utf-8');

    // BUG: disabled buttons should not be interactive
    expect(content).toContain('disabled',
      'Button missing disabled state check');

    // BUG: opacity for disabled state visibility
    expect(content).toMatch(/opacity.*0\.5|0\.5.*opacity/,
      'Disabled buttons missing visual indication (opacity)');

    // BUG: cursor should show not-allowed
    expect(content).toContain('not-allowed',
      'Disabled buttons missing cursor: not-allowed');

    // BUG: hover should skip disabled buttons
    expect(content).toMatch(/!.*disabled|button\.disabled/,
      'Button hover effects checking disabled state');
  });

  it('should have accessible dialog overlays', () => {
    const dialogPath = path.join(srcDir, 'common/Dialog.ts');
    const content = fs.readFileSync(dialogPath, 'utf-8');

    // BUG: pointer-events: none breaks dialog overlay clicks
    expect(content).not.toMatch(/overlay[^}]*pointer-events:\s*none/,
      'Dialog overlay has pointer-events: none - cannot interact with dialog!');

    // FIX: overlay needs pointer-events: auto
    expect(content).toContain('pointer-events: auto',
      'Dialog overlay missing pointer-events: auto - clicks blocked');

    // BUG: Escape key handling for accessibility
    expect(content).toContain('Escape',
      'Dialog missing Escape key handler - cannot close with keyboard');

    // BUG: focus management
    expect(content).toContain('focus',
      'Dialog missing focus management - accessibility broken');
  });

  it('should handle multiple toasts without overlap', () => {
    const toastPath = path.join(srcDir, 'common/Toast.ts');
    const content = fs.readFileSync(toastPath, 'utf-8');

    // BUG: container needs max-height to prevent overflow
    expect(content).toMatch(/max-height|overflow/,
      'Toast container missing max-height/overflow - toasts will stack infinitely');

    // BUG: keyboard focus needed for accessibility
    expect(content).toMatch(/outline|focus/,
      'Toast missing keyboard focus styling - screen readers cannot access');

    // BUG: aria-label for screen readers
    expect(content).toMatch(/aria-label|role/,
      'Toast missing aria-label - not accessible to screen readers');
  });

  it('should not have layout z-index conflicts', () => {
    const mainPanelPath = path.join(srcDir, 'layout/MainPanel.ts');
    const content = fs.readFileSync(mainPanelPath, 'utf-8');

    // BUG: z-index stacking context needed
    expect(content).toContain('position: relative',
      'MainPanel missing position: relative - z-index will not work');

    // FIX: proper z-index for main content
    expect(content).toMatch(/z-index:\s*[0-9]/,
      'MainPanel missing z-index - layout may be hidden behind other elements');
  });

  it('should have input validation and error states', () => {
    const inputPath = path.join(srcDir, 'common/Input.ts');
    const content = fs.readFileSync(inputPath, 'utf-8');

    // BUG: onChange callback without guard crashes on null
    expect(content).toMatch(/if\s*\(.*onChange\)|onChange.*\?/,
      'Input onChange not guarded - will crash on null callback');

    // BUG: error state styling needed
    expect(content).toMatch(/error|--red|#ef4444|#dc2626|red/i,
      'Input missing error state styling - users cannot see validation errors');
  });

  it('should detect CSS variable usage for theming', () => {
    const sidebarPath = path.join(srcDir, 'layout/Sidebar.ts');
    const chatPath = path.join(srcDir, 'chat/ChatWindow.ts');

    const sidebarContent = fs.readFileSync(sidebarPath, 'utf-8');
    const chatContent = fs.readFileSync(chatPath, 'utf-8');

    // BUG: hardcoded colors instead of CSS variables
    expect(sidebarContent).toMatch(/var\(--/,
      'Sidebar using hardcoded colors instead of CSS variables - theming broken');

    expect(chatContent).toMatch(/var\(--/,
      'ChatWindow using hardcoded colors instead of CSS variables - theming broken');
  });

  it('should detect viewport and responsive issues', () => {
    const layoutFiles = [
      path.join(srcDir, 'layout/Sidebar.ts'),
      path.join(srcDir, 'layout/MainPanel.ts'),
    ];

    layoutFiles.forEach(file => {
      const content = fs.readFileSync(file, 'utf-8');

      // BUG: height: 100vh causes issues on mobile
      if (content.includes('height: 100vh')) {
        // This is ok only if viewport is properly managed
        expect(content).toMatch(/viewport|overflow|scroll/,
          `${path.basename(file)}: height: 100vh without viewport handling - scrolling broken`);
      }
    });
  });

  it('should detect performance issues in event handlers', () => {
    const sidebarPath = path.join(srcDir, 'layout/Sidebar.ts');
    const content = fs.readFileSync(sidebarPath, 'utf-8');

    // BUG: excessive DOM queries in event handlers
    if (content.includes('addEventListener')) {
      // Should use event delegation or memoization
      expect(content).toMatch(/querySelectorAll|Array\.from/,
        'Sidebar event handlers may use inefficient DOM queries');
    }
  });
});
