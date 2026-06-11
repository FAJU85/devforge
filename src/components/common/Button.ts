/**
 * Button component - base button with variants
 */

import { ButtonProps } from '@types/ui';

export function createButton(props: ButtonProps): HTMLButtonElement {
  const button = document.createElement('button');

  // Apply styles
  button.style.cssText = `
    padding: 8px 16px;
    border-radius: 6px;
    border: none;
    cursor: pointer;
    font-size: 14px;
    font-weight: 500;
    transition: all 0.2s;
    font-family: inherit;
  `;

  // Apply variant styles
  const variants = {
    primary: `
      background-color: var(--accent);
      color: var(--bg);
    `,
    secondary: `
      background-color: var(--panel);
      color: var(--text);
      border: 1px solid var(--border);
    `,
    danger: `
      background-color: var(--red);
      color: white;
    `,
  };

  button.style.cssText += variants[props.variant || 'primary'];

  // Apply hover state
  button.addEventListener('mouseenter', () => {
    button.style.opacity = '0.8';
  });

  button.addEventListener('mouseleave', () => {
    button.style.opacity = '1';
  });

  // Set properties
  button.textContent = props.label;
  button.disabled = props.disabled || false;
  if (props.className) button.className = props.className;

  // Attach click handler
  if (props.onClick) {
    button.addEventListener('click', props.onClick);
  }

  return button;
}

// Attach to Button namespace for easier usage
export const Button = {
  create: createButton,
};
