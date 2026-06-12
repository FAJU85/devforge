/**
 * ContextInfo component - displays context statistics and metadata
 */

export interface ContextStats {
  filesCount: number;
  totalLines: number;
  totalTokens: number;
  maxTokens?: number;
  languages?: { [key: string]: number };
  lastUpdated?: Date;
}

export interface ContextInfoOptions {
  stats: ContextStats;
  onClear?: () => void;
  onExport?: () => void;
}

export function createContextInfo(options: ContextInfoOptions): HTMLDivElement {
  const container = document.createElement('div');
  container.className = 'context-info';

  container.style.cssText = `
    display: flex;
    flex-direction: column;
    gap: 12px;
    padding: 16px;
    background-color: var(--panel);
    border-radius: 6px;
    border: 1px solid var(--border);
  `;

  // Title
  const title = document.createElement('h3');
  title.textContent = 'Context Info';
  title.style.cssText = `
    margin: 0 0 8px 0;
    font-size: 13px;
    font-weight: 600;
    color: var(--text);
  `;

  // Stats grid
  const statsGrid = document.createElement('div');
  statsGrid.style.cssText = `
    display: grid;
    grid-template-columns: repeat(2, 1fr);
    gap: 12px;
  `;

  const stats = [
    { label: 'Files', value: options.stats.filesCount, icon: '📁' },
    { label: 'Lines', value: options.stats.totalLines, icon: '📝' },
    { label: 'Tokens', value: options.stats.totalTokens, icon: '🔢' },
  ];

  stats.forEach((stat) => {
    const statDiv = document.createElement('div');
    statDiv.style.cssText = `
      display: flex;
      flex-direction: column;
      gap: 6px;
      padding: 10px;
      background-color: var(--bg);
      border-radius: 4px;
      border: 1px solid var(--border);
    `;

    const label = document.createElement('div');
    label.style.cssText = `
      font-size: 10px;
      color: var(--text-secondary);
      text-transform: uppercase;
      letter-spacing: 0.5px;
    `;
    label.textContent = stat.label;

    const value = document.createElement('div');
    value.style.cssText = `
      font-size: 16px;
      font-weight: 600;
      color: var(--text);
    `;
    value.textContent = `${stat.icon} ${typeof stat.value === 'number' ? stat.value.toLocaleString() : stat.value}`;

    statDiv.appendChild(label);
    statDiv.appendChild(value);
    statsGrid.appendChild(statDiv);
  });

  // Languages
  if (options.stats.languages && Object.keys(options.stats.languages).length > 0) {
    const langSection = document.createElement('div');
    langSection.style.cssText = `
      display: flex;
      flex-direction: column;
      gap: 6px;
      padding-top: 8px;
      border-top: 1px solid var(--border);
    `;

    const langLabel = document.createElement('div');
    langLabel.style.cssText = `
      font-size: 11px;
      color: var(--text-secondary);
      text-transform: uppercase;
      letter-spacing: 0.5px;
      font-weight: 600;
    `;
    langLabel.textContent = 'Languages';

    langSection.appendChild(langLabel);

    const langTags = document.createElement('div');
    langTags.style.cssText = `
      display: flex;
      flex-wrap: wrap;
      gap: 6px;
    `;

    Object.entries(options.stats.languages).forEach(([lang, count]) => {
      const tag = document.createElement('span');
      tag.style.cssText = `
        padding: 4px 8px;
        background-color: var(--accent);
        color: var(--bg);
        border-radius: 3px;
        font-size: 10px;
        font-weight: 500;
      `;
      tag.textContent = `${lang} (${count})`;
      langTags.appendChild(tag);
    });

    langSection.appendChild(langTags);
    statsGrid.appendChild(langSection);
  }

  // Token usage bar
  if (options.stats.maxTokens) {
    const percentage = (options.stats.totalTokens / options.stats.maxTokens) * 100;

    const tokenSection = document.createElement('div');
    tokenSection.style.cssText = `
      display: flex;
      flex-direction: column;
      gap: 6px;
      padding-top: 8px;
      border-top: 1px solid var(--border);
    `;

    const tokenLabel = document.createElement('div');
    tokenLabel.style.cssText = `
      display: flex;
      justify-content: space-between;
      font-size: 11px;
      color: var(--text-secondary);
    `;

    const labelText = document.createElement('span');
    labelText.textContent = 'Token Usage';

    const percentage_text = document.createElement('span');
    percentage_text.textContent = `${percentage.toFixed(1)}%`;

    tokenLabel.appendChild(labelText);
    tokenLabel.appendChild(percentage_text);

    const bar = document.createElement('div');
    bar.style.cssText = `
      width: 100%;
      height: 6px;
      background-color: var(--border);
      border-radius: 3px;
      overflow: hidden;
    `;

    const fill = document.createElement('div');
    fill.style.cssText = `
      height: 100%;
      background-color: ${percentage < 70 ? 'var(--green)' : percentage < 90 ? 'var(--yellow)' : 'var(--red)'};
      width: ${percentage}%;
      transition: width 0.3s ease;
    `;

    bar.appendChild(fill);

    tokenSection.appendChild(tokenLabel);
    tokenSection.appendChild(bar);
    statsGrid.appendChild(tokenSection);
  }

  // Last updated
  if (options.stats.lastUpdated) {
    const updated = document.createElement('div');
    updated.style.cssText = `
      font-size: 10px;
      color: var(--text-secondary);
      padding-top: 8px;
      border-top: 1px solid var(--border);
    `;
    updated.textContent = `Updated: ${options.stats.lastUpdated.toLocaleString()}`;
    statsGrid.appendChild(updated);
  }

  // Actions
  const actions = document.createElement('div');
  actions.style.cssText = `
    display: flex;
    gap: 8px;
    padding-top: 8px;
    border-top: 1px solid var(--border);
  `;

  if (options.onClear) {
    const clearBtn = document.createElement('button');
    clearBtn.textContent = '🗑️ Clear';
    clearBtn.style.cssText = `
      flex: 1;
      padding: 6px 12px;
      border: 1px solid var(--border);
      border-radius: 4px;
      background-color: transparent;
      color: var(--text);
      cursor: pointer;
      font-size: 11px;
      font-weight: 500;
      transition: all 0.2s;
      font-family: inherit;
    `;

    clearBtn.addEventListener('mouseover', () => {
      clearBtn.style.backgroundColor = 'var(--red)';
      clearBtn.style.color = 'white';
    });

    clearBtn.addEventListener('mouseout', () => {
      clearBtn.style.backgroundColor = 'transparent';
      clearBtn.style.color = 'var(--text)';
    });

    clearBtn.addEventListener('click', () => {
      options.onClear?.();
    });

    actions.appendChild(clearBtn);
  }

  if (options.onExport) {
    const exportBtn = document.createElement('button');
    exportBtn.textContent = '📤 Export';
    exportBtn.style.cssText = `
      flex: 1;
      padding: 6px 12px;
      border: 1px solid var(--border);
      border-radius: 4px;
      background-color: transparent;
      color: var(--text);
      cursor: pointer;
      font-size: 11px;
      font-weight: 500;
      transition: all 0.2s;
      font-family: inherit;
    `;

    exportBtn.addEventListener('mouseover', () => {
      exportBtn.style.backgroundColor = 'var(--accent)';
      exportBtn.style.color = 'var(--bg)';
    });

    exportBtn.addEventListener('mouseout', () => {
      exportBtn.style.backgroundColor = 'transparent';
      exportBtn.style.color = 'var(--text)';
    });

    exportBtn.addEventListener('click', () => {
      options.onExport?.();
    });

    actions.appendChild(exportBtn);
  }

  container.appendChild(title);
  container.appendChild(statsGrid);
  if (actions.children.length > 0) {
    container.appendChild(actions);
  }

  // Expose methods
  (container as any).updateStats = (stats: ContextStats) => {
    // Would update the display with new stats
    statsGrid.innerHTML = '';
    // Re-render stats...
  };

  return container;
}

export const ContextInfo = {
  create: createContextInfo,
};
