import { describe, it, expect, beforeEach } from 'vitest';
import { useRepoStore, Repository, FileNode } from '../../src/stores/repoStore';

describe('Repository Store', () => {
  beforeEach(() => {
    // Reset store state before each test
    useRepoStore.setState({
      repositories: [],
      currentRepoId: null,
      fileTree: [],
      selectedFileId: null,
      openFiles: [],
      searchQuery: '',
      filteredFiles: [],
    });
  });

  describe('Initial State', () => {
    it('should have correct initial state', () => {
      const state = useRepoStore.getState();
      expect(state.repositories).toEqual([]);
      expect(state.currentRepoId).toBeNull();
      expect(state.fileTree).toEqual([]);
      expect(state.selectedFileId).toBeNull();
      expect(state.openFiles).toEqual([]);
      expect(state.searchQuery).toBe('');
      expect(state.filteredFiles).toEqual([]);
    });
  });

  describe('Repository Management', () => {
    it('should add a repository', () => {
      const state = useRepoStore.getState();
      const repo: Repository = {
        id: 'repo-1',
        name: 'DevForge',
        owner: 'user',
        url: 'https://github.com/user/devforge',
        branch: 'main',
      };

      state.addRepository(repo);

      expect(useRepoStore.getState().repositories).toHaveLength(1);
      expect(useRepoStore.getState().repositories[0]).toEqual(repo);
    });

    it('should set first repository as current automatically', () => {
      const state = useRepoStore.getState();
      const repo: Repository = {
        id: 'repo-1',
        name: 'DevForge',
        owner: 'user',
        url: 'https://github.com/user/devforge',
        branch: 'main',
      };

      state.addRepository(repo);

      expect(useRepoStore.getState().currentRepoId).toBe('repo-1');
    });

    it('should not change current repo when adding subsequent repositories', () => {
      const state = useRepoStore.getState();
      const repo1: Repository = {
        id: 'repo-1',
        name: 'DevForge',
        owner: 'user',
        url: 'https://github.com/user/devforge',
        branch: 'main',
      };
      const repo2: Repository = {
        id: 'repo-2',
        name: 'Project',
        owner: 'user',
        url: 'https://github.com/user/project',
        branch: 'main',
      };

      state.addRepository(repo1);
      state.addRepository(repo2);

      expect(useRepoStore.getState().currentRepoId).toBe('repo-1');
    });

    it('should remove a repository', () => {
      const state = useRepoStore.getState();
      const repo: Repository = {
        id: 'repo-1',
        name: 'DevForge',
        owner: 'user',
        url: 'https://github.com/user/devforge',
        branch: 'main',
      };

      state.addRepository(repo);
      expect(useRepoStore.getState().repositories).toHaveLength(1);

      state.removeRepository('repo-1');
      expect(useRepoStore.getState().repositories).toHaveLength(0);
    });

    it('should clear current repo when removing active repository', () => {
      const state = useRepoStore.getState();
      const repo: Repository = {
        id: 'repo-1',
        name: 'DevForge',
        owner: 'user',
        url: 'https://github.com/user/devforge',
        branch: 'main',
      };

      state.addRepository(repo);
      expect(useRepoStore.getState().currentRepoId).toBe('repo-1');

      state.removeRepository('repo-1');
      expect(useRepoStore.getState().currentRepoId).toBeNull();
    });

    it('should set current repository', () => {
      const state = useRepoStore.getState();
      const repo1: Repository = {
        id: 'repo-1',
        name: 'DevForge',
        owner: 'user',
        url: 'https://github.com/user/devforge',
        branch: 'main',
      };
      const repo2: Repository = {
        id: 'repo-2',
        name: 'Project',
        owner: 'user',
        url: 'https://github.com/user/project',
        branch: 'main',
      };

      state.addRepository(repo1);
      state.addRepository(repo2);

      state.setCurrentRepository('repo-2');
      expect(useRepoStore.getState().currentRepoId).toBe('repo-2');
    });

    it('should get current repository', () => {
      const state = useRepoStore.getState();
      const repo: Repository = {
        id: 'repo-1',
        name: 'DevForge',
        owner: 'user',
        url: 'https://github.com/user/devforge',
        branch: 'main',
      };

      state.addRepository(repo);
      const current = state.getCurrentRepository();

      expect(current).toBeDefined();
      expect(current?.id).toBe('repo-1');
      expect(current?.name).toBe('DevForge');
    });

    it('should return undefined for current repository when none selected', () => {
      const state = useRepoStore.getState();
      const current = state.getCurrentRepository();

      expect(current).toBeUndefined();
    });
  });

  describe('File Tree Management', () => {
    it('should set file tree', () => {
      const state = useRepoStore.getState();
      const fileTree: FileNode[] = [
        {
          id: 'file-1',
          name: 'src',
          path: '/src',
          type: 'folder',
          children: [
            {
              id: 'file-2',
              name: 'main.ts',
              path: '/src/main.ts',
              type: 'file',
              language: 'typescript',
            },
          ],
        },
      ];

      state.setFileTree(fileTree);

      expect(useRepoStore.getState().fileTree).toEqual(fileTree);
    });

    it('should select a file', () => {
      const state = useRepoStore.getState();
      state.selectFile('file-1');

      expect(useRepoStore.getState().selectedFileId).toBe('file-1');
    });

    it('should deselect file by passing null', () => {
      const state = useRepoStore.getState();
      state.selectFile('file-1');
      state.selectFile(null);

      expect(useRepoStore.getState().selectedFileId).toBeNull();
    });

    it('should open a file', () => {
      const state = useRepoStore.getState();
      state.openFile('file-1');

      expect(useRepoStore.getState().openFiles).toContain('file-1');
      expect(useRepoStore.getState().selectedFileId).toBe('file-1');
    });

    it('should not duplicate open files', () => {
      const state = useRepoStore.getState();
      state.openFile('file-1');
      state.openFile('file-1');

      expect(useRepoStore.getState().openFiles).toHaveLength(1);
    });

    it('should open multiple files', () => {
      const state = useRepoStore.getState();
      state.openFile('file-1');
      state.openFile('file-2');
      state.openFile('file-3');

      expect(useRepoStore.getState().openFiles).toHaveLength(3);
      expect(useRepoStore.getState().openFiles).toContain('file-1');
      expect(useRepoStore.getState().openFiles).toContain('file-2');
      expect(useRepoStore.getState().openFiles).toContain('file-3');
    });

    it('should close a file', () => {
      const state = useRepoStore.getState();
      state.openFile('file-1');
      state.openFile('file-2');

      expect(useRepoStore.getState().openFiles).toHaveLength(2);

      state.closeFile('file-1');
      expect(useRepoStore.getState().openFiles).toHaveLength(1);
      expect(useRepoStore.getState().openFiles).not.toContain('file-1');
    });

    it('should clear selection when closing selected file', () => {
      const state = useRepoStore.getState();
      state.openFile('file-1');

      expect(useRepoStore.getState().selectedFileId).toBe('file-1');

      state.closeFile('file-1');
      expect(useRepoStore.getState().selectedFileId).toBeNull();
    });

    it('should preserve selection when closing non-selected file', () => {
      const state = useRepoStore.getState();
      state.openFile('file-1');
      state.openFile('file-2');
      state.selectFile('file-1');

      state.closeFile('file-2');
      expect(useRepoStore.getState().selectedFileId).toBe('file-1');
    });

    it('should get file from tree', () => {
      const state = useRepoStore.getState();
      const fileTree: FileNode[] = [
        {
          id: 'folder-1',
          name: 'src',
          path: '/src',
          type: 'folder',
          children: [
            {
              id: 'file-1',
              name: 'main.ts',
              path: '/src/main.ts',
              type: 'file',
              language: 'typescript',
            },
          ],
        },
      ];

      state.setFileTree(fileTree);
      const file = state.getFile('file-1');

      expect(file).toBeDefined();
      expect(file?.name).toBe('main.ts');
    });

    it('should return undefined for non-existent file', () => {
      const state = useRepoStore.getState();
      const file = state.getFile('non-existent');

      expect(file).toBeUndefined();
    });

    it('should get open file count', () => {
      const state = useRepoStore.getState();
      state.openFile('file-1');
      state.openFile('file-2');
      state.openFile('file-3');

      expect(state.getOpenFileCount()).toBe(3);
    });
  });

  describe('Folder Toggle', () => {
    it('should toggle folder open state', () => {
      const state = useRepoStore.getState();
      const fileTree: FileNode[] = [
        {
          id: 'folder-1',
          name: 'src',
          path: '/src',
          type: 'folder',
          isOpen: false,
        },
      ];

      state.setFileTree(fileTree);
      state.toggleFolder('folder-1');

      expect(useRepoStore.getState().fileTree[0].isOpen).toBe(true);

      state.toggleFolder('folder-1');
      expect(useRepoStore.getState().fileTree[0].isOpen).toBe(false);
    });

    it('should toggle nested folder', () => {
      const state = useRepoStore.getState();
      const fileTree: FileNode[] = [
        {
          id: 'folder-1',
          name: 'src',
          path: '/src',
          type: 'folder',
          isOpen: true,
          children: [
            {
              id: 'folder-2',
              name: 'components',
              path: '/src/components',
              type: 'folder',
              isOpen: false,
            },
          ],
        },
      ];

      state.setFileTree(fileTree);
      state.toggleFolder('folder-2');

      const nestedFolder = useRepoStore.getState().fileTree[0].children?.[0];
      expect(nestedFolder?.isOpen).toBe(true);
    });
  });

  describe('Search Functionality', () => {
    beforeEach(() => {
      const state = useRepoStore.getState();
      const fileTree: FileNode[] = [
        {
          id: 'folder-1',
          name: 'src',
          path: '/src',
          type: 'folder',
          children: [
            {
              id: 'file-1',
              name: 'main.ts',
              path: '/src/main.ts',
              type: 'file',
              language: 'typescript',
            },
            {
              id: 'file-2',
              name: 'utils.ts',
              path: '/src/utils.ts',
              type: 'file',
              language: 'typescript',
            },
          ],
        },
        {
          id: 'folder-2',
          name: 'tests',
          path: '/tests',
          type: 'folder',
          children: [
            {
              id: 'file-3',
              name: 'main.test.ts',
              path: '/tests/main.test.ts',
              type: 'file',
              language: 'typescript',
            },
          ],
        },
      ];

      state.setFileTree(fileTree);
    });

    it('should search files by name', () => {
      const state = useRepoStore.getState();
      const results = state.searchFiles('main');

      expect(results.length).toBeGreaterThan(0);
      expect(results.some((f) => f.name.includes('main'))).toBe(true);
    });

    it('should search case-insensitively', () => {
      const state = useRepoStore.getState();
      const results = state.searchFiles('MAIN');

      expect(results.length).toBeGreaterThan(0);
    });

    it('should return empty array for no matches', () => {
      const state = useRepoStore.getState();
      const results = state.searchFiles('nonexistent');

      expect(results).toEqual([]);
    });

    it('should return empty array for empty query', () => {
      const state = useRepoStore.getState();
      const results = state.searchFiles('');

      expect(results).toEqual([]);
    });

    it('should set search query and update filtered files', () => {
      const state = useRepoStore.getState();
      state.setSearchQuery('test');

      expect(useRepoStore.getState().searchQuery).toBe('test');
      expect(useRepoStore.getState().filteredFiles.length).toBeGreaterThan(0);
    });

    it('should clear filtered files when clearing search', () => {
      const state = useRepoStore.getState();
      state.setSearchQuery('test');
      expect(useRepoStore.getState().filteredFiles.length).toBeGreaterThan(0);

      state.setSearchQuery('');
      expect(useRepoStore.getState().filteredFiles).toEqual([]);
    });
  });

  describe('Edge Cases', () => {
    it('should handle adding repository with no lastSynced date', () => {
      const state = useRepoStore.getState();
      const repo: Repository = {
        id: 'repo-1',
        name: 'DevForge',
        owner: 'user',
        url: 'https://github.com/user/devforge',
        branch: 'main',
      };

      state.addRepository(repo);

      expect(useRepoStore.getState().repositories[0].lastSynced).toBeUndefined();
    });

    it('should handle removing non-existent repository', () => {
      const state = useRepoStore.getState();
      state.removeRepository('non-existent');

      expect(useRepoStore.getState().repositories).toHaveLength(0);
    });

    it('should handle closing non-existent file', () => {
      const state = useRepoStore.getState();
      state.closeFile('non-existent');

      expect(useRepoStore.getState().openFiles).toHaveLength(0);
    });

    it('should handle empty file tree', () => {
      const state = useRepoStore.getState();
      state.setFileTree([]);

      expect(useRepoStore.getState().fileTree).toEqual([]);
    });

    it('should handle deeply nested file search', () => {
      const state = useRepoStore.getState();
      const deepTree: FileNode[] = [
        {
          id: 'f1',
          name: 'a',
          path: '/a',
          type: 'folder',
          children: [
            {
              id: 'f2',
              name: 'b',
              path: '/a/b',
              type: 'folder',
              children: [
                {
                  id: 'f3',
                  name: 'c',
                  path: '/a/b/c',
                  type: 'folder',
                  children: [
                    {
                      id: 'f4',
                      name: 'target.ts',
                      path: '/a/b/c/target.ts',
                      type: 'file',
                    },
                  ],
                },
              ],
            },
          ],
        },
      ];

      state.setFileTree(deepTree);
      const results = state.searchFiles('target');

      expect(results.length).toBeGreaterThan(0);
      expect(results.some((f) => f.name === 'target.ts')).toBe(true);
    });

    it('should handle file with no language property', () => {
      const state = useRepoStore.getState();
      const fileTree: FileNode[] = [
        {
          id: 'file-1',
          name: 'README',
          path: '/README',
          type: 'file',
        },
      ];

      state.setFileTree(fileTree);
      const file = state.getFile('file-1');

      expect(file?.language).toBeUndefined();
    });

    it('should handle file with size property', () => {
      const state = useRepoStore.getState();
      const fileTree: FileNode[] = [
        {
          id: 'file-1',
          name: 'main.ts',
          path: '/src/main.ts',
          type: 'file',
          language: 'typescript',
          size: 1024,
        },
      ];

      state.setFileTree(fileTree);
      const file = state.getFile('file-1');

      expect(file?.size).toBe(1024);
    });

    it('should handle setting null as current repository', () => {
      const state = useRepoStore.getState();
      const repo: Repository = {
        id: 'repo-1',
        name: 'DevForge',
        owner: 'user',
        url: 'https://github.com/user/devforge',
        branch: 'main',
      };

      state.addRepository(repo);
      state.setCurrentRepository(null);

      expect(useRepoStore.getState().currentRepoId).toBeNull();
    });
  });

  describe('Complex Scenarios', () => {
    it('should handle multiple repositories with file operations', () => {
      const state = useRepoStore.getState();
      const repo1: Repository = {
        id: 'repo-1',
        name: 'DevForge',
        owner: 'user',
        url: 'https://github.com/user/devforge',
        branch: 'main',
      };
      const repo2: Repository = {
        id: 'repo-2',
        name: 'Project',
        owner: 'user',
        url: 'https://github.com/user/project',
        branch: 'main',
      };

      state.addRepository(repo1);
      state.addRepository(repo2);

      const fileTree: FileNode[] = [
        {
          id: 'file-1',
          name: 'main.ts',
          path: '/src/main.ts',
          type: 'file',
        },
      ];

      state.setFileTree(fileTree);
      state.openFile('file-1');

      expect(useRepoStore.getState().repositories).toHaveLength(2);
      expect(useRepoStore.getState().openFiles).toHaveLength(1);
      expect(useRepoStore.getState().currentRepoId).toBe('repo-1');
    });

    it('should handle repository switching with open files', () => {
      const state = useRepoStore.getState();
      const repo1: Repository = {
        id: 'repo-1',
        name: 'DevForge',
        owner: 'user',
        url: 'https://github.com/user/devforge',
        branch: 'main',
      };
      const repo2: Repository = {
        id: 'repo-2',
        name: 'Project',
        owner: 'user',
        url: 'https://github.com/user/project',
        branch: 'main',
      };

      state.addRepository(repo1);
      state.addRepository(repo2);
      state.openFile('file-1');

      state.setCurrentRepository('repo-2');

      expect(useRepoStore.getState().currentRepoId).toBe('repo-2');
      expect(useRepoStore.getState().openFiles).toHaveLength(1); // Files persist
    });
  });
});
