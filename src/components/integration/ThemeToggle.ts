/**
 * ThemeToggle component - switch between dark and light themes
 */

export type Theme = 'dark' | 'light' | 'auto';

export interface ThemeToggleOptions {
  initialTheme?: Theme;
  onThemeChange?: (theme: Theme) => void;
  position?: 'fixed' | 'inline';
}

export function createThemeToggle(options?: ThemeToggleOptions): HTMLDivElement {
  const container = document.createElement('div');
  container.className = 'theme-toggle';

  const position = options?.position || 'inline';
  if (position === 'fixed') {
    container.style.cssText = `
      position: fixed;
      top: 20px;
      right: 20px;
      z-index: 100;
    `;
  }

  // Get system preference
  const systemPrefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
  const savedTheme = localStorage.getItem('devforge-theme') as Theme;
  let currentTheme: Theme = options?.initialTheme || savedTheme || 'auto';

  const applyTheme = (theme: Theme) => {
    let actualTheme: 'dark' | 'light';

    if (theme === 'auto') {
      actualTheme = systemPrefersDark ? 'dark' : 'light';
    } else {
      actualTheme = theme;
    }

    document.documentElement.setAttribute('data-theme', actualTheme);
    localStorage.setItem('devforge-theme', theme);
    currentTheme = theme;

    updateButton();
    options?.onThemeChange?.(theme);
  };

  // Button container
  const buttonContainer = document.createElement('div');
  buttonContainer.style.cssText = `
    display: flex;
    align-items: center;
    gap: 4px;
    padding: 6px;
    background-color: var(--panel);
    border: 1px solid var(--border);
    border-radius: 6px;
  `;

  // Buttons for each theme
  const themes: Theme[] = ['auto', 'light', 'dark'];
  const icons: { [key in Theme]: string } = {
    auto: '🔄',
    light: '☀️',
    dark: '🌙',
  };

  const buttons: { [key in Theme]: HTMLButtonElement } = {} as any;

  const updateButton = () => {
    (Object.keys(buttons) as Theme[]).forEach((theme) => {
      const btn = buttons[theme];
      if (theme === currentTheme) {
        btn.style.backgroundColor = 'var(--accent)';
        btn.style.color = 'var(--bg)';
      } else {
        btn.style.backgroundColor = 'transparent';
        btn.style.color = 'var(--text)';
      }
    });
  };

  themes.forEach((theme) => {
    const btn = document.createElement('button');
    btn.className = `theme-btn theme-${theme}`;
    btn.title = `${theme.charAt(0).toUpperCase() + theme.slice(1)} mode`;
    btn.textContent = icons[theme];

    btn.style.cssText = `
      padding: 6px 10px;
      border: none;
      background-color: transparent;
      color: var(--text);
      cursor: pointer;
      font-size: 16px;
      border-radius: 4px;
      transition: all 0.2s;
      font-family: inherit;
    `;

    btn.addEventListener('click', () => {
      applyTheme(theme);
    });

    btn.addEventListener('mouseover', () => {
      if (theme !== currentTheme) {
        btn.style.backgroundColor = 'var(--border)';
      }
    });

    btn.addEventListener('mouseout', () => {
      if (theme !== currentTheme) {
        btn.style.backgroundColor = 'transparent';
      }
    });

    buttons[theme] = btn;
    buttonContainer.appendChild(btn);
  });

  container.appendChild(buttonContainer);

  // Listen for system theme changes
  const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)');
  const handleChange = () => {
    if (currentTheme === 'auto') {
      applyTheme('auto');
    }
  };

  mediaQuery.addEventListener('change', handleChange);

  // Apply initial theme
  applyTheme(currentTheme);

  // Expose methods
  (container as any).getTheme = () => currentTheme;
  (container as any).setTheme = (theme: Theme) => {
    applyTheme(theme);
  };
  (container as any).toggleTheme = () => {
    const themes: Theme[] = ['auto', 'light', 'dark'];
    const currentIndex = themes.indexOf(currentTheme);
    const nextIndex = (currentIndex + 1) % themes.length;
    applyTheme(themes[nextIndex]);
  };

  return container;
}

export const ThemeToggle = {
  create: createThemeToggle,
};
