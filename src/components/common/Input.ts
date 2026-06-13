/**
 * Input component - text input field
 */

import { InputProps } from '@types/ui';

export function createInput(props: InputProps): HTMLInputElement {
  const input = document.createElement('input');

  // Apply base styles
  input.style.cssText = `
    padding: 8px 12px;
    border-radius: 6px;
    border: 1px solid var(--border);
    background-color: var(--input-bg);
    color: var(--text);
    font-size: 14px;
    font-family: inherit;
    transition: border-color 0.2s;
  `;

  // Set type and properties
  input.type = props.type || 'text';
  input.value = props.value;
  input.placeholder = props.placeholder || '';
  input.disabled = props.disabled || false;
  if (props.className) input.className = props.className;

  // Add focus styles
  input.addEventListener('focus', () => {
    input.style.borderColor = 'var(--accent)';
    input.style.boxShadow = '0 0 0 2px var(--accent-dim)';
  });

  input.addEventListener('blur', () => {
    input.style.borderColor = 'var(--border)';
    input.style.boxShadow = 'none';
  });

  // Add error state styling if provided
  if ((props as any).error) {
    input.style.borderColor = 'var(--red)';
    input.style.boxShadow = '0 0 0 2px rgba(239, 68, 68, 0.2)';
  }

  // Attach change handler with guard
  input.addEventListener('input', (e) => {
    const target = e.target as HTMLInputElement;
    if (props.onChange) {
      props.onChange(target.value);
    }
  });

  return input;
}

// Attach to Input namespace for easier usage
export const Input = {
  create: createInput,
};
