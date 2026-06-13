import { describe, it, expect, beforeEach, vi } from 'vitest';

interface SidebarItem {
  id: string;
  label: string;
  icon?: string;
  active?: boolean;
}

class Sidebar {
  private items: SidebarItem[] = [];
  private collapsed: boolean = false;
  private onItemClick: ((itemId: string) => void) | null = null;

  addItem(item: SidebarItem): void {
    if (!this.items.find(i => i.id === item.id)) {
      this.items.push(item);
    }
  }

  getItems(): SidebarItem[] {
    return [...this.items];
  }

  removeItem(itemId: string): boolean {
    const index = this.items.findIndex(i => i.id === itemId);
    if (index > -1) {
      this.items.splice(index, 1);
      return true;
    }
    return false;
  }

  selectItem(itemId: string): void {
    this.items.forEach(item => {
      item.active = item.id === itemId;
    });
    this.onItemClick?.(itemId);
  }

  getSelectedItem(): SidebarItem | undefined {
    return this.items.find(i => i.active);
  }

  toggle(): void {
    this.collapsed = !this.collapsed;
  }

  isCollapsed(): boolean {
    return this.collapsed;
  }

  onItemSelected(callback: (itemId: string) => void): void {
    this.onItemClick = callback;
  }

  clear(): void {
    this.items = [];
  }
}

describe('Sidebar', () => {
  let sidebar: Sidebar;

  beforeEach(() => {
    sidebar = new Sidebar();
  });

  it('should initialize', () => {
    expect(sidebar.getItems()).toHaveLength(0);
    expect(sidebar.isCollapsed()).toBe(false);
  });

  it('should add items', () => {
    sidebar.addItem({ id: 'home', label: 'Home' });
    expect(sidebar.getItems()).toHaveLength(1);
  });

  it('should remove items', () => {
    sidebar.addItem({ id: 'home', label: 'Home' });
    expect(sidebar.removeItem('home')).toBe(true);
    expect(sidebar.getItems()).toHaveLength(0);
  });

  it('should select item', () => {
    sidebar.addItem({ id: 'home', label: 'Home' });
    sidebar.selectItem('home');
    expect(sidebar.getSelectedItem()?.id).toBe('home');
  });

  it('should call onItemClick', () => {
    const callback = vi.fn();
    sidebar.addItem({ id: 'home', label: 'Home' });
    sidebar.onItemSelected(callback);
    sidebar.selectItem('home');
    expect(callback).toHaveBeenCalledWith('home');
  });

  it('should toggle collapse', () => {
    sidebar.toggle();
    expect(sidebar.isCollapsed()).toBe(true);
    sidebar.toggle();
    expect(sidebar.isCollapsed()).toBe(false);
  });

  it('should clear items', () => {
    sidebar.addItem({ id: 'home', label: 'Home' });
    sidebar.clear();
    expect(sidebar.getItems()).toHaveLength(0);
  });
});
