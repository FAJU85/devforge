import { describe, it, expect, beforeEach, vi } from 'vitest';

interface ContextItem {
  id: string;
  content: string;
  type: 'file' | 'code' | 'doc';
}

class ContextService {
  private items: ContextItem[] = [];
  private onItemsChange: ((items: ContextItem[]) => void) | null = null;

  addItem(item: ContextItem): void {
    if (!this.items.find(i => i.id === item.id)) {
      this.items.push(item);
      this.notifyChange();
    }
  }

  removeItem(id: string): boolean {
    const index = this.items.findIndex(i => i.id === id);
    if (index > -1) {
      this.items.splice(index, 1);
      this.notifyChange();
      return true;
    }
    return false;
  }

  getItems(): ContextItem[] {
    return [...this.items];
  }

  getItemsByType(type: string): ContextItem[] {
    return this.items.filter(i => i.type === type);
  }

  clearItems(): void {
    this.items = [];
    this.notifyChange();
  }

  onItemsChanged(callback: (items: ContextItem[]) => void): void {
    this.onItemsChange = callback;
  }

  private notifyChange(): void {
    this.onItemsChange?.(this.items);
  }

  getItemCount(): number {
    return this.items.length;
  }
}

describe('ContextService', () => {
  let service: ContextService;

  beforeEach(() => {
    service = new ContextService();
  });

  it('should initialize empty', () => {
    expect(service.getItemCount()).toBe(0);
  });

  it('should add item', () => {
    const item: ContextItem = { id: '1', content: 'test', type: 'file' };
    service.addItem(item);
    expect(service.getItemCount()).toBe(1);
  });

  it('should remove item', () => {
    service.addItem({ id: '1', content: 'test', type: 'file' });
    expect(service.removeItem('1')).toBe(true);
    expect(service.getItemCount()).toBe(0);
  });

  it('should filter by type', () => {
    service.addItem({ id: '1', content: 'file', type: 'file' });
    service.addItem({ id: '2', content: 'code', type: 'code' });
    const files = service.getItemsByType('file');
    expect(files).toHaveLength(1);
  });

  it('should call onItemsChanged', () => {
    const callback = vi.fn();
    service.onItemsChanged(callback);
    service.addItem({ id: '1', content: 'test', type: 'file' });
    expect(callback).toHaveBeenCalled();
  });

  it('should clear items', () => {
    service.addItem({ id: '1', content: 'test', type: 'file' });
    service.clearItems();
    expect(service.getItemCount()).toBe(0);
  });
});
