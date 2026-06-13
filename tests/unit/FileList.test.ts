import { describe, it, expect, beforeEach, vi } from 'vitest';

interface FileItem {
  id: string;
  name: string;
  path: string;
  size: number;
  modified: number;
}

class FileList {
  private files: FileItem[] = [];
  private selected: Set<string> = new Set();
  private sortBy: 'name' | 'size' | 'modified' = 'name';

  addFile(file: FileItem): void {
    if (!this.files.find(f => f.id === file.id)) {
      this.files.push(file);
    }
  }

  removeFile(id: string): boolean {
    const index = this.files.findIndex(f => f.id === id);
    if (index > -1) {
      this.files.splice(index, 1);
      this.selected.delete(id);
      return true;
    }
    return false;
  }

  getFiles(): FileItem[] {
    return this.getSorted();
  }

  selectFile(id: string): void {
    this.selected.add(id);
  }

  deselectFile(id: string): void {
    this.selected.delete(id);
  }

  getSelected(): FileItem[] {
    return this.files.filter(f => this.selected.has(f.id));
  }

  getSelectedCount(): number {
    return this.selected.size;
  }

  setSortBy(sortBy: 'name' | 'size' | 'modified'): void {
    this.sortBy = sortBy;
  }

  private getSorted(): FileItem[] {
    const sorted = [...this.files];
    if (this.sortBy === 'name') {
      sorted.sort((a, b) => a.name.localeCompare(b.name));
    } else if (this.sortBy === 'size') {
      sorted.sort((a, b) => a.size - b.size);
    } else if (this.sortBy === 'modified') {
      sorted.sort((a, b) => b.modified - a.modified);
    }
    return sorted;
  }

  getFileCount(): number {
    return this.files.length;
  }

  clear(): void {
    this.files = [];
    this.selected.clear();
  }

  search(query: string): FileItem[] {
    const lower = query.toLowerCase();
    return this.files.filter(f => f.name.toLowerCase().includes(lower));
  }
}

describe('FileList', () => {
  let list: FileList;

  beforeEach(() => {
    list = new FileList();
  });

  it('should initialize empty', () => {
    expect(list.getFileCount()).toBe(0);
  });

  it('should add file', () => {
    const file: FileItem = {
      id: '1',
      name: 'test.ts',
      path: '/test.ts',
      size: 1024,
      modified: Date.now()
    };
    list.addFile(file);
    expect(list.getFileCount()).toBe(1);
  });

  it('should remove file', () => {
    const file: FileItem = {
      id: '1',
      name: 'test.ts',
      path: '/test.ts',
      size: 1024,
      modified: Date.now()
    };
    list.addFile(file);
    expect(list.removeFile('1')).toBe(true);
    expect(list.getFileCount()).toBe(0);
  });

  it('should select file', () => {
    const file: FileItem = {
      id: '1',
      name: 'test.ts',
      path: '/test.ts',
      size: 1024,
      modified: Date.now()
    };
    list.addFile(file);
    list.selectFile('1');
    expect(list.getSelectedCount()).toBe(1);
  });

  it('should deselect file', () => {
    const file: FileItem = {
      id: '1',
      name: 'test.ts',
      path: '/test.ts',
      size: 1024,
      modified: Date.now()
    };
    list.addFile(file);
    list.selectFile('1');
    list.deselectFile('1');
    expect(list.getSelectedCount()).toBe(0);
  });

  it('should get selected files', () => {
    const file1: FileItem = {
      id: '1',
      name: 'test1.ts',
      path: '/test1.ts',
      size: 1024,
      modified: Date.now()
    };
    const file2: FileItem = {
      id: '2',
      name: 'test2.ts',
      path: '/test2.ts',
      size: 2048,
      modified: Date.now()
    };
    list.addFile(file1);
    list.addFile(file2);
    list.selectFile('1');
    expect(list.getSelected()).toHaveLength(1);
  });

  it('should sort by name', () => {
    list.addFile({ id: '1', name: 'z.ts', path: '/z.ts', size: 1024, modified: Date.now() });
    list.addFile({ id: '2', name: 'a.ts', path: '/a.ts', size: 2048, modified: Date.now() });
    list.setSortBy('name');
    const files = list.getFiles();
    expect(files[0].name).toBe('a.ts');
  });

  it('should sort by size', () => {
    list.addFile({ id: '1', name: 'big.ts', path: '/big.ts', size: 5000, modified: Date.now() });
    list.addFile({ id: '2', name: 'small.ts', path: '/small.ts', size: 512, modified: Date.now() });
    list.setSortBy('size');
    const files = list.getFiles();
    expect(files[0].size).toBe(512);
  });

  it('should search files', () => {
    list.addFile({ id: '1', name: 'main.ts', path: '/main.ts', size: 1024, modified: Date.now() });
    list.addFile({ id: '2', name: 'utils.ts', path: '/utils.ts', size: 2048, modified: Date.now() });
    const results = list.search('main');
    expect(results).toHaveLength(1);
  });

  it('should clear files', () => {
    list.addFile({ id: '1', name: 'test.ts', path: '/test.ts', size: 1024, modified: Date.now() });
    list.clear();
    expect(list.getFileCount()).toBe(0);
  });
});
