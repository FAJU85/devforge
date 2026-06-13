/**
 * WritePanel component - modal for writing and editing files
 */

export interface WritePanelOptions {
  filename: string;
  initialContent?: string;
  language?: string;
  readOnly?: boolean;
  onSave?: (content: string) => void;
  onClose?: () => void;
}

export function createWritePanel(options: WritePanelOptions): HTMLDivElement {
  const modal = document.createElement('div');
  modal.className = 'write-panel-modal';

  modal.style.cssText = `
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background-color: rgba(0, 0, 0, 0.5);
    display: flex;
    align-items: flex-end;
    justify-content: flex-end;
    z-index: 9996;
  `;

  const panel = document.createElement('div');
  panel.style.cssText = `
    background-color: var(--panel);
    width: 100%;
    max-width: 600px;
    height: 100vh;
    display: flex;
    flex-direction: column;
    box-shadow: -4px 0 12px rgba(0, 0, 0, 0.2);
    animation: slideIn 0.3s ease-out;
  `;

  // Header
  const header = document.createElement('div');
  header.style.cssText = `
    padding: 16px;
    border-bottom: 1px solid var(--border);
    background-color: var(--bg);
    display: flex;
    justify-content: space-between;
    align-items: center;
  `;

  const title = document.createElement('h2');
  title.textContent = `✏️ ${options.filename}`;
  title.style.cssText = `
    margin: 0;
    font-size: 16px;
    font-weight: 600;
    color: var(--text);
  `;

  const closeBtn = document.createElement('button');
  closeBtn.textContent = '✕';
  closeBtn.style.cssText = `
    background: none;
    border: none;
    color: var(--text);
    font-size: 20px;
    cursor: pointer;
    transition: color 0.2s;
  `;

  closeBtn.addEventListener('mouseover', () => {
    closeBtn.style.color = 'var(--red)';
  });

  closeBtn.addEventListener('mouseout', () => {
    closeBtn.style.color = 'var(--text)';
  });

  closeBtn.addEventListener('click', () => {
    panel.style.animation = 'slideOut 0.3s ease-in';
    setTimeout(() => {
      modal.remove();
      options.onClose?.();
    }, 300);
  });

  header.appendChild(title);
  header.appendChild(closeBtn);

  // Editor
  const editor = document.createElement('textarea');
  editor.value = options.initialContent || '';
  editor.readOnly = options.readOnly || false;
  editor.spellcheck = false;

  editor.style.cssText = `
    flex: 1;
    padding: 12px;
    border: none;
    background-color: var(--bg);
    color: var(--text);
    font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
    font-size: 13px;
    line-height: 1.5;
    resize: none;
    outline: none;
  `;

  // Footer
  const footer = document.createElement('div');
  footer.style.cssText = `
    padding: 12px 16px;
    border-top: 1px solid var(--border);
    background-color: var(--panel);
    display: flex;
    gap: 12px;
    justify-content: flex-end;
  `;

  if (!options.readOnly) {
    const saveBtn = document.createElement('button');
    saveBtn.textContent = '💾 Save';
    saveBtn.style.cssText = `
      padding: 8px 16px;
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
      options.onSave?.(editor.value);
      saveBtn.textContent = '✓ Saved';
      setTimeout(() => {
        saveBtn.textContent = '💾 Save';
      }, 2000);
    });

    footer.appendChild(saveBtn);
  }

  const cancelBtn = document.createElement('button');
  cancelBtn.textContent = 'Close';
  cancelBtn.style.cssText = `
    padding: 8px 16px;
    border: 1px solid var(--border);
    border-radius: 4px;
    background-color: transparent;
    color: var(--text);
    cursor: pointer;
    font-size: 12px;
    font-weight: 500;
    transition: all 0.2s;
    font-family: inherit;
  `;

  cancelBtn.addEventListener('click', () => {
    closeBtn.click();
  });

  footer.appendChild(cancelBtn);

  panel.appendChild(header);
  panel.appendChild(editor);
  panel.appendChild(footer);
  modal.appendChild(panel);

  // Expose methods
  (modal as any).getValue = () => editor.value;
  (modal as any).setValue = (content: string) => {
    editor.value = content;
  };

  return modal;
}

export const WritePanel = {
  create: createWritePanel,
};
