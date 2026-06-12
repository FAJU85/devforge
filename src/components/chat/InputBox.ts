/**
 * InputBox component - chat message input with send button
 */

export interface InputBoxOptions {
  placeholder?: string;
  onSend: (message: string) => void;
  onCancel?: () => void;
  disabled?: boolean;
  maxLength?: number;
}

export function createInputBox(options: InputBoxOptions): HTMLDivElement {
  const container = document.createElement('div');
  container.className = 'input-box-container';

  container.style.cssText = `
    display: flex;
    flex-direction: column;
    gap: 8px;
    padding: 16px;
    border-top: 1px solid var(--border);
    background-color: var(--panel);
    border-radius: 0 0 8px 8px;
  `;

  // Input area
  const inputArea = document.createElement('div');
  inputArea.style.cssText = `
    display: flex;
    gap: 10px;
    align-items: flex-end;
  `;

  // Textarea
  const textarea = document.createElement('textarea');
  textarea.placeholder = options.placeholder || 'Type your message here...';
  textarea.disabled = options.disabled || false;
  if (options.maxLength) {
    textarea.maxLength = options.maxLength;
  }

  textarea.style.cssText = `
    flex: 1;
    padding: 10px 12px;
    border: 1px solid var(--border);
    border-radius: 6px;
    background-color: var(--input-bg);
    color: var(--text);
    font-size: 14px;
    font-family: inherit;
    resize: none;
    max-height: 200px;
    min-height: 44px;
    transition: border-color 0.2s;
  `;

  textarea.addEventListener('focus', () => {
    textarea.style.borderColor = 'var(--accent)';
    textarea.style.boxShadow = '0 0 0 2px var(--accent-dim)';
  });

  textarea.addEventListener('blur', () => {
    textarea.style.borderColor = 'var(--border)';
    textarea.style.boxShadow = 'none';
  });

  // Auto-grow textarea
  textarea.addEventListener('input', () => {
    textarea.style.height = '44px';
    textarea.style.height = Math.min(textarea.scrollHeight, 200) + 'px';
  });

  // Send button
  const sendBtn = document.createElement('button');
  sendBtn.textContent = '📤 Send';
  sendBtn.style.cssText = `
    padding: 10px 16px;
    border: none;
    border-radius: 6px;
    background-color: var(--accent);
    color: var(--bg);
    cursor: pointer;
    font-size: 13px;
    font-weight: 500;
    transition: all 0.2s;
    font-family: inherit;
    white-space: nowrap;
    flex-shrink: 0;
  `;

  sendBtn.addEventListener('mouseover', () => {
    sendBtn.style.opacity = '0.8';
  });

  sendBtn.addEventListener('mouseout', () => {
    sendBtn.style.opacity = '1';
  });

  sendBtn.addEventListener('click', () => {
    const message = textarea.value.trim();
    if (message) {
      options.onSend(message);
      textarea.value = '';
      textarea.style.height = '44px';
      textarea.focus();
    }
  });

  // Send on Ctrl+Enter or Cmd+Enter
  textarea.addEventListener('keydown', (e) => {
    if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
      sendBtn.click();
    }
  });

  inputArea.appendChild(textarea);
  inputArea.appendChild(sendBtn);

  // Character count
  const charCount = document.createElement('div');
  charCount.style.cssText = `
    display: flex;
    justify-content: space-between;
    align-items: center;
    font-size: 12px;
    color: var(--text-secondary);
  `;

  const counter = document.createElement('span');
  counter.textContent = `0/${options.maxLength || 'unlimited'} characters`;

  charCount.appendChild(counter);

  if (options.onCancel) {
    const cancelBtn = document.createElement('button');
    cancelBtn.textContent = 'Cancel';
    cancelBtn.style.cssText = `
      padding: 4px 12px;
      border: 1px solid var(--border);
      background-color: transparent;
      color: var(--text);
      border-radius: 4px;
      cursor: pointer;
      font-size: 12px;
      transition: all 0.2s;
      font-family: inherit;
    `;

    cancelBtn.addEventListener('mouseover', () => {
      cancelBtn.style.backgroundColor = 'var(--border)';
    });

    cancelBtn.addEventListener('mouseout', () => {
      cancelBtn.style.backgroundColor = 'transparent';
    });

    cancelBtn.addEventListener('click', () => {
      textarea.value = '';
      textarea.style.height = '44px';
      options.onCancel?.();
    });

    charCount.appendChild(cancelBtn);
  }

  textarea.addEventListener('input', () => {
    counter.textContent = `${textarea.value.length}/${options.maxLength || 'unlimited'} characters`;
  });

  container.appendChild(inputArea);
  container.appendChild(charCount);

  // Expose methods
  (container as any).getValue = () => textarea.value;
  (container as any).setValue = (value: string) => {
    textarea.value = value;
    textarea.style.height = Math.min(textarea.scrollHeight, 200) + 'px';
    counter.textContent = `${value.length}/${options.maxLength || 'unlimited'} characters`;
  };
  (container as any).focus = () => textarea.focus();
  (container as any).disable = (disabled: boolean) => {
    textarea.disabled = disabled;
    sendBtn.disabled = disabled;
    sendBtn.style.opacity = disabled ? '0.5' : '1';
  };

  return container;
}

export const InputBox = {
  create: createInputBox,
};
