/**
 * BatchPanel component - modal for batch file operations
 */

export interface BatchOperation {
  id: string;
  file: string;
  action: 'create' | 'update' | 'delete';
  status: 'pending' | 'processing' | 'completed' | 'error';
  content?: string;
  error?: string;
}

export interface BatchPanelOptions {
  operations: BatchOperation[];
  onExecute?: () => void;
  onCancel?: () => void;
  onClose?: () => void;
}

export function createBatchPanel(options: BatchPanelOptions): HTMLDivElement {
  const modal = document.createElement('div');
  modal.className = 'batch-panel-modal';

  modal.style.cssText = `
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background-color: rgba(0, 0, 0, 0.5);
    display: flex;
    align-items: center;
    justify-content: center;
    z-index: 9996;
    padding: 20px;
  `;

  const panel = document.createElement('div');
  panel.style.cssText = `
    background-color: var(--panel);
    border-radius: 8px;
    box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
    width: 100%;
    max-width: 700px;
    max-height: 80vh;
    display: flex;
    flex-direction: column;
    overflow: hidden;
  `;

  // Header
  const header = document.createElement('div');
  header.style.cssText = `
    padding: 16px;
    border-bottom: 1px solid var(--border);
    background-color: var(--bg);
  `;

  const title = document.createElement('h2');
  title.textContent = '📦 Batch Operations';
  title.style.cssText = `
    margin: 0 0 8px 0;
    font-size: 16px;
    font-weight: 600;
    color: var(--text);
  `;

  const stats = document.createElement('div');
  stats.style.cssText = `
    display: flex;
    gap: 12px;
    font-size: 12px;
    color: var(--text-secondary);
  `;

  const pending = options.operations.filter((o) => o.status === 'pending').length;
  const completed = options.operations.filter((o) => o.status === 'completed').length;
  const errors = options.operations.filter((o) => o.status === 'error').length;

  stats.textContent = `${completed} completed • ${pending} pending${errors > 0 ? ` • ${errors} errors` : ''}`;

  header.appendChild(title);
  header.appendChild(stats);

  // Operations list
  const list = document.createElement('div');
  list.className = 'batch-operations-list';
  list.style.cssText = `
    flex: 1;
    overflow-y: auto;
    padding: 12px;
    display: flex;
    flex-direction: column;
    gap: 8px;
  `;

  options.operations.forEach((op) => {
    const item = document.createElement('div');
    item.className = `batch-operation batch-op-${op.action}`;

    const statusColors = {
      pending: '#6b7280',
      processing: '#3b82f6',
      completed: '#10b981',
      error: '#ef4444',
    };

    const statusIcon = {
      pending: '⏳',
      processing: '⚙️',
      completed: '✓',
      error: '✕',
    };

    item.style.cssText = `
      display: flex;
      gap: 12px;
      padding: 10px;
      background-color: var(--bg);
      border: 1px solid var(--border);
      border-radius: 4px;
      border-left: 3px solid ${statusColors[op.status]};
    `;

    // Status icon
    const status = document.createElement('div');
    status.textContent = statusIcon[op.status];
    status.style.cssText = `
      font-size: 16px;
      flex-shrink: 0;
    `;

    // Info
    const info = document.createElement('div');
    info.style.cssText = `
      flex: 1;
      display: flex;
      flex-direction: column;
      gap: 4px;
    `;

    const filename = document.createElement('div');
    filename.textContent = op.file;
    filename.style.cssText = `
      font-size: 12px;
      font-weight: 500;
      color: var(--text);
    `;

    const action = document.createElement('div');
    action.textContent = op.action.toUpperCase();
    action.style.cssText = `
      font-size: 10px;
      padding: 2px 6px;
      background-color: var(--border);
      border-radius: 3px;
      color: var(--text-secondary);
      width: fit-content;
    `;

    info.appendChild(filename);
    info.appendChild(action);

    if (op.error) {
      const error = document.createElement('div');
      error.textContent = op.error;
      error.style.cssText = `
        font-size: 10px;
        color: var(--red);
      `;
      info.appendChild(error);
    }

    item.appendChild(status);
    item.appendChild(info);

    list.appendChild(item);
  });

  if (options.operations.length === 0) {
    const empty = document.createElement('div');
    empty.style.cssText = `
      display: flex;
      align-items: center;
      justify-content: center;
      height: 100%;
      color: var(--text-secondary);
      font-size: 13px;
    `;
    empty.textContent = 'No operations';
    list.appendChild(empty);
  }

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

  const closeBtn = document.createElement('button');
  closeBtn.textContent = 'Close';
  closeBtn.style.cssText = `
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

  closeBtn.addEventListener('click', () => {
    panel.style.animation = 'fadeOut 0.2s ease-in';
    setTimeout(() => {
      modal.remove();
      options.onClose?.();
    }, 200);
  });

  if (options.onCancel) {
    const cancelBtn = document.createElement('button');
    cancelBtn.textContent = '⏹️ Cancel';
    cancelBtn.style.cssText = `
      padding: 8px 16px;
      border: 1px solid var(--red);
      border-radius: 4px;
      background-color: transparent;
      color: var(--red);
      cursor: pointer;
      font-size: 12px;
      font-weight: 500;
      transition: all 0.2s;
      font-family: inherit;
    `;

    cancelBtn.addEventListener('click', () => {
      options.onCancel?.();
    });

    footer.appendChild(cancelBtn);
  }

  if (options.onExecute) {
    const executeBtn = document.createElement('button');
    executeBtn.textContent = '▶ Execute';
    executeBtn.style.cssText = `
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

    executeBtn.addEventListener('mouseover', () => {
      executeBtn.style.opacity = '0.8';
    });

    executeBtn.addEventListener('mouseout', () => {
      executeBtn.style.opacity = '1';
    });

    executeBtn.addEventListener('click', () => {
      executeBtn.disabled = true;
      options.onExecute?.();
    });

    footer.appendChild(executeBtn);
  }

  footer.appendChild(closeBtn);

  panel.appendChild(header);
  panel.appendChild(list);
  panel.appendChild(footer);
  modal.appendChild(panel);

  return modal;
}

export const BatchPanel = {
  create: createBatchPanel,
};
