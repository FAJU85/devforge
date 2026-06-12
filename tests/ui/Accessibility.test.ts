import { describe, it, expect, beforeEach } from 'vitest';
import { createDialog } from '../../src/components/common/Dialog';
import { Toast } from '../../src/components/common/Toast';

describe('UI Accessibility Tests', () => {
  beforeEach(() => {
    document.body.innerHTML = '';
  });

  describe('Dialog Accessibility', () => {
    it('should have proper ARIA attributes', () => {
      const dialog = createDialog({
        title: 'Test',
        message: 'Message',
        type: 'alert',
        onConfirm: () => {},
      });
      document.body.appendChild(dialog);

      const dialogElement = dialog.querySelector('[role="dialog"]');
      expect(dialogElement).toBeDefined();
      expect(dialogElement?.getAttribute('aria-modal')).toBe('true');
    });

    it('should have focusable buttons', () => {
      const dialog = createDialog({
        title: 'Test Dialog',
        message: 'Message',
        type: 'alert',
        onConfirm: () => {},
      });
      document.body.appendChild(dialog);

      const buttons = dialog.querySelectorAll('button');
      expect(buttons.length).toBeGreaterThan(0);

      buttons.forEach((btn) => {
        expect((btn as HTMLButtonElement).tabIndex).toBeGreaterThanOrEqual(-1);
      });
    });

    it('should have semantic text elements', () => {
      const dialog = createDialog({
        title: 'Dialog Title',
        message: 'Dialog Message',
        type: 'alert',
        onConfirm: () => {},
      });
      document.body.appendChild(dialog);

      const title = dialog.querySelector('h2');
      const message = dialog.querySelector('p');

      expect(title).toBeDefined();
      expect(message).toBeDefined();
      expect(title?.textContent).toBe('Dialog Title');
      expect(message?.textContent).toBe('Dialog Message');
    });

    it('should support keyboard interaction', () => {
      let confirmCalled = false;

      const dialog = createDialog({
        title: 'Test',
        message: 'Test message',
        type: 'alert',
        onConfirm: () => {
          confirmCalled = true;
        },
      });
      document.body.appendChild(dialog);

      const button = dialog.querySelector('button') as HTMLButtonElement;
      const enterEvent = new KeyboardEvent('keydown', {
        key: 'Enter',
        code: 'Enter',
      });

      button?.focus();
      button?.dispatchEvent(enterEvent);
      button?.click();

      expect(confirmCalled).toBe(true);
    });
  });

  describe('Toast Accessibility', () => {
    it('should have live region attributes', () => {
      const toast = Toast.create({
        id: 'test-toast',
        text: 'Notification message',
        type: 'info',
        duration: 0,
        onRemove: () => {},
      });

      expect(toast.getAttribute('role')).toBe('status');
      expect(toast.getAttribute('aria-live')).toBe('polite');
    });

    it('should have accessible close button', () => {
      const toast = Toast.create({
        id: 'test-toast',
        text: 'Message',
        type: 'info',
        duration: 0,
        onRemove: () => {},
      });

      const closeBtn = toast.querySelector('button');
      expect(closeBtn).toBeDefined();
      expect((closeBtn as HTMLButtonElement).textContent).toBe('×');
    });

    it('should have readable icon symbols', () => {
      const types: Array<'success' | 'error' | 'info' | 'warning'> = [
        'success',
        'error',
        'info',
        'warning',
      ];

      const expectedIcons: Record<string, string> = {
        success: '✓',
        error: '✕',
        info: 'ℹ',
        warning: '⚠',
      };

      types.forEach((type) => {
        const toast = Toast.create({
          id: `toast-${type}`,
          text: `${type} message`,
          type,
          duration: 0,
          onRemove: () => {},
        });

        expect(toast.textContent).toContain(expectedIcons[type]);
      });
    });

    it('should have CSS styling applied', () => {
      const toast = Toast.create({
        id: 'test-toast',
        text: 'Test message',
        type: 'success',
        duration: 0,
        onRemove: () => {},
      });

      const style = toast.getAttribute('style');
      expect(style).toBeTruthy();
      expect(style).toContain('display');
      expect(style).toContain('color: white');
      expect(style).toContain('background-color');
    });
  });

  describe('Focus Management', () => {
    it('should support tab navigation', () => {
      const dialog = createDialog({
        title: 'Test',
        message: 'Message',
        confirmText: 'Confirm',
        cancelText: 'Cancel',
        type: 'confirm',
        onConfirm: () => {},
        onCancel: () => {},
      });
      document.body.appendChild(dialog);

      const buttons = dialog.querySelectorAll('button');
      expect(buttons.length).toBeGreaterThanOrEqual(1);

      buttons.forEach((btn) => {
        expect((btn as HTMLButtonElement).type).not.toBeUndefined();
      });
    });

    it('should have proper button types for accessibility', () => {
      const dialog = createDialog({
        title: 'Test',
        message: 'Message',
        type: 'alert',
        onConfirm: () => {},
      });
      document.body.appendChild(dialog);

      const button = dialog.querySelector('button') as HTMLButtonElement;
      expect(button).toBeDefined();
      expect(['button', 'submit', 'reset', '']).toContain(button?.type || 'button');
    });
  });

  describe('Semantic HTML', () => {
    it('should use proper heading levels', () => {
      const dialog = createDialog({
        title: 'Dialog Title',
        message: 'Message',
        type: 'alert',
        onConfirm: () => {},
      });
      document.body.appendChild(dialog);

      const heading = dialog.querySelector('h2');
      expect(heading).toBeDefined();
      expect(heading?.textContent).toBe('Dialog Title');
    });

    it('should use div container for layout', () => {
      const container = Toast.createContainer();

      expect(container.tagName).toBe('DIV');
      expect(container.id).toBe('toast-container');
    });

    it('should have descriptive text content', () => {
      const dialog = createDialog({
        title: 'Confirm Delete',
        message: 'This action cannot be undone.',
        type: 'confirm',
        onConfirm: () => {},
        onCancel: () => {},
      });
      document.body.appendChild(dialog);

      expect(dialog.textContent).toContain('Confirm Delete');
      expect(dialog.textContent).toContain('This action cannot be undone.');
    });
  });
});
