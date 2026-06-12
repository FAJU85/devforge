/**
 * ApiKeyInput component - secure API key management
 */

export interface ApiKeyInputOptions {
  label: string;
  provider: string;
  placeholder?: string;
  icon?: string;
  onSave?: (key: string) => void;
  onRemove?: () => void;
  hasExisting?: boolean;
  helpText?: string;
}

export function createApiKeyInput(options: ApiKeyInputOptions): HTMLDivElement {
  const container = document.createElement('div');
  container.className = 'api-key-input';

  container.style.cssText = `
    display: flex;
    flex-direction: column;
    gap: 8px;
    padding: 12px;
    border: 1px solid var(--border);
    border-radius: 6px;
    background-color: var(--panel);
  `;

  // Header
  const header = document.createElement('div');
  header.style.cssText = `
    display: flex;
    align-items: center;
    gap: 8px;
  `;

  if (options.icon) {
    const icon = document.createElement('span');
    icon.textContent = options.icon;
    icon.style.fontSize = '18px';
    header.appendChild(icon);
  }

  const label = document.createElement('label');
  label.textContent = options.label;
  label.style.cssText = `
    font-weight: 600;
    color: var(--text);
    font-size: 13px;
  `;

  header.appendChild(label);

  // Status badge
  if (options.hasExisting) {
    const badge = document.createElement('div');
    badge.textContent = '✓ Configured';
    badge.style.cssText = `
      margin-left: auto;
      padding: 2px 8px;
      background-color: rgba(16, 185, 129, 0.2);
      color: var(--green);
      font-size: 11px;
      border-radius: 3px;
    `;
    header.appendChild(badge);
  }

  // Input wrapper
  const inputWrapper = document.createElement('div');
  inputWrapper.style.cssText = `
    display: flex;
    gap: 8px;
    align-items: center;
  `;

  const input = document.createElement('input');
  input.type = 'password';
  input.placeholder = options.placeholder || 'Enter API key...';
  input.style.cssText = `
    flex: 1;
    padding: 8px 12px;
    border: 1px solid var(--border);
    border-radius: 4px;
    background-color: var(--input-bg);
    color: var(--text);
    font-size: 13px;
    font-family: inherit;
    transition: border-color 0.2s;
  `;

  const toggleVisibility = document.createElement('button');
  toggleVisibility.textContent = '👁️';
  toggleVisibility.style.cssText = `
    padding: 4px 8px;
    border: 1px solid var(--border);
    background-color: transparent;
    color: var(--text-secondary);
    border-radius: 4px;
    cursor: pointer;
    font-size: 14px;
    transition: all 0.2s;
  `;

  let isVisible = false;
  toggleVisibility.addEventListener('click', () => {
    isVisible = !isVisible;
    input.type = isVisible ? 'text' : 'password';
    toggleVisibility.textContent = isVisible ? '🙈' : '👁️';
  });

  toggleVisibility.addEventListener('mouseover', () => {
    toggleVisibility.style.backgroundColor = 'var(--border)';
  });

  toggleVisibility.addEventListener('mouseout', () => {
    toggleVisibility.style.backgroundColor = 'transparent';
  });

  input.addEventListener('focus', () => {
    input.style.borderColor = 'var(--accent)';
  });

  input.addEventListener('blur', () => {
    input.style.borderColor = 'var(--border)';
  });

  inputWrapper.appendChild(input);
  inputWrapper.appendChild(toggleVisibility);

  // Action buttons
  const actions = document.createElement('div');
  actions.style.cssText = `
    display: flex;
    gap: 8px;
  `;

  const saveBtn = document.createElement('button');
  saveBtn.textContent = '💾 Save Key';
  saveBtn.style.cssText = `
    flex: 1;
    padding: 8px 12px;
    border: none;
    border-radius: 4px;
    background-color: var(--accent);
    color: var(--bg);
    cursor: pointer;
    font-size: 12px;
    font-weight: 500;
    transition: all 0.2s;
    font-family: inherit;
  `;

  saveBtn.addEventListener('mouseover', () => {
    saveBtn.style.opacity = '0.8';
  });

  saveBtn.addEventListener('mouseout', () => {
    saveBtn.style.opacity = '1';
  });

  saveBtn.addEventListener('click', () => {
    const value = input.value.trim();
    if (value) {
      options.onSave?.(value);
      input.value = '';
      saveBtn.textContent = '✓ Saved';
      setTimeout(() => {
        saveBtn.textContent = '💾 Save Key';
      }, 2000);
    }
  });

  actions.appendChild(saveBtn);

  // Remove button if key exists
  if (options.hasExisting) {
    const removeBtn = document.createElement('button');
    removeBtn.textContent = '🗑️ Remove';
    removeBtn.style.cssText = `
      padding: 8px 12px;
      border: 1px solid var(--border);
      border-radius: 4px;
      background-color: transparent;
      color: var(--text);
      cursor: pointer;
      font-size: 12px;
      transition: all 0.2s;
      font-family: inherit;
    `;

    removeBtn.addEventListener('mouseover', () => {
      removeBtn.style.backgroundColor = 'var(--red)';
      removeBtn.style.color = 'white';
    });

    removeBtn.addEventListener('mouseout', () => {
      removeBtn.style.backgroundColor = 'transparent';
      removeBtn.style.color = 'var(--text)';
    });

    removeBtn.addEventListener('click', () => {
      options.onRemove?.();
      input.value = '';
    });

    actions.appendChild(removeBtn);
  }

  // Help text
  let helpElement: HTMLElement | null = null;
  if (options.helpText) {
    helpElement = document.createElement('div');
    helpElement.style.cssText = `
      font-size: 11px;
      color: var(--text-secondary);
      padding-top: 4px;
    `;
    helpElement.textContent = options.helpText;
  }

  container.appendChild(header);
  container.appendChild(inputWrapper);
  container.appendChild(actions);
  if (helpElement) {
    container.appendChild(helpElement);
  }

  // Expose methods
  (container as any).getValue = () => input.value;
  (container as any).setValue = (value: string) => {
    input.value = value;
  };
  (container as any).clear = () => {
    input.value = '';
    input.type = 'password';
    isVisible = false;
    toggleVisibility.textContent = '👁️';
  };

  return container;
}

export const ApiKeyInput = {
  create: createApiKeyInput,
};
