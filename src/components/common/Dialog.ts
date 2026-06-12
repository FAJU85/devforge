/**
 * Dialog component - modal dialogs with confirm/cancel
 */

import { DialogOptions } from '@types/ui';

export function createDialog(options: DialogOptions): HTMLDivElement {
  const overlay = document.createElement('div');
  overlay.style.cssText = `
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background-color: rgba(0, 0, 0, 0.5);
    display: flex;
    align-items: center;
    justify-content: center;
    z-index: 9998;
    animation: fadeIn 0.2s ease-out;
  `;

  const dialog = document.createElement('div');
  dialog.setAttribute('role', 'dialog');
  dialog.setAttribute('aria-modal', 'true');
  dialog.style.cssText = `
    background-color: var(--bg);
    border-radius: 8px;
    padding: 24px;
    box-shadow: 0 10px 40px rgba(0, 0, 0, 0.3);
    max-width: 500px;
    width: 90%;
    animation: slideUp 0.3s ease-out;
  `;

  const title = document.createElement('h2');
  title.textContent = options.title;
  title.style.cssText = `
    margin: 0 0 12px 0;
    color: var(--text);
    font-size: 18px;
    font-weight: 600;
  `;

  const message = document.createElement('p');
  message.textContent = options.message;
  message.style.cssText = `
    margin: 0 0 24px 0;
    color: var(--text-secondary);
    font-size: 14px;
    line-height: 1.5;
  `;

  const buttonContainer = document.createElement('div');
  buttonContainer.style.cssText = `
    display: flex;
    gap: 12px;
    justify-content: flex-end;
  `;

  const cancelText = options.cancelText || 'Cancel';
  const confirmText = options.confirmText || (options.type === 'alert' ? 'OK' : 'Confirm');

  const closeDialog = (callback?: () => void) => {
    overlay.style.animation = 'fadeOut 0.2s ease-in';
    dialog.style.animation = 'slideDown 0.2s ease-in';
    setTimeout(() => {
      overlay.remove();
      if (callback) callback();
    }, 200);
  };

  if (options.type !== 'alert') {
    const cancelBtn = document.createElement('button');
    cancelBtn.textContent = cancelText;
    cancelBtn.style.cssText = `
      padding: 8px 16px;
      border-radius: 6px;
      border: 1px solid var(--border);
      background-color: var(--panel);
      color: var(--text);
      cursor: pointer;
      font-size: 14px;
      font-weight: 500;
      transition: all 0.2s;
      font-family: inherit;
    `;

    cancelBtn.addEventListener('mouseover', () => {
      cancelBtn.style.backgroundColor = 'var(--border)';
    });

    cancelBtn.addEventListener('mouseout', () => {
      cancelBtn.style.backgroundColor = 'var(--panel)';
    });

    cancelBtn.addEventListener('click', () => {
      closeDialog(options.onCancel);
    });

    buttonContainer.appendChild(cancelBtn);
  }

  const confirmBtn = document.createElement('button');
  confirmBtn.textContent = confirmText;
  confirmBtn.style.cssText = `
    padding: 8px 16px;
    border-radius: 6px;
    border: none;
    background-color: var(--accent);
    color: var(--bg);
    cursor: pointer;
    font-size: 14px;
    font-weight: 500;
    transition: all 0.2s;
    font-family: inherit;
  `;

  confirmBtn.addEventListener('mouseover', () => {
    confirmBtn.style.opacity = '0.8';
  });

  confirmBtn.addEventListener('mouseout', () => {
    confirmBtn.style.opacity = '1';
  });

  confirmBtn.addEventListener('click', () => {
    closeDialog(options.onConfirm);
  });

  buttonContainer.appendChild(confirmBtn);

  overlay.addEventListener('click', (e) => {
    if (e.target === overlay) {
      closeDialog(options.onCancel);
    }
  });

  dialog.appendChild(title);
  dialog.appendChild(message);
  dialog.appendChild(buttonContainer);
  overlay.appendChild(dialog);

  const style = document.createElement('style');
  style.textContent = `
    @keyframes fadeIn {
      from {
        opacity: 0;
      }
      to {
        opacity: 1;
      }
    }

    @keyframes fadeOut {
      from {
        opacity: 1;
      }
      to {
        opacity: 0;
      }
    }

    @keyframes slideUp {
      from {
        transform: translateY(20px);
        opacity: 0;
      }
      to {
        transform: translateY(0);
        opacity: 1;
      }
    }

    @keyframes slideDown {
      from {
        transform: translateY(0);
        opacity: 1;
      }
      to {
        transform: translateY(20px);
        opacity: 0;
      }
    }
  `;

  document.head.appendChild(style);

  return overlay;
}

export const Dialog = {
  create: createDialog,
};
