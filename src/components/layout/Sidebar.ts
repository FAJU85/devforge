/**
 * Sidebar component - main navigation and project explorer
 */

export function createSidebar(): HTMLDivElement {
  const sidebar = document.createElement('div');
  sidebar.className = 'sidebar';

  sidebar.style.cssText = `
    display: flex;
    flex-direction: column;
    width: 280px;
    height: 100vh;
    background-color: var(--panel);
    border-right: 1px solid var(--border);
    overflow-y: auto;
    transition: width 0.3s ease;
  `;

  // Header section
  const header = document.createElement('div');
  header.style.cssText = `
    padding: 16px;
    border-bottom: 1px solid var(--border);
    display: flex;
    align-items: center;
    gap: 12px;
  `;

  const logo = document.createElement('div');
  logo.textContent = '⚡';
  logo.style.cssText = `
    font-size: 24px;
    font-weight: bold;
  `;

  const title = document.createElement('span');
  title.textContent = 'DevForge';
  title.style.cssText = `
    font-size: 16px;
    font-weight: 600;
    color: var(--text);
  `;

  header.appendChild(logo);
  header.appendChild(title);

  // Navigation menu
  const nav = document.createElement('nav');
  nav.style.cssText = `
    flex: 1;
    padding: 16px 0;
    display: flex;
    flex-direction: column;
    gap: 4px;
  `;

  const menuItems = [
    { icon: '💬', label: 'Chat', id: 'nav-chat' },
    { icon: '📁', label: 'Repository', id: 'nav-repo' },
    { icon: '⚙️', label: 'Configuration', id: 'nav-config' },
    { icon: '🔧', label: 'Tools', id: 'nav-tools' },
    { icon: '📊', label: 'Analytics', id: 'nav-analytics' },
  ];

  let activeMenuItem: HTMLButtonElement | null = null;

  // Set first item as active by default
  menuItems.forEach((item, index) => {
    const menuItem = document.createElement('button');
    menuItem.id = item.id;
    menuItem.style.cssText = `
      padding: 12px 16px;
      border: none;
      background: none;
      color: var(--text);
      cursor: pointer;
      display: flex;
      align-items: center;
      gap: 12px;
      font-size: 14px;
      transition: all 0.2s;
      font-family: inherit;
      text-align: left;
      border-left: 3px solid transparent;
    `;

    // Make first item active by default
    const isActive = index === 0;
    if (isActive) {
      menuItem.style.backgroundColor = 'var(--accent-dim)';
      menuItem.style.borderLeftColor = 'var(--accent)';
      menuItem.style.color = 'var(--accent)';
      activeMenuItem = menuItem;
    }

    menuItem.addEventListener('mouseover', () => {
      if (menuItem !== activeMenuItem) {
        menuItem.style.backgroundColor = 'var(--border)';
      }
    });

    menuItem.addEventListener('mouseout', () => {
      if (menuItem !== activeMenuItem) {
        menuItem.style.backgroundColor = 'transparent';
      }
    });

    // Add click handler to set active state
    menuItem.addEventListener('click', () => {
      if (activeMenuItem) {
        activeMenuItem.style.backgroundColor = 'transparent';
        activeMenuItem.style.borderLeftColor = 'transparent';
        activeMenuItem.style.color = 'var(--text)';
      }
      menuItem.style.backgroundColor = 'var(--accent-dim)';
      menuItem.style.borderLeftColor = 'var(--accent)';
      menuItem.style.color = 'var(--accent)';
      activeMenuItem = menuItem;
    });

    // Add keyboard navigation support
    menuItem.addEventListener('keydown', (e) => {
      const buttons = Array.from(nav.querySelectorAll('button'));
      const currentIndex = buttons.indexOf(menuItem);

      if (e.key === 'ArrowDown' && currentIndex < buttons.length - 1) {
        e.preventDefault();
        (buttons[currentIndex + 1] as HTMLButtonElement).focus();
      } else if (e.key === 'ArrowUp' && currentIndex > 0) {
        e.preventDefault();
        (buttons[currentIndex - 1] as HTMLButtonElement).focus();
      }
    });

    const icon = document.createElement('span');
    icon.textContent = item.icon;
    icon.style.fontSize = '18px';

    const label = document.createElement('span');
    label.textContent = item.label;

    menuItem.appendChild(icon);
    menuItem.appendChild(label);
    nav.appendChild(menuItem);
  });

  // Footer section
  const footer = document.createElement('div');
  footer.style.cssText = `
    padding: 16px;
    border-top: 1px solid var(--border);
    display: flex;
    flex-direction: column;
    gap: 8px;
  `;

  const settingsBtn = document.createElement('button');
  settingsBtn.id = 'sidebar-settings';
  settingsBtn.style.cssText = `
    padding: 10px 12px;
    border: 1px solid var(--border);
    background: none;
    color: var(--text);
    cursor: pointer;
    border-radius: 6px;
    font-size: 13px;
    transition: all 0.2s;
    font-family: inherit;
    display: flex;
    align-items: center;
    gap: 8px;
  `;

  settingsBtn.addEventListener('mouseover', () => {
    settingsBtn.style.backgroundColor = 'var(--border)';
  });

  settingsBtn.addEventListener('mouseout', () => {
    settingsBtn.style.backgroundColor = 'transparent';
  });

  settingsBtn.textContent = '⚙️ Settings';

  footer.appendChild(settingsBtn);
  sidebar.appendChild(header);
  sidebar.appendChild(nav);
  sidebar.appendChild(footer);

  return sidebar;
}

export const Sidebar = {
  create: createSidebar,
};
