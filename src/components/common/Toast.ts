/**
 * Toast component - notification messages with auto-dismiss
 */

import { ToastMessage } from '@types/ui';

interface ToastElementProps extends ToastMessage {
  onRemove: (id: string) => void;
}

export function createToast(props: ToastElementProps): HTMLDivElement {
  const toast = document.createElement('div');

  const colors = {
    success: { bg: 'var(--green)', icon: '✓' },
    error: { bg: 'var(--red)', icon: '✕' },
    info: { bg: 'var(--accent)', icon: 'ℹ' },
    warning: { bg: 'var(--yellow)', icon: '⚠' },
  };

  const color = colors[props.type] || colors.info;

  toast.style.cssText = `
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 12px 16px;
    border-radius: 6px;
    background-color: ${color.bg};
    color: white;
    font-size: 14px;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
    min-width: 300px;
    animation: slideIn 0.3s ease-out;
  `;

  toast.id = props.id;

  const icon = document.createElement('span');
  icon.textContent = color.icon;
  icon.style.cssText = `
    font-weight: bold;
    font-size: 16px;
    flex-shrink: 0;
  `;

  const message = document.createElement('span');
  message.textContent = props.text;
  message.style.cssText = `
    flex: 1;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  `;

  const closeBtn = document.createElement('button');
  closeBtn.textContent = '×';
  closeBtn.style.cssText = `
    background: none;
    border: none;
    color: white;
    font-size: 20px;
    cursor: pointer;
    padding: 0;
    flex-shrink: 0;
    transition: opacity 0.2s;
  `;

  closeBtn.addEventListener('mouseover', () => {
    closeBtn.style.opacity = '0.7';
  });

  closeBtn.addEventListener('mouseout', () => {
    closeBtn.style.opacity = '1';
  });

  closeBtn.addEventListener('click', () => {
    toast.style.animation = 'slideOut 0.3s ease-in';
    setTimeout(() => props.onRemove(props.id), 300);
  });

  toast.appendChild(icon);
  toast.appendChild(message);
  toast.appendChild(closeBtn);

  return toast;
}

export function createToastContainer(): HTMLDivElement {
  const container = document.createElement('div');
  container.style.cssText = `
    position: fixed;
    top: 20px;
    right: 20px;
    display: flex;
    flex-direction: column;
    gap: 10px;
    max-width: 400px;
    z-index: 9999;
  `;

  const style = document.createElement('style');
  style.textContent = `
    @keyframes slideIn {
      from {
        transform: translateX(400px);
        opacity: 0;
      }
      to {
        transform: translateX(0);
        opacity: 1;
      }
    }

    @keyframes slideOut {
      from {
        transform: translateX(0);
        opacity: 1;
      }
      to {
        transform: translateX(400px);
        opacity: 0;
      }
    }
  `;

  document.head.appendChild(style);

  return container;
}

export const Toast = {
  create: createToast,
  createContainer: createToastContainer,
};
