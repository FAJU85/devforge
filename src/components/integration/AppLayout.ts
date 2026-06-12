/**
 * AppLayout component - main application layout combining all sections
 */

export interface AppLayoutOptions {
  showSidebar?: boolean;
  showContextPanel?: boolean;
  onToggleSidebar?: (visible: boolean) => void;
  onToggleContext?: (visible: boolean) => void;
}

export function createAppLayout(options?: AppLayoutOptions): HTMLDivElement {
  const layout = document.createElement('div');
  layout.className = 'app-layout';

  layout.style.cssText = `
    display: flex;
    width: 100vw;
    height: 100vh;
    background-color: var(--bg);
    overflow: hidden;
  `;

  // Sidebar section
  const sidebarSection = document.createElement('div');
  sidebarSection.className = 'sidebar-section';
  sidebarSection.style.cssText = `
    width: 280px;
    height: 100vh;
    background-color: var(--panel);
    border-right: 1px solid var(--border);
    display: flex;
    flex-direction: column;
    transition: width 0.3s ease;
    overflow-y: auto;
  `;

  if (options?.showSidebar === false) {
    sidebarSection.style.width = '0';
    sidebarSection.style.borderRight = 'none';
  }

  // Main content section
  const mainSection = document.createElement('div');
  mainSection.className = 'main-section';
  mainSection.style.cssText = `
    flex: 1;
    display: flex;
    flex-direction: column;
    overflow: hidden;
  `;

  // Top toolbar
  const toolbar = document.createElement('div');
  toolbar.className = 'app-toolbar';
  toolbar.style.cssText = `
    height: 50px;
    background-color: var(--panel);
    border-bottom: 1px solid var(--border);
    display: flex;
    align-items: center;
    padding: 0 16px;
    gap: 12px;
  `;

  // Toggle sidebar button
  const toggleSidebar = document.createElement('button');
  toggleSidebar.textContent = '☰';
  toggleSidebar.style.cssText = `
    background: none;
    border: none;
    color: var(--text);
    font-size: 18px;
    cursor: pointer;
    padding: 4px 8px;
    transition: color 0.2s;
  `;

  toggleSidebar.addEventListener('mouseover', () => {
    toggleSidebar.style.color = 'var(--accent)';
  });

  toggleSidebar.addEventListener('mouseout', () => {
    toggleSidebar.style.color = 'var(--text)';
  });

  let sidebarVisible = options?.showSidebar !== false;
  toggleSidebar.addEventListener('click', () => {
    sidebarVisible = !sidebarVisible;
    sidebarSection.style.width = sidebarVisible ? '280px' : '0';
    sidebarSection.style.borderRight = sidebarVisible ? '1px solid var(--border)' : 'none';
    options?.onToggleSidebar?.(sidebarVisible);
  });

  // Breadcrumb area
  const breadcrumb = document.createElement('div');
  breadcrumb.className = 'app-breadcrumb';
  breadcrumb.style.cssText = `
    flex: 1;
    display: flex;
    align-items: center;
    gap: 8px;
    font-size: 13px;
    color: var(--text-secondary);
  `;
  breadcrumb.textContent = '📂 DevForge';

  // Theme toggle
  const themeToggle = document.createElement('button');
  themeToggle.textContent = '🌙';
  themeToggle.title = 'Toggle theme';
  themeToggle.style.cssText = `
    background: none;
    border: 1px solid var(--border);
    color: var(--text);
    font-size: 16px;
    cursor: pointer;
    padding: 6px 10px;
    border-radius: 4px;
    transition: all 0.2s;
  `;

  themeToggle.addEventListener('mouseover', () => {
    themeToggle.style.backgroundColor = 'var(--border)';
  });

  themeToggle.addEventListener('mouseout', () => {
    themeToggle.style.backgroundColor = 'transparent';
  });

  let isDark = true;
  themeToggle.addEventListener('click', () => {
    isDark = !isDark;
    const html = document.documentElement;
    html.setAttribute('data-theme', isDark ? 'dark' : 'light');
    themeToggle.textContent = isDark ? '🌙' : '☀️';
  });

  toolbar.appendChild(toggleSidebar);
  toolbar.appendChild(breadcrumb);
  toolbar.appendChild(themeToggle);

  // Content and context area
  const contentWrapper = document.createElement('div');
  contentWrapper.className = 'content-wrapper';
  contentWrapper.style.cssText = `
    flex: 1;
    display: grid;
    grid-template-columns: 1fr 300px;
    gap: 0;
    overflow: hidden;
  `;

  // Main content
  const mainContent = document.createElement('div');
  mainContent.className = 'main-content';
  mainContent.style.cssText = `
    display: flex;
    flex-direction: column;
    overflow: auto;
    background-color: var(--bg);
  `;

  const placeholder = document.createElement('div');
  placeholder.style.cssText = `
    padding: 20px;
    color: var(--text-secondary);
    display: flex;
    align-items: center;
    justify-content: center;
    height: 100%;
    font-size: 14px;
  `;
  placeholder.textContent = 'Main content area';

  mainContent.appendChild(placeholder);

  // Context panel
  const contextPanel = document.createElement('div');
  contextPanel.className = 'context-panel';
  contextPanel.style.cssText = `
    width: 300px;
    background-color: var(--panel);
    border-left: 1px solid var(--border);
    overflow-y: auto;
    padding: 12px;
    transition: width 0.3s ease;
  `;

  if (options?.showContextPanel === false) {
    contextPanel.style.width = '0';
    contextPanel.style.borderLeft = 'none';
    contextPanel.style.padding = '0';
  }

  const contextTitle = document.createElement('h3');
  contextTitle.textContent = 'Context';
  contextTitle.style.cssText = `
    margin: 0 0 12px 0;
    font-size: 13px;
    font-weight: 600;
    color: var(--text);
  `;

  contextPanel.appendChild(contextTitle);

  contentWrapper.appendChild(mainContent);
  contentWrapper.appendChild(contextPanel);

  // Status bar
  const statusBar = document.createElement('div');
  statusBar.className = 'status-bar';
  statusBar.style.cssText = `
    height: 30px;
    background-color: var(--panel);
    border-top: 1px solid var(--border);
    display: flex;
    align-items: center;
    padding: 0 16px;
    gap: 20px;
    font-size: 11px;
    color: var(--text-secondary);
  `;

  const statusLeft = document.createElement('div');
  statusLeft.textContent = '✓ Ready';
  statusLeft.style.cssText = `color: var(--green);`;

  const statusRight = document.createElement('div');
  statusRight.style.cssText = `margin-left: auto;`;
  statusRight.textContent = 'Line 1, Col 1';

  statusBar.appendChild(statusLeft);
  statusBar.appendChild(statusRight);

  mainSection.appendChild(toolbar);
  mainSection.appendChild(contentWrapper);
  mainSection.appendChild(statusBar);

  layout.appendChild(sidebarSection);
  layout.appendChild(mainSection);

  // Expose methods
  (layout as any).getSidebar = () => sidebarSection;
  (layout as any).getMainContent = () => mainContent;
  (layout as any).getContextPanel = () => contextPanel;
  (layout as any).toggleSidebar = (visible: boolean) => {
    sidebarVisible = visible;
    sidebarSection.style.width = visible ? '280px' : '0';
    sidebarSection.style.borderRight = visible ? '1px solid var(--border)' : 'none';
  };

  return layout;
}

export const AppLayout = {
  create: createAppLayout,
};
