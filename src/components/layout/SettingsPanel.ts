/**
 * SettingsPanel component - settings and preferences
 */

interface SettingsCategory {
  title: string;
  icon: string;
  id: string;
  items: SettingsItem[];
}

interface SettingsItem {
  label: string;
  type: 'toggle' | 'select' | 'text' | 'color';
  value?: string | boolean;
  onChange?: (value: any) => void;
}

export function createSettingsPanel(): HTMLDivElement {
  const panel = document.createElement('div');
  panel.className = 'settings-panel';

  panel.style.cssText = `
    display: flex;
    gap: 20px;
    padding: 20px;
    background-color: var(--bg);
    height: 100%;
    overflow: auto;
  `;

  // Sidebar navigation
  const nav = document.createElement('nav');
  nav.style.cssText = `
    width: 200px;
    display: flex;
    flex-direction: column;
    gap: 8px;
    flex-shrink: 0;
  `;

  const categories: SettingsCategory[] = [
    {
      title: 'General',
      icon: '⚙️',
      id: 'settings-general',
      items: [],
    },
    {
      title: 'Appearance',
      icon: '🎨',
      id: 'settings-appearance',
      items: [],
    },
    {
      title: 'API Keys',
      icon: '🔑',
      id: 'settings-keys',
      items: [],
    },
    {
      title: 'Models',
      icon: '🤖',
      id: 'settings-models',
      items: [],
    },
    {
      title: 'Advanced',
      icon: '⚡',
      id: 'settings-advanced',
      items: [],
    },
  ];

  categories.forEach((category, index) => {
    const navItem = document.createElement('button');
    navItem.className = 'settings-nav-item';
    navItem.id = category.id;
    navItem.style.cssText = `
      padding: 12px 16px;
      border: 1px solid ${index === 0 ? 'var(--accent)' : 'transparent'};
      background-color: ${index === 0 ? 'var(--accent)' : 'transparent'};
      color: ${index === 0 ? 'var(--bg)' : 'var(--text)'};
      border-radius: 6px;
      cursor: pointer;
      font-size: 14px;
      font-weight: 500;
      transition: all 0.2s;
      font-family: inherit;
      display: flex;
      align-items: center;
      gap: 10px;
      text-align: left;
    `;

    navItem.addEventListener('mouseover', () => {
      if (index !== 0) {
        navItem.style.backgroundColor = 'var(--border)';
      }
    });

    navItem.addEventListener('mouseout', () => {
      if (index !== 0) {
        navItem.style.backgroundColor = 'transparent';
      }
    });

    const icon = document.createElement('span');
    icon.textContent = category.icon;

    const label = document.createElement('span');
    label.textContent = category.title;

    navItem.appendChild(icon);
    navItem.appendChild(label);
    nav.appendChild(navItem);
  });

  // Content area
  const content = document.createElement('div');
  content.style.cssText = `
    flex: 1;
    display: flex;
    flex-direction: column;
    gap: 24px;
    max-width: 600px;
  `;

  // General settings content
  const generalContent = document.createElement('div');
  generalContent.style.cssText = `
    display: flex;
    flex-direction: column;
    gap: 16px;
  `;

  const heading = document.createElement('h2');
  heading.textContent = 'General Settings';
  heading.style.cssText = `
    margin: 0 0 12px 0;
    font-size: 18px;
    font-weight: 600;
    color: var(--text);
  `;

  const description = document.createElement('p');
  description.textContent = 'Configure your DevForge workspace settings';
  description.style.cssText = `
    margin: 0;
    font-size: 13px;
    color: var(--text-secondary);
  `;

  generalContent.appendChild(heading);
  generalContent.appendChild(description);

  // Settings items
  const settingsItems = [
    { label: 'Auto-save changes', type: 'toggle' },
    { label: 'Show line numbers', type: 'toggle' },
    { label: 'Font size', type: 'select' },
  ];

  settingsItems.forEach((item) => {
    const itemDiv = document.createElement('div');
    itemDiv.style.cssText = `
      display: flex;
      justify-content: space-between;
      align-items: center;
      padding: 12px;
      background-color: var(--panel);
      border-radius: 6px;
      border: 1px solid var(--border);
    `;

    const label = document.createElement('label');
    label.textContent = item.label;
    label.style.cssText = `
      color: var(--text);
      font-size: 14px;
      cursor: pointer;
    `;

    let control: HTMLElement;

    if (item.type === 'toggle') {
      control = document.createElement('input');
      (control as HTMLInputElement).type = 'checkbox';
      (control as HTMLInputElement).checked = true;
      control.style.cssText = `
        cursor: pointer;
        width: 18px;
        height: 18px;
      `;
    } else {
      control = document.createElement('select');
      (control as HTMLSelectElement).innerHTML = '<option>14px</option><option>16px</option><option>18px</option>';
      control.style.cssText = `
        padding: 6px 10px;
        border: 1px solid var(--border);
        background-color: var(--input-bg);
        color: var(--text);
        border-radius: 4px;
        cursor: pointer;
        font-size: 13px;
        font-family: inherit;
      `;
    }

    itemDiv.appendChild(label);
    itemDiv.appendChild(control);
    generalContent.appendChild(itemDiv);
  });

  content.appendChild(generalContent);
  panel.appendChild(nav);
  panel.appendChild(content);

  return panel;
}

export const SettingsPanel = {
  create: createSettingsPanel,
};
