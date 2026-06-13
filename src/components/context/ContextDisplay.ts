/**
 * ContextDisplay component - shows current context with files and code snippets
 */

export interface ContextItem {
  id: string;
  type: 'file' | 'function' | 'class' | 'variable';
  name: string;
  path: string;
  preview?: string;
  tokens?: number;
}

export interface ContextDisplayOptions {
  items: ContextItem[];
  maxTokens?: number;
  onRemove?: (id: string) => void;
  onPreview?: (item: ContextItem) => void;
}

export function createContextDisplay(options: ContextDisplayOptions): HTMLDivElement {
  const container = document.createElement('div');
  container.className = 'context-display';

  container.style.cssText = `
    display: flex;
    flex-direction: column;
    gap: 8px;
    padding: 12px;
    background-color: var(--panel);
    border-radius: 6px;
    border: 1px solid var(--border);
  `;

  // Header
  const header = document.createElement('div');
  header.style.cssText = `
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding-bottom: 8px;
    border-bottom: 1px solid var(--border);
  `;

  const title = document.createElement('h3');
  title.textContent = 'Context';
  title.style.cssText = `
    margin: 0;
    font-size: 13px;
    font-weight: 600;
    color: var(--text);
  `;

  const count = document.createElement('span');
  count.textContent = `${options.items.length} items`;
  count.style.cssText = `
    font-size: 11px;
    color: var(--text-secondary);
  `;

  header.appendChild(title);
  header.appendChild(count);

  // Items container
  const itemsContainer = document.createElement('div');
  itemsContainer.className = 'context-items';
  itemsContainer.style.cssText = `
    display: flex;
    flex-direction: column;
    gap: 6px;
    max-height: 400px;
    overflow-y: auto;
  `;

  options.items.forEach((item) => {
    const itemDiv = document.createElement('div');
    itemDiv.className = `context-item context-item-${item.type}`;
    itemDiv.style.cssText = `
      display: flex;
      align-items: center;
      gap: 8px;
      padding: 8px;
      background-color: var(--bg);
      border-radius: 4px;
      border: 1px solid var(--border);
      transition: all 0.2s;
    `;

    // Icon based on type
    const icons: { [key: string]: string } = {
      file: '📄',
      function: '𝒇',
      class: '𝐂',
      variable: '𝐯',
    };

    const icon = document.createElement('span');
    icon.textContent = icons[item.type] || '📌';
    icon.style.fontSize = '14px';

    // Name and path
    const info = document.createElement('div');
    info.style.cssText = `
      flex: 1;
      display: flex;
      flex-direction: column;
      gap: 2px;
      min-width: 0;
    `;

    const name = document.createElement('div');
    name.textContent = item.name;
    name.style.cssText = `
      font-size: 12px;
      font-weight: 500;
      color: var(--text);
      white-space: nowrap;
      overflow: hidden;
      text-overflow: ellipsis;
    `;

    const path = document.createElement('div');
    path.textContent = item.path;
    path.style.cssText = `
      font-size: 10px;
      color: var(--text-secondary);
      white-space: nowrap;
      overflow: hidden;
      text-overflow: ellipsis;
    `;

    info.appendChild(name);
    info.appendChild(path);

    // Token count and actions
    const actions = document.createElement('div');
    actions.style.cssText = `
      display: flex;
      align-items: center;
      gap: 6px;
      opacity: 0;
      transition: opacity 0.2s;
    `;

    if (item.tokens) {
      const tokens = document.createElement('span');
      tokens.textContent = `${item.tokens}t`;
      tokens.style.cssText = `
        font-size: 10px;
        color: var(--text-secondary);
        white-space: nowrap;
      `;
      actions.appendChild(tokens);
    }

    const removeBtn = document.createElement('button');
    removeBtn.textContent = '✕';
    removeBtn.style.cssText = `
      padding: 2px 4px;
      background: none;
      border: none;
      color: var(--text-secondary);
      cursor: pointer;
      font-size: 14px;
      transition: color 0.2s;
    `;

    removeBtn.addEventListener('mouseover', () => {
      removeBtn.style.color = 'var(--red)';
    });

    removeBtn.addEventListener('mouseout', () => {
      removeBtn.style.color = 'var(--text-secondary)';
    });

    removeBtn.addEventListener('click', () => {
      options.onRemove?.(item.id);
      itemDiv.style.animation = 'fadeOut 0.2s ease-in';
      setTimeout(() => itemDiv.remove(), 200);
    });

    actions.appendChild(removeBtn);

    itemDiv.addEventListener('mouseover', () => {
      actions.style.opacity = '1';
    });

    itemDiv.addEventListener('mouseout', () => {
      actions.style.opacity = '0';
    });

    itemDiv.addEventListener('click', () => {
      options.onPreview?.(item);
    });

    itemDiv.appendChild(icon);
    itemDiv.appendChild(info);
    itemDiv.appendChild(actions);
    itemsContainer.appendChild(itemDiv);
  });

  if (options.items.length === 0) {
    const empty = document.createElement('div');
    empty.style.cssText = `
      padding: 20px;
      text-align: center;
      color: var(--text-secondary);
      font-size: 12px;
    `;
    empty.textContent = 'No context items. Add files to get started.';
    itemsContainer.appendChild(empty);
  }

  container.appendChild(header);
  container.appendChild(itemsContainer);

  // Add animations
  const style = document.createElement('style');
  if (!document.head.querySelector('style[data-context-animations]')) {
    style.setAttribute('data-context-animations', 'true');
    style.textContent = `
      @keyframes fadeOut {
        from {
          opacity: 1;
          transform: translateX(0);
        }
        to {
          opacity: 0;
          transform: translateX(10px);
        }
      }
    `;
    document.head.appendChild(style);
  }

  return container;
}

export const ContextDisplay = {
  create: createContextDisplay,
};
