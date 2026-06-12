import { describe, it, expect, beforeEach } from 'vitest';
import { createDialog } from '../../src/components/common/Dialog';
import { Toast } from '../../src/components/common/Toast';

describe('Dialog + Toast Integration', () => {
  beforeEach(() => {
    document.body.innerHTML = '';
  });

  it('should display dialog and toast together', () => {
    const toastContainer = Toast.createContainer();
    document.body.appendChild(toastContainer);

    const dialog = createDialog({
      title: 'Confirm Action',
      message: 'Are you sure?',
      confirmText: 'Confirm',
      cancelText: 'Cancel',
      type: 'confirm',
      onConfirm: () => {},
      onCancel: () => {},
    });
    document.body.appendChild(dialog);

    const toast = Toast.create({
      id: 'notification',
      text: 'Action pending',
      type: 'info',
      duration: 0,
      onRemove: () => {},
    });
    toastContainer.appendChild(toast);

    expect(dialog.textContent).toContain('Confirm Action');
    expect(toast.textContent).toContain('Action pending');
    expect(document.body.contains(dialog)).toBe(true);
    expect(document.body.contains(toastContainer)).toBe(true);
  });

  it('should handle dialog confirmation with toast notification', async () => {
    let confirmCalled = false;
    let toastRemoved = false;

    const toastContainer = Toast.createContainer();
    document.body.appendChild(toastContainer);

    const dialog = createDialog({
      title: 'Save Changes',
      message: 'Save your changes?',
      confirmText: 'Save',
      cancelText: 'Discard',
      type: 'confirm',
      onConfirm: () => {
        confirmCalled = true;
      },
      onCancel: () => {},
    });
    document.body.appendChild(dialog);

    const toast = Toast.create({
      id: 'save-notification',
      text: 'Changes saved',
      type: 'success',
      duration: 0,
      onRemove: () => {
        toastRemoved = true;
      },
    });
    toastContainer.appendChild(toast);

    const confirmBtn = Array.from(dialog.querySelectorAll('button')).find(
      (btn) => btn.textContent === 'Save'
    ) as HTMLButtonElement;
    confirmBtn?.click();

    await new Promise((resolve) => setTimeout(resolve, 250));
    expect(confirmCalled).toBe(true);

    const closeBtn = toast.querySelector('button') as HTMLButtonElement;
    closeBtn?.click();

    await new Promise((resolve) => setTimeout(resolve, 350));
    expect(toastRemoved).toBe(true);
  });

  it('should maintain separate dialog and toast zIndexes', () => {
    const toastContainer = Toast.createContainer();
    document.body.appendChild(toastContainer);

    const dialog = createDialog({
      title: 'Test',
      message: 'Message',
      type: 'alert',
      onConfirm: () => {},
    });
    document.body.appendChild(dialog);

    const dialogStyle = window.getComputedStyle(dialog);
    const containerStyle = window.getComputedStyle(toastContainer);

    const dialogZIndex = parseInt(dialogStyle.zIndex || '1000') || 1000;
    const containerZIndex = parseInt(containerStyle.zIndex || '9999') || 9999;

    expect(containerZIndex).toBeGreaterThanOrEqual(dialogZIndex);
  });

  it('should handle multiple toasts with dialog', async () => {
    const toastContainer = Toast.createContainer();
    document.body.appendChild(toastContainer);

    const dialog = createDialog({
      title: 'Dialog',
      message: 'Message',
      type: 'alert',
      onConfirm: () => {},
    });
    document.body.appendChild(dialog);

    let removeCount = 0;
    const onToastRemove = () => {
      removeCount++;
    };

    const toast1 = Toast.create({
      id: 'toast1',
      text: 'First notification',
      type: 'info',
      duration: 0,
      onRemove: onToastRemove,
    });

    const toast2 = Toast.create({
      id: 'toast2',
      text: 'Second notification',
      type: 'info',
      duration: 0,
      onRemove: onToastRemove,
    });

    toastContainer.appendChild(toast1);
    toastContainer.appendChild(toast2);

    expect(toastContainer.children.length).toBe(2);

    const btn1 = toast1.querySelector('button') as HTMLButtonElement;
    btn1?.click();

    await new Promise((resolve) => setTimeout(resolve, 350));
    expect(removeCount).toBe(1);
  });
});
