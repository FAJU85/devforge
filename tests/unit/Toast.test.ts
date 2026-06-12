import { describe, it, expect, beforeEach } from 'vitest';
import { Toast } from '../../src/components/common/Toast';

describe('Toast Component', () => {
  beforeEach(() => {
    document.body.innerHTML = '';
  });

  it('should create a toast element', () => {
    const toast = Toast.create({
      id: 'test-toast',
      text: 'Test message',
      type: 'success',
      duration: 3000,
      onRemove: () => {},
    });

    expect(toast).toBeDefined();
    expect(toast.id).toBe('test-toast');
  });

  it('should set message text correctly', () => {
    const toast = Toast.create({
      id: 'test-toast',
      text: 'My Test Message',
      type: 'success',
      duration: 3000,
      onRemove: () => {},
    });

    expect(toast.textContent).toContain('My Test Message');
  });

  it('should have role="status" for accessibility', () => {
    const toast = Toast.create({
      id: 'test-toast',
      text: 'Message',
      type: 'success',
      duration: 3000,
      onRemove: () => {},
    });

    expect(toast.getAttribute('role')).toBe('status');
  });

  it('should have aria-live for screen readers', () => {
    const toast = Toast.create({
      id: 'test-toast',
      text: 'Message',
      type: 'info',
      duration: 3000,
      onRemove: () => {},
    });

    expect(toast.getAttribute('aria-live')).toBe('polite');
  });

  it('should create container element', () => {
    const container = Toast.createContainer();

    expect(container).toBeDefined();
    expect(container.id).toBe('toast-container');
  });

  it('should have close button', () => {
    const toast = Toast.create({
      id: 'test-toast',
      text: 'Message',
      type: 'error',
      duration: 3000,
      onRemove: () => {},
    });

    const buttons = toast.querySelectorAll('button');
    expect(buttons.length).toBeGreaterThan(0);
  });

  it('should call onRemove when close button clicked', async () => {
    let removeCalled = false;
    const removeId = 'test-toast';

    const toast = Toast.create({
      id: removeId,
      text: 'Message',
      type: 'warning',
      duration: 3000,
      onRemove: (id) => {
        if (id === removeId) {
          removeCalled = true;
        }
      },
    });

    const closeBtn = toast.querySelector('button') as HTMLButtonElement;
    closeBtn?.click();

    // Wait for animation and callback (300ms)
    await new Promise((resolve) => setTimeout(resolve, 350));

    expect(removeCalled).toBe(true);
  });

  it('should have success icon for success type', () => {
    const toast = Toast.create({
      id: 'test-toast',
      text: 'Success',
      type: 'success',
      duration: 3000,
      onRemove: () => {},
    });

    expect(toast.textContent).toContain('✓');
  });

  it('should have error icon for error type', () => {
    const toast = Toast.create({
      id: 'test-toast',
      text: 'Error',
      type: 'error',
      duration: 3000,
      onRemove: () => {},
    });

    expect(toast.textContent).toContain('✕');
  });

  it('should have info icon for info type', () => {
    const toast = Toast.create({
      id: 'test-toast',
      text: 'Info',
      type: 'info',
      duration: 3000,
      onRemove: () => {},
    });

    expect(toast.textContent).toContain('ℹ');
  });

  it('should have warning icon for warning type', () => {
    const toast = Toast.create({
      id: 'test-toast',
      text: 'Warning',
      type: 'warning',
      duration: 3000,
      onRemove: () => {},
    });

    expect(toast.textContent).toContain('⚠');
  });
});
