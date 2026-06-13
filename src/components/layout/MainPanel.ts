/**
 * MainPanel component - central content area
 */

export function createMainPanel(): HTMLDivElement {
  const mainPanel = document.createElement('div');
  mainPanel.className = 'main-panel';

  mainPanel.style.cssText = `
    display: flex;
    flex-direction: column;
    flex: 1;
    height: 100vh;
    background-color: var(--bg);
    overflow: hidden;
  `;

  // Top bar with tabs
  const topBar = document.createElement('div');
  topBar.style.cssText = `
    display: flex;
    align-items: center;
    padding: 12px 20px;
    border-bottom: 1px solid var(--border);
    background-color: var(--panel);
    gap: 12px;
    overflow-x: auto;
  `;

  const tabContainer = document.createElement('div');
  tabContainer.style.cssText = `
    display: flex;
    gap: 4px;
    flex: 1;
  `;

  // Default tabs
  const tabs = ['Chat', 'Repository', 'Debug'];
  tabs.forEach((tabName, index) => {
    const tab = document.createElement('button');
    tab.className = 'main-tab';
    tab.textContent = tabName;
    tab.style.cssText = `
      padding: 8px 16px;
      border: 1px solid var(--border);
      background-color: ${index === 0 ? 'var(--accent)' : 'transparent'};
      color: ${index === 0 ? 'var(--bg)' : 'var(--text)'};
      border-radius: 4px;
      cursor: pointer;
      font-size: 13px;
      font-weight: 500;
      transition: all 0.2s;
      font-family: inherit;
      white-space: nowrap;
    `;

    tab.addEventListener('mouseover', () => {
      if (index !== 0) {
        tab.style.backgroundColor = 'var(--border)';
      }
    });

    tab.addEventListener('mouseout', () => {
      if (index !== 0) {
        tab.style.backgroundColor = 'transparent';
      }
    });

    tab.addEventListener('click', () => {
      document.querySelectorAll('.main-tab').forEach((t) => {
        if (t instanceof HTMLElement) {
          t.style.backgroundColor = 'transparent';
          t.style.color = 'var(--text)';
        }
      });
      tab.style.backgroundColor = 'var(--accent)';
      tab.style.color = 'var(--bg)';
    });

    tabContainer.appendChild(tab);
  });

  topBar.appendChild(tabContainer);

  // Content area
  const contentArea = document.createElement('div');
  contentArea.className = 'content-area';
  contentArea.style.cssText = `
    flex: 1;
    overflow: auto;
    padding: 20px;
    display: flex;
    flex-direction: column;
    gap: 16px;
  `;

  // Placeholder content
  const placeholder = document.createElement('div');
  placeholder.style.cssText = `
    display: flex;
    align-items: center;
    justify-content: center;
    height: 100%;
    color: var(--text-secondary);
    font-size: 16px;
  `;
  placeholder.textContent = 'Select a tab to get started';

  contentArea.appendChild(placeholder);

  mainPanel.appendChild(topBar);
  mainPanel.appendChild(contentArea);

  return mainPanel;
}

export const MainPanel = {
  create: createMainPanel,
};
