import { describe, it, expect, beforeEach, vi } from 'vitest';

interface DiffLine {
  type: 'added' | 'removed' | 'unchanged';
  content: string;
  lineNumber?: number;
}

class DiffViewer {
  private oldContent: string = '';
  private newContent: string = '';
  private diffLines: DiffLine[] = [];
  private splitView: boolean = false;

  setContent(oldContent: string, newContent: string): void {
    this.oldContent = oldContent;
    this.newContent = newContent;
    this.generateDiff();
  }

  private generateDiff(): void {
    this.diffLines = [];
    const oldLines = this.oldContent.split('\n');
    const newLines = this.newContent.split('\n');

    const maxLines = Math.max(oldLines.length, newLines.length);

    for (let i = 0; i < maxLines; i++) {
      if (i < oldLines.length && i < newLines.length) {
        if (oldLines[i] === newLines[i]) {
          this.diffLines.push({ type: 'unchanged', content: oldLines[i], lineNumber: i });
        } else {
          this.diffLines.push({ type: 'removed', content: oldLines[i], lineNumber: i });
          this.diffLines.push({ type: 'added', content: newLines[i], lineNumber: i });
        }
      } else if (i < oldLines.length) {
        this.diffLines.push({ type: 'removed', content: oldLines[i], lineNumber: i });
      } else {
        this.diffLines.push({ type: 'added', content: newLines[i], lineNumber: i });
      }
    }
  }

  getDiffLines(): DiffLine[] {
    return [...this.diffLines];
  }

  getAddedLines(): DiffLine[] {
    return this.diffLines.filter(l => l.type === 'added');
  }

  getRemovedLines(): DiffLine[] {
    return this.diffLines.filter(l => l.type === 'removed');
  }

  getUnchangedLines(): DiffLine[] {
    return this.diffLines.filter(l => l.type === 'unchanged');
  }

  setSplitView(enabled: boolean): void {
    this.splitView = enabled;
  }

  isSplitView(): boolean {
    return this.splitView;
  }

  getStats(): { added: number; removed: number; total: number } {
    return {
      added: this.getAddedLines().length,
      removed: this.getRemovedLines().length,
      total: this.diffLines.length
    };
  }

  getOldContent(): string {
    return this.oldContent;
  }

  getNewContent(): string {
    return this.newContent;
  }

  clear(): void {
    this.oldContent = '';
    this.newContent = '';
    this.diffLines = [];
  }
}

describe('DiffViewer', () => {
  let viewer: DiffViewer;

  beforeEach(() => {
    viewer = new DiffViewer();
  });

  it('should initialize empty', () => {
    expect(viewer.getDiffLines()).toHaveLength(0);
  });

  it('should set content', () => {
    viewer.setContent('old', 'new');
    expect(viewer.getOldContent()).toBe('old');
    expect(viewer.getNewContent()).toBe('new');
  });

  it('should generate diff for identical content', () => {
    viewer.setContent('line1\nline2', 'line1\nline2');
    const unchanged = viewer.getUnchangedLines();
    expect(unchanged).toHaveLength(2);
  });

  it('should detect added lines', () => {
    viewer.setContent('line1', 'line1\nline2');
    const added = viewer.getAddedLines();
    expect(added).toHaveLength(1);
    expect(added[0].content).toBe('line2');
  });

  it('should detect removed lines', () => {
    viewer.setContent('line1\nline2', 'line1');
    const removed = viewer.getRemovedLines();
    expect(removed).toHaveLength(1);
    expect(removed[0].content).toBe('line2');
  });

  it('should detect changed lines', () => {
    viewer.setContent('old line', 'new line');
    const removed = viewer.getRemovedLines();
    const added = viewer.getAddedLines();
    expect(removed).toHaveLength(1);
    expect(added).toHaveLength(1);
  });

  it('should toggle split view', () => {
    expect(viewer.isSplitView()).toBe(false);
    viewer.setSplitView(true);
    expect(viewer.isSplitView()).toBe(true);
  });

  it('should get statistics', () => {
    viewer.setContent('line1\nline2', 'line1\nline3');
    const stats = viewer.getStats();
    expect(stats.added).toBe(1);
    expect(stats.removed).toBe(1);
  });

  it('should clear viewer', () => {
    viewer.setContent('old', 'new');
    viewer.clear();
    expect(viewer.getDiffLines()).toHaveLength(0);
    expect(viewer.getOldContent()).toBe('');
    expect(viewer.getNewContent()).toBe('');
  });

  it('should handle multiline content', () => {
    const old = 'line1\nline2\nline3';
    const newContent = 'line1\nline2modified\nline3\nline4';
    viewer.setContent(old, newContent);

    expect(viewer.getAddedLines()).toHaveLength(2);
    expect(viewer.getRemovedLines()).toHaveLength(1);
  });

  it('should filter different line types', () => {
    viewer.setContent('a\nb\nc', 'a\nx\nc\nd');
    const added = viewer.getAddedLines();
    const removed = viewer.getRemovedLines();
    const unchanged = viewer.getUnchangedLines();

    expect(added.length).toBeGreaterThan(0);
    expect(removed.length).toBeGreaterThan(0);
    expect(unchanged.length).toBeGreaterThan(0);
  });

  it('should handle empty files', () => {
    viewer.setContent('', 'content');
    expect(viewer.getAddedLines().length).toBeGreaterThan(0);
  });

  it('should preserve line numbers', () => {
    viewer.setContent('line1\nline2', 'line1\nline2');
    const lines = viewer.getDiffLines();
    expect(lines[0].lineNumber).toBe(0);
    expect(lines[1].lineNumber).toBe(1);
  });
});
