import { describe, it, expect, beforeEach, vi } from 'vitest';

interface ContextItem {
  id: string;
  type: 'file' | 'directory' | 'symbol';
  path: string;
  content?: string;
  relevance: number;
}

class ContextDisplay {
  private context: ContextItem[] = [];
  private selectedItems: Set<string> = new Set();
  private expandedItems: Set<string> = new Set();
  private onSelectionChange: ((selected: string[]) => void) | null = null;

  addItem(item: ContextItem): void {
    if (!this.context.find(c => c.id === item.id)) {
      this.context.push(item);
    }
  }

  removeItem(id: string): boolean {
    const index = this.context.findIndex(c => c.id === id);
    if (index > -1) {
      this.context.splice(index, 1);
      this.selectedItems.delete(id);
      return true;
    }
    return false;
  }

  getContext(): ContextItem[] {
    return [...this.context];
  }

  selectItem(id: string): void {
    this.selectedItems.add(id);
    this.notifySelectionChange();
  }

  deselectItem(id: string): void {
    this.selectedItems.delete(id);
    this.notifySelectionChange();
  }

  isSelected(id: string): boolean {
    return this.selectedItems.has(id);
  }

  toggleItem(id: string): void {
    if (this.selectedItems.has(id)) {
      this.deselectItem(id);
    } else {
      this.selectItem(id);
    }
  }

  getSelectedItems(): ContextItem[] {
    return this.context.filter(c => this.selectedItems.has(c.id));
  }

  getItemCount(): number {
    return this.context.length;
  }

  getSelectedCount(): number {
    return this.selectedItems.size;
  }

  clear(): void {
    this.context = [];
    this.selectedItems.clear();
    this.expandedItems.clear();
  }

  expandItem(id: string): void {
    this.expandedItems.add(id);
  }

  collapseItem(id: string): void {
    this.expandedItems.delete(id);
  }

  isExpanded(id: string): boolean {
    return this.expandedItems.has(id);
  }

  getRelevanceScore(): number {
    if (this.getSelectedCount() === 0) return 0;
    const total = this.getSelectedItems().reduce((sum, item) => sum + item.relevance, 0);
    return total / this.getSelectedCount();
  }

  onSelectionChangeCallback(callback: (selected: string[]) => void): void {
    this.onSelectionChange = callback;
  }

  private notifySelectionChange(): void {
    this.onSelectionChange?.(Array.from(this.selectedItems));
  }

  filterByType(type: string): ContextItem[] {
    return this.context.filter(c => c.type === type);
  }

  sortByRelevance(): ContextItem[] {
    return [...this.context].sort((a, b) => b.relevance - a.relevance);
  }
}

describe('ContextDisplay', () => {
  let display: ContextDisplay;

  beforeEach(() => {
    display = new ContextDisplay();
  });

  it('should initialize empty', () => {
    expect(display.getItemCount()).toBe(0);
  });

  it('should add items', () => {
    const item: ContextItem = {
      id: '1',
      type: 'file',
      path: '/src/main.ts',
      relevance: 0.9
    };
    display.addItem(item);
    expect(display.getItemCount()).toBe(1);
  });

  it('should not add duplicate items', () => {
    const item: ContextItem = {
      id: '1',
      type: 'file',
      path: '/src/main.ts',
      relevance: 0.9
    };
    display.addItem(item);
    display.addItem(item);
    expect(display.getItemCount()).toBe(1);
  });

  it('should remove items', () => {
    const item: ContextItem = {
      id: '1',
      type: 'file',
      path: '/src/main.ts',
      relevance: 0.9
    };
    display.addItem(item);
    expect(display.removeItem('1')).toBe(true);
    expect(display.getItemCount()).toBe(0);
  });

  it('should return false when removing nonexistent item', () => {
    expect(display.removeItem('nonexistent')).toBe(false);
  });

  it('should select items', () => {
    const item: ContextItem = {
      id: '1',
      type: 'file',
      path: '/src/main.ts',
      relevance: 0.9
    };
    display.addItem(item);
    display.selectItem('1');
    expect(display.isSelected('1')).toBe(true);
  });

  it('should deselect items', () => {
    const item: ContextItem = {
      id: '1',
      type: 'file',
      path: '/src/main.ts',
      relevance: 0.9
    };
    display.addItem(item);
    display.selectItem('1');
    display.deselectItem('1');
    expect(display.isSelected('1')).toBe(false);
  });

  it('should toggle items', () => {
    const item: ContextItem = {
      id: '1',
      type: 'file',
      path: '/src/main.ts',
      relevance: 0.9
    };
    display.addItem(item);
    display.toggleItem('1');
    expect(display.isSelected('1')).toBe(true);
    display.toggleItem('1');
    expect(display.isSelected('1')).toBe(false);
  });

  it('should get selected items', () => {
    const item1: ContextItem = {
      id: '1',
      type: 'file',
      path: '/src/main.ts',
      relevance: 0.9
    };
    const item2: ContextItem = {
      id: '2',
      type: 'file',
      path: '/src/utils.ts',
      relevance: 0.8
    };
    display.addItem(item1);
    display.addItem(item2);
    display.selectItem('1');
    const selected = display.getSelectedItems();
    expect(selected).toHaveLength(1);
    expect(selected[0].id).toBe('1');
  });

  it('should count selected items', () => {
    const item1: ContextItem = {
      id: '1',
      type: 'file',
      path: '/src/main.ts',
      relevance: 0.9
    };
    const item2: ContextItem = {
      id: '2',
      type: 'file',
      path: '/src/utils.ts',
      relevance: 0.8
    };
    display.addItem(item1);
    display.addItem(item2);
    display.selectItem('1');
    display.selectItem('2');
    expect(display.getSelectedCount()).toBe(2);
  });

  it('should clear context', () => {
    const item: ContextItem = {
      id: '1',
      type: 'file',
      path: '/src/main.ts',
      relevance: 0.9
    };
    display.addItem(item);
    display.selectItem('1');
    display.clear();
    expect(display.getItemCount()).toBe(0);
    expect(display.getSelectedCount()).toBe(0);
  });

  it('should expand and collapse items', () => {
    const item: ContextItem = {
      id: '1',
      type: 'directory',
      path: '/src',
      relevance: 0.9
    };
    display.addItem(item);
    display.expandItem('1');
    expect(display.isExpanded('1')).toBe(true);
    display.collapseItem('1');
    expect(display.isExpanded('1')).toBe(false);
  });

  it('should call selection change callback', () => {
    const callback = vi.fn();
    display.onSelectionChangeCallback(callback);

    const item: ContextItem = {
      id: '1',
      type: 'file',
      path: '/src/main.ts',
      relevance: 0.9
    };
    display.addItem(item);
    display.selectItem('1');
    expect(callback).toHaveBeenCalledWith(['1']);
  });

  it('should filter by type', () => {
    display.addItem({
      id: '1',
      type: 'file',
      path: '/src/main.ts',
      relevance: 0.9
    });
    display.addItem({
      id: '2',
      type: 'directory',
      path: '/src',
      relevance: 0.9
    });
    const files = display.filterByType('file');
    expect(files).toHaveLength(1);
    expect(files[0].type).toBe('file');
  });

  it('should sort by relevance', () => {
    display.addItem({
      id: '1',
      type: 'file',
      path: '/src/main.ts',
      relevance: 0.5
    });
    display.addItem({
      id: '2',
      type: 'file',
      path: '/src/utils.ts',
      relevance: 0.9
    });
    const sorted = display.sortByRelevance();
    expect(sorted[0].relevance).toBe(0.9);
    expect(sorted[1].relevance).toBe(0.5);
  });

  it('should calculate average relevance', () => {
    display.addItem({
      id: '1',
      type: 'file',
      path: '/src/main.ts',
      relevance: 0.8
    });
    display.addItem({
      id: '2',
      type: 'file',
      path: '/src/utils.ts',
      relevance: 0.6
    });
    display.selectItem('1');
    display.selectItem('2');
    const score = display.getRelevanceScore();
    expect(score).toBe(0.7);
  });
});
