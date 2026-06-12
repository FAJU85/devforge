/**
 * StatusBar component - bottom status display with current state
 */

export interface StatusItem {
  id: string;
  label: string;
  icon?: string;
  value?: string;
  color?: 'success' | 'warning' | 'error' | 'info';
  onClick?: () => void;
}

export interface StatusBarOptions {
  items?: StatusItem[];
  onItemClick?: (id: string) => void;
}

export function createStatusBar(options?: StatusBarOptions): HTMLDivElement {
  const bar = document.createElement('div');
  bar.className = 'status-bar';

  bar.style.cssText = `
    height: 32px;
    background-color: var(--panel);
    border-top: 1px solid var(--border);
    display: flex;
    align-items: center;
    padding: 0 16px;
    gap: 16px;
    font-size: 11px;
    color: var(--text-secondary);
  `;

  const defaultItems: StatusItem[] = [
    { id: 'status', label: 'Ready', icon: '✓', color: 'success' },
    { id: 'tokens', label: 'Tokens', value: '0/4096', color: 'info' },
    { id: 'line', label: 'Line', value: '1', color: 'info' },
    { id: 'col', label: 'Col', value: '1', color: 'info' },
  ];

  const itemsToDisplay = options?.items || defaultItems;

  itemsToDisplay.forEach((item) => {
    const itemDiv = document.createElement('button');
    itemDiv.className = `status-item status-${item.color || 'info'}`;

    const colors = {
      success: 'var(--green)',
      warning: 'var(--yellow)',
      error: 'var(--red)',
      info: 'var(--text-secondary)',
    };

    itemDiv.style.cssText = `
      display: flex;
      align-items: center;
      gap: 6px;
      background: none;
      border: none;
      color: ${colors[item.color || 'info']};
      cursor: pointer;
      font-size: 11px;
      font-family: inherit;
      transition: opacity 0.2s;
    `;

    if (item.icon) {
      const icon = document.createElement('span');
      icon.textContent = item.icon;
      itemDiv.appendChild(icon);
    }

    const label = document.createElement('span');
    label.textContent = item.label;

    if (item.value) {
      const value = document.createElement('span');
      value.textContent = item.value;
      value.style.fontWeight = '500';
      value.style.color = colors[item.color || 'info'];

      itemDiv.appendChild(label);
      itemDiv.appendChild(document.createTextNode(': '));
      itemDiv.appendChild(value);
    } else {
      itemDiv.appendChild(label);
    }

    itemDiv.addEventListener('mouseover', () => {
      itemDiv.style.opacity = '0.8';
    });

    itemDiv.addEventListener('mouseout', () => {
      itemDiv.style.opacity = '1';
    });

    itemDiv.addEventListener('click', () => {
      item.onClick?.();
      options?.onItemClick?.(item.id);
    });

    bar.appendChild(itemDiv);
  });

  // Right-side info
  const rightSection = document.createElement('div');
  rightSection.style.cssText = `
    margin-left: auto;
    display: flex;
    align-items: center;
    gap: 16px;
  `;

  const time = document.createElement('span');
  time.style.cssText = `
    color: var(--text-secondary);
  `;

  const updateTime = () => {
    const now = new Date();
    time.textContent = now.toLocaleTimeString([], {
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  updateTime();
  setInterval(updateTime, 1000);

  rightSection.appendChild(time);
  bar.appendChild(rightSection);

  // Expose methods
  (bar as any).setStatus = (id: string, value: string, color?: string) => {
    const item = bar.querySelector(`[data-id="${id}"]`) as HTMLElement;
    if (item) {
      item.textContent = value;
    }
  };

  (bar as any).updateItems = (items: StatusItem[]) => {
    bar.innerHTML = '';
    items.forEach((item) => {
      const itemDiv = document.createElement('div');
      itemDiv.setAttribute('data-id', item.id);
      itemDiv.textContent = `${item.label}: ${item.value || ''}`;
      itemDiv.style.cssText = `
        display: flex;
        align-items: center;
        gap: 6px;
        font-size: 11px;
      `;
      bar.appendChild(itemDiv);
    });
  };

  return bar;
}

export const StatusBar = {
  create: createStatusBar,
};
