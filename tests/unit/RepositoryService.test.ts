import { describe, it, expect, beforeEach, vi } from 'vitest';

interface File {
  name: string;
  path: string;
  type: 'file' | 'directory';
  size: number;
}

interface Repository {
  name: string;
  owner: string;
  url: string;
  description: string;
  isPrivate: boolean;
}

class RepositoryService {
  private currentRepo: Repository | null = null;
  private files: File[] = [];
  private onRepoChange: ((repo: Repository | null) => void) | null = null;
  private onFilesChange: ((files: File[]) => void) | null = null;

  setRepository(repo: Repository): void {
    this.currentRepo = repo;
    this.files = [];
    this.onRepoChange?.(repo);
  }

  getRepository(): Repository | null {
    return this.currentRepo;
  }

  setFiles(files: File[]): void {
    this.files = files;
    this.onFilesChange?.(files);
  }

  getFiles(): File[] {
    return [...this.files];
  }

  getFileByPath(path: string): File | undefined {
    return this.files.find(f => f.path === path);
  }

  getDirectories(): File[] {
    return this.files.filter(f => f.type === 'directory');
  }

  getFilesByExtension(ext: string): File[] {
    return this.files.filter(f =>
      f.type === 'file' && f.name.endsWith(`.${ext}`)
    );
  }

  deleteFile(path: string): boolean {
    const index = this.files.findIndex(f => f.path === path);
    if (index > -1) {
      this.files.splice(index, 1);
      return true;
    }
    return false;
  }

  addFile(file: File): void {
    if (!this.files.find(f => f.path === file.path)) {
      this.files.push(file);
    }
  }

  getTotalSize(): number {
    return this.files.reduce((sum, f) => sum + f.size, 0);
  }

  onRepositoryChange(callback: (repo: Repository | null) => void): void {
    this.onRepoChange = callback;
  }

  onFilesChange(callback: (files: File[]) => void): void {
    this.onFilesChange = callback;
  }

  search(query: string): File[] {
    return this.files.filter(f =>
      f.name.toLowerCase().includes(query.toLowerCase())
    );
  }

  clearRepository(): void {
    this.currentRepo = null;
    this.files = [];
  }
}

describe('RepositoryService', () => {
  let service: RepositoryService;
  const mockRepo: Repository = {
    name: 'devforge',
    owner: 'faju85',
    url: 'https://github.com/faju85/devforge',
    description: 'AI coding agent',
    isPrivate: false
  };

  const mockFiles: File[] = [
    { name: 'package.json', path: 'package.json', type: 'file', size: 1024 },
    { name: 'src', path: 'src', type: 'directory', size: 0 },
    { name: 'main.ts', path: 'src/main.ts', type: 'file', size: 2048 },
    { name: 'utils.ts', path: 'src/utils.ts', type: 'file', size: 512 }
  ];

  beforeEach(() => {
    service = new RepositoryService();
  });

  it('should initialize without repository', () => {
    expect(service.getRepository()).toBeNull();
  });

  it('should set repository', () => {
    service.setRepository(mockRepo);
    expect(service.getRepository()?.name).toBe('devforge');
  });

  it('should clear files when changing repo', () => {
    service.setFiles(mockFiles);
    service.setRepository(mockRepo);
    expect(service.getFiles()).toHaveLength(0);
  });

  it('should set and get files', () => {
    service.setFiles(mockFiles);
    expect(service.getFiles()).toHaveLength(4);
  });

  it('should get file by path', () => {
    service.setFiles(mockFiles);
    const file = service.getFileByPath('package.json');
    expect(file?.name).toBe('package.json');
  });

  it('should get directories', () => {
    service.setFiles(mockFiles);
    const dirs = service.getDirectories();
    expect(dirs).toHaveLength(1);
    expect(dirs[0].name).toBe('src');
  });

  it('should get files by extension', () => {
    service.setFiles(mockFiles);
    const tsFiles = service.getFilesByExtension('ts');
    expect(tsFiles).toHaveLength(2);
  });

  it('should delete file', () => {
    service.setFiles([...mockFiles]);
    const deleted = service.deleteFile('package.json');
    expect(deleted).toBe(true);
    expect(service.getFiles()).toHaveLength(3);
  });

  it('should return false when deleting nonexistent file', () => {
    service.setFiles(mockFiles);
    expect(service.deleteFile('nonexistent')).toBe(false);
  });

  it('should add file', () => {
    service.setFiles(mockFiles);
    const newFile: File = { name: 'test.ts', path: 'test.ts', type: 'file', size: 256 };
    service.addFile(newFile);
    expect(service.getFiles()).toHaveLength(5);
  });

  it('should not add duplicate files', () => {
    service.setFiles(mockFiles);
    service.addFile(mockFiles[0]);
    expect(service.getFiles()).toHaveLength(4);
  });

  it('should calculate total size', () => {
    service.setFiles(mockFiles);
    expect(service.getTotalSize()).toBe(3584); // 1024 + 2048 + 512
  });

  it('should call onRepositoryChange callback', () => {
    const callback = vi.fn();
    service.onRepositoryChange(callback);
    service.setRepository(mockRepo);
    expect(callback).toHaveBeenCalledWith(mockRepo);
  });

  it('should call onFilesChange callback', () => {
    const callback = vi.fn();
    service.onFilesChange(callback);
    service.setFiles(mockFiles);
    expect(callback).toHaveBeenCalledWith(mockFiles);
  });

  it('should search files', () => {
    service.setFiles(mockFiles);
    const results = service.search('main');
    expect(results).toHaveLength(1);
    expect(results[0].name).toBe('main.ts');
  });

  it('should search case-insensitive', () => {
    service.setFiles(mockFiles);
    const results = service.search('PACKAGE');
    expect(results).toHaveLength(1);
  });

  it('should clear repository', () => {
    service.setRepository(mockRepo);
    service.setFiles(mockFiles);
    service.clearRepository();
    expect(service.getRepository()).toBeNull();
    expect(service.getFiles()).toHaveLength(0);
  });
});
