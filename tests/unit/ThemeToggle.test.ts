import { describe, it, expect, beforeEach, vi } from 'vitest';

type Theme = 'light' | 'dark' | 'auto';

class ThemeToggle {
  private theme: Theme = 'light';
  private onThemeChange: ((theme: Theme) => void) | null = null;

  getTheme(): Theme {
    return this.theme;
  }

  setTheme(theme: Theme): void {
    this.theme = theme;
    this.onThemeChange?.(theme);
  }

  toggle(): void {
    this.theme = this.theme === 'light' ? 'dark' : 'light';
    this.onThemeChange?.(this.theme);
  }

  isDark(): boolean {
    return this.theme === 'dark';
  }

  isLight(): boolean {
    return this.theme === 'light';
  }

  onThemeChanged(callback: (theme: Theme) => void): void {
    this.onThemeChange = callback;
  }

  getSystemTheme(): Theme {
    return 'light'; // Simulated
  }

  applyTheme(): void {
    // Apply theme to document
  }
}

describe('ThemeToggle', () => {
  let toggle: ThemeToggle;

  beforeEach(() => {
    toggle = new ThemeToggle();
  });

  it('should initialize with light theme', () => {
    expect(toggle.getTheme()).toBe('light');
  });

  it('should set theme', () => {
    toggle.setTheme('dark');
    expect(toggle.getTheme()).toBe('dark');
  });

  it('should toggle theme', () => {
    toggle.toggle();
    expect(toggle.getTheme()).toBe('dark');
    toggle.toggle();
    expect(toggle.getTheme()).toBe('light');
  });

  it('should detect dark mode', () => {
    toggle.setTheme('dark');
    expect(toggle.isDark()).toBe(true);
    expect(toggle.isLight()).toBe(false);
  });

  it('should detect light mode', () => {
    expect(toggle.isLight()).toBe(true);
    expect(toggle.isDark()).toBe(false);
  });

  it('should call onThemeChanged callback', () => {
    const callback = vi.fn();
    toggle.onThemeChanged(callback);
    toggle.setTheme('dark');
    expect(callback).toHaveBeenCalledWith('dark');
  });

  it('should handle auto theme', () => {
    toggle.setTheme('auto');
    expect(toggle.getTheme()).toBe('auto');
  });

  it('should apply theme', () => {
    expect(() => toggle.applyTheme()).not.toThrow();
  });

  it('should get system theme', () => {
    const systemTheme = toggle.getSystemTheme();
    expect(['light', 'dark', 'auto']).toContain(systemTheme);
  });
});
