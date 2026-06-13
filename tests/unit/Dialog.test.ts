import { describe, it, expect, beforeEach } from 'vitest';
import { createDialog } from '../../src/components/common/Dialog';

describe('Dialog Component', () => {
  let container: HTMLElement;

  beforeEach(() => {
    container = document.body;
    container.innerHTML = '';
  });

  it('should create a dialog element', () => {
    const dialog = createDialog({
      title: 'Test Dialog',
      message: 'This is a test',
      confirmText: 'OK',
      type: 'alert',
    });

    expect(dialog).toBeDefined();
    expect(dialog.getAttribute('role')).not.toBe('dialog');
    expect(dialog.querySelector('[role="dialog"]')).toBeTruthy();
  });

  it('should set title correctly', () => {
    const dialog = createDialog({
      title: 'Test Title',
      message: 'Message',
      confirmText: 'OK',
      type: 'alert',
    });

    const titleElement = dialog.querySelector('h2');
    expect(titleElement?.textContent).toBe('Test Title');
  });

  it('should set message correctly', () => {
    const dialog = createDialog({
      title: 'Title',
      message: 'Test Message',
      confirmText: 'OK',
      type: 'alert',
    });

    const messageElement = dialog.querySelector('p');
    expect(messageElement?.textContent).toBe('Test Message');
  });

  it('should have confirm button with correct text', () => {
    const dialog = createDialog({
      title: 'Title',
      message: 'Message',
      confirmText: 'Confirm',
      type: 'confirm',
    });

    const buttons = dialog.querySelectorAll('button');
    const confirmBtn = Array.from(buttons).find((btn) => btn.textContent === 'Confirm');
    expect(confirmBtn).toBeTruthy();
  });

  it('should have cancel button for confirm type', () => {
    const dialog = createDialog({
      title: 'Title',
      message: 'Message',
      confirmText: 'Confirm',
      cancelText: 'Cancel',
      type: 'confirm',
    });

    const buttons = dialog.querySelectorAll('button');
    const cancelBtn = Array.from(buttons).find((btn) => btn.textContent === 'Cancel');
    expect(cancelBtn).toBeTruthy();
  });

  it('should not have cancel button for alert type', () => {
    const dialog = createDialog({
      title: 'Title',
      message: 'Message',
      confirmText: 'OK',
      type: 'alert',
    });

    const buttons = dialog.querySelectorAll('button');
    expect(buttons.length).toBe(1);
  });

  it('should have pointer-events auto on overlay', () => {
    const dialog = createDialog({
      title: 'Title',
      message: 'Message',
      confirmText: 'OK',
      type: 'alert',
    });

    const pointerEvents = dialog.style.pointerEvents;
    expect(pointerEvents).toBe('auto');
  });

  it('should have pointer-events auto on dialog', () => {
    const dialog = createDialog({
      title: 'Title',
      message: 'Message',
      confirmText: 'OK',
      type: 'alert',
    });

    const dialogEl = dialog.querySelector('[role="dialog"]');
    const pointerEvents = (dialogEl as HTMLElement)?.style.pointerEvents;
    expect(pointerEvents).toBe('auto');
  });

  it('should call onConfirm callback when confirm button clicked', async () => {
    let confirmCalled = false;

    const dialog = createDialog({
      title: 'Title',
      message: 'Message',
      confirmText: 'OK',
      type: 'alert',
      onConfirm: () => {
        confirmCalled = true;
      },
    });

    const confirmBtn = dialog.querySelector('button') as HTMLButtonElement;
    confirmBtn?.click();

    // Give it a moment for callback
    await new Promise((resolve) => setTimeout(resolve, 10));

    expect(confirmCalled).toBe(true);
  });
});
