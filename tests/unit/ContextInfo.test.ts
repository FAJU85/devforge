import { describe, it, expect, beforeEach, vi } from 'vitest';

interface ContextMetadata {
  totalItems: number;
  selectedItems: number;
  averageRelevance: number;
  lastUpdated: number;
}

class ContextInfo {
  private metadata: ContextMetadata = {
    totalItems: 0,
    selectedItems: 0,
    averageRelevance: 0,
    lastUpdated: Date.now()
  };

  setMetadata(data: Partial<ContextMetadata>): void {
    this.metadata = { ...this.metadata, ...data };
  }

  getMetadata(): ContextMetadata {
    return { ...this.metadata };
  }

  updateLastModified(): void {
    this.metadata.lastUpdated = Date.now();
  }

  getSelectedPercentage(): number {
    if (this.metadata.totalItems === 0) return 0;
    return (this.metadata.selectedItems / this.metadata.totalItems) * 100;
  }

  isRelevant(): boolean {
    return this.metadata.averageRelevance >= 0.6;
  }

  getSummary(): string {
    return `${this.metadata.selectedItems}/${this.metadata.totalItems} items selected`;
  }
}

describe('ContextInfo', () => {
  let info: ContextInfo;

  beforeEach(() => {
    info = new ContextInfo();
  });

  it('should initialize with defaults', () => {
    const metadata = info.getMetadata();
    expect(metadata.totalItems).toBe(0);
    expect(metadata.selectedItems).toBe(0);
  });

  it('should set metadata', () => {
    info.setMetadata({ totalItems: 10, selectedItems: 5 });
    expect(info.getMetadata().totalItems).toBe(10);
    expect(info.getMetadata().selectedItems).toBe(5);
  });

  it('should calculate selection percentage', () => {
    info.setMetadata({ totalItems: 10, selectedItems: 5 });
    expect(info.getSelectedPercentage()).toBe(50);
  });

  it('should handle zero total items', () => {
    expect(info.getSelectedPercentage()).toBe(0);
  });

  it('should detect relevance', () => {
    info.setMetadata({ averageRelevance: 0.7 });
    expect(info.isRelevant()).toBe(true);

    info.setMetadata({ averageRelevance: 0.5 });
    expect(info.isRelevant()).toBe(false);
  });

  it('should update last modified time', () => {
    const before = info.getMetadata().lastUpdated;
    setTimeout(() => {
      info.updateLastModified();
      const after = info.getMetadata().lastUpdated;
      expect(after).toBeGreaterThan(before);
    }, 10);
  });

  it('should generate summary', () => {
    info.setMetadata({ totalItems: 10, selectedItems: 3 });
    expect(info.getSummary()).toBe('3/10 items selected');
  });
});
