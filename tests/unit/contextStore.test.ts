import { describe, it, expect, beforeEach } from 'vitest';
import { useContextStore, ContextFile, ContextReference } from '../../src/stores/contextStore';

describe('Context Store', () => {
  beforeEach(() => {
    // Reset store state before each test
    useContextStore.setState({
      files: [],
      totalTokens: 0,
      maxTokens: 8000,
      references: [],
      createdAt: new Date(),
      lastUpdated: new Date(),
    });
  });

  describe('Initial State', () => {
    it('should have correct initial state', () => {
      const state = useContextStore.getState();
      expect(state.files).toEqual([]);
      expect(state.totalTokens).toBe(0);
      expect(state.maxTokens).toBe(8000);
      expect(state.references).toEqual([]);
      expect(state.createdAt).toBeInstanceOf(Date);
      expect(state.lastUpdated).toBeInstanceOf(Date);
    });

    it('should have default maxTokens of 8000', () => {
      const state = useContextStore.getState();
      expect(state.maxTokens).toBe(8000);
    });
  });

  describe('File Management', () => {
    it('should add a file to context', () => {
      const state = useContextStore.getState();
      const file: ContextFile = {
        id: 'file-1',
        path: '/src/main.ts',
        name: 'main.ts',
        tokens: 100,
        language: 'typescript',
      };

      state.addFile(file);

      expect(useContextStore.getState().files).toHaveLength(1);
      expect(useContextStore.getState().files[0]).toEqual(file);
      expect(useContextStore.getState().totalTokens).toBe(100);
    });

    it('should not add file if it exceeds token limit', () => {
      const state = useContextStore.getState();
      const file: ContextFile = {
        id: 'file-1',
        path: '/src/large.ts',
        name: 'large.ts',
        tokens: 9000,
        language: 'typescript',
      };

      state.addFile(file);

      // File should not be added
      expect(useContextStore.getState().files).toHaveLength(0);
      expect(useContextStore.getState().totalTokens).toBe(0);
    });

    it('should add multiple files as long as within token limit', () => {
      const state = useContextStore.getState();
      const file1: ContextFile = {
        id: 'file-1',
        path: '/src/file1.ts',
        name: 'file1.ts',
        tokens: 2000,
        language: 'typescript',
      };
      const file2: ContextFile = {
        id: 'file-2',
        path: '/src/file2.ts',
        name: 'file2.ts',
        tokens: 3000,
        language: 'typescript',
      };

      state.addFile(file1);
      state.addFile(file2);

      expect(useContextStore.getState().files).toHaveLength(2);
      expect(useContextStore.getState().totalTokens).toBe(5000);
    });

    it('should prevent adding file that would exceed limit', () => {
      const state = useContextStore.getState();
      const file1: ContextFile = {
        id: 'file-1',
        path: '/src/file1.ts',
        name: 'file1.ts',
        tokens: 5000,
        language: 'typescript',
      };
      const file2: ContextFile = {
        id: 'file-2',
        path: '/src/file2.ts',
        name: 'file2.ts',
        tokens: 4000,
        language: 'typescript',
      };

      state.addFile(file1);
      state.addFile(file2); // Should fail

      expect(useContextStore.getState().files).toHaveLength(1);
      expect(useContextStore.getState().totalTokens).toBe(5000);
    });

    it('should remove a file from context', () => {
      const state = useContextStore.getState();
      const file: ContextFile = {
        id: 'file-1',
        path: '/src/main.ts',
        name: 'main.ts',
        tokens: 100,
        language: 'typescript',
      };

      state.addFile(file);
      expect(useContextStore.getState().files).toHaveLength(1);

      state.removeFile('file-1');
      expect(useContextStore.getState().files).toHaveLength(0);
      expect(useContextStore.getState().totalTokens).toBe(0);
    });

    it('should update a file in context', () => {
      const state = useContextStore.getState();
      const file: ContextFile = {
        id: 'file-1',
        path: '/src/main.ts',
        name: 'main.ts',
        tokens: 100,
        language: 'typescript',
      };

      state.addFile(file);
      state.updateFile('file-1', { name: 'updated.ts', tokens: 150 });

      const updated = useContextStore.getState().files[0];
      expect(updated.name).toBe('updated.ts');
      expect(updated.tokens).toBe(150);
      expect(useContextStore.getState().totalTokens).toBe(150);
    });

    it('should not update file if token increase exceeds limit', () => {
      const state = useContextStore.getState();
      const file: ContextFile = {
        id: 'file-1',
        path: '/src/main.ts',
        name: 'main.ts',
        tokens: 4000,
        language: 'typescript',
      };

      state.addFile(file);
      state.updateFile('file-1', { tokens: 9000 }); // Would exceed 8000 limit

      expect(useContextStore.getState().files[0].tokens).toBe(4000);
      expect(useContextStore.getState().totalTokens).toBe(4000);
    });

    it('should clear all files from context', () => {
      const state = useContextStore.getState();
      const file1: ContextFile = {
        id: 'file-1',
        path: '/src/file1.ts',
        name: 'file1.ts',
        tokens: 100,
        language: 'typescript',
      };
      const file2: ContextFile = {
        id: 'file-2',
        path: '/src/file2.ts',
        name: 'file2.ts',
        tokens: 200,
        language: 'typescript',
      };

      state.addFile(file1);
      state.addFile(file2);
      expect(useContextStore.getState().files).toHaveLength(2);

      state.clearFiles();
      expect(useContextStore.getState().files).toHaveLength(0);
      expect(useContextStore.getState().totalTokens).toBe(0);
    });

    it('should update lastUpdated timestamp when file is added', () => {
      const state = useContextStore.getState();
      const initialTime = useContextStore.getState().lastUpdated;
      const file: ContextFile = {
        id: 'file-1',
        path: '/src/main.ts',
        name: 'main.ts',
        tokens: 100,
        language: 'typescript',
      };

      state.addFile(file);
      const updatedTime = useContextStore.getState().lastUpdated;

      expect(updatedTime.getTime()).toBeGreaterThanOrEqual(initialTime.getTime());
    });
  });

  describe('Reference Management', () => {
    it('should add a reference', () => {
      const state = useContextStore.getState();
      const ref: ContextReference = {
        id: 'ref-1',
        type: 'function',
        name: 'getData',
        path: '/src/api.ts',
        lineStart: 10,
        lineEnd: 20,
        tokens: 50,
      };

      state.addReference(ref);

      expect(useContextStore.getState().references).toHaveLength(1);
      expect(useContextStore.getState().references[0]).toEqual(ref);
    });

    it('should add multiple references', () => {
      const state = useContextStore.getState();
      const ref1: ContextReference = {
        id: 'ref-1',
        type: 'function',
        name: 'getData',
        path: '/src/api.ts',
        tokens: 50,
      };
      const ref2: ContextReference = {
        id: 'ref-2',
        type: 'class',
        name: 'ApiClient',
        path: '/src/api.ts',
        tokens: 100,
      };

      state.addReference(ref1);
      state.addReference(ref2);

      expect(useContextStore.getState().references).toHaveLength(2);
    });

    it('should remove a reference', () => {
      const state = useContextStore.getState();
      const ref: ContextReference = {
        id: 'ref-1',
        type: 'function',
        name: 'getData',
        path: '/src/api.ts',
        tokens: 50,
      };

      state.addReference(ref);
      expect(useContextStore.getState().references).toHaveLength(1);

      state.removeReference('ref-1');
      expect(useContextStore.getState().references).toHaveLength(0);
    });

    it('should clear all references', () => {
      const state = useContextStore.getState();
      const ref1: ContextReference = {
        id: 'ref-1',
        type: 'function',
        name: 'getData',
        path: '/src/api.ts',
        tokens: 50,
      };
      const ref2: ContextReference = {
        id: 'ref-2',
        type: 'class',
        name: 'ApiClient',
        path: '/src/api.ts',
        tokens: 100,
      };

      state.addReference(ref1);
      state.addReference(ref2);
      expect(useContextStore.getState().references).toHaveLength(2);

      state.clearReferences();
      expect(useContextStore.getState().references).toHaveLength(0);
    });
  });

  describe('Token Management', () => {
    it('should set max tokens', () => {
      const state = useContextStore.getState();
      state.setMaxTokens(16000);

      expect(useContextStore.getState().maxTokens).toBe(16000);
    });

    it('should get available tokens', () => {
      const state = useContextStore.getState();
      const file: ContextFile = {
        id: 'file-1',
        path: '/src/main.ts',
        name: 'main.ts',
        tokens: 2000,
        language: 'typescript',
      };

      state.addFile(file);
      const available = state.getAvailableTokens();

      expect(available).toBe(6000); // 8000 - 2000
    });

    it('should check if can add file', () => {
      const state = useContextStore.getState();
      const file: ContextFile = {
        id: 'file-1',
        path: '/src/main.ts',
        name: 'main.ts',
        tokens: 7500,
        language: 'typescript',
      };

      state.addFile(file);

      expect(state.canAddFile(400)).toBe(true); // 7500 + 400 = 7900 <= 8000
      expect(state.canAddFile(600)).toBe(false); // 7500 + 600 = 8100 > 8000
    });

    it('should get token usage', () => {
      const state = useContextStore.getState();
      const file1: ContextFile = {
        id: 'file-1',
        path: '/src/file1.ts',
        name: 'file1.ts',
        tokens: 1000,
        language: 'typescript',
      };
      const file2: ContextFile = {
        id: 'file-2',
        path: '/src/file2.ts',
        name: 'file2.ts',
        tokens: 2000,
        language: 'typescript',
      };

      state.addFile(file1);
      state.addFile(file2);

      expect(state.getTokenUsage()).toBe(3000);
    });

    it('should get token percentage', () => {
      const state = useContextStore.getState();
      const file: ContextFile = {
        id: 'file-1',
        path: '/src/main.ts',
        name: 'main.ts',
        tokens: 4000,
        language: 'typescript',
      };

      state.addFile(file);
      const percentage = state.getTokenPercentage();

      expect(percentage).toBe(50); // 4000 / 8000 * 100
    });

    it('should check if has room for tokens', () => {
      const state = useContextStore.getState();
      const file: ContextFile = {
        id: 'file-1',
        path: '/src/main.ts',
        name: 'main.ts',
        tokens: 6000,
        language: 'typescript',
      };

      state.addFile(file);

      expect(state.hasRoom(1500)).toBe(true); // 6000 + 1500 = 7500 <= 8000
      expect(state.hasRoom(2500)).toBe(false); // 6000 + 2500 = 8500 > 8000
    });
  });

  describe('Getters', () => {
    it('should get context size', () => {
      const state = useContextStore.getState();
      const file1: ContextFile = {
        id: 'file-1',
        path: '/src/file1.ts',
        name: 'file1.ts',
        tokens: 100,
        language: 'typescript',
      };
      const file2: ContextFile = {
        id: 'file-2',
        path: '/src/file2.ts',
        name: 'file2.ts',
        tokens: 200,
        language: 'typescript',
      };

      state.addFile(file1);
      state.addFile(file2);

      expect(state.getContextSize()).toBe(2);
    });
  });

  describe('Edge Cases', () => {
    it('should handle adding file with zero tokens', () => {
      const state = useContextStore.getState();
      const file: ContextFile = {
        id: 'file-1',
        path: '/src/empty.ts',
        name: 'empty.ts',
        tokens: 0,
        language: 'typescript',
      };

      state.addFile(file);

      expect(useContextStore.getState().files).toHaveLength(1);
      expect(useContextStore.getState().totalTokens).toBe(0);
    });

    it('should handle removing non-existent file', () => {
      const state = useContextStore.getState();
      state.removeFile('non-existent');

      expect(useContextStore.getState().files).toHaveLength(0);
      expect(useContextStore.getState().totalTokens).toBe(0);
    });

    it('should handle updating non-existent file', () => {
      const state = useContextStore.getState();
      state.updateFile('non-existent', { name: 'updated.ts' });

      expect(useContextStore.getState().files).toHaveLength(0);
    });

    it('should handle file without language property', () => {
      const state = useContextStore.getState();
      const file: ContextFile = {
        id: 'file-1',
        path: '/src/noext',
        name: 'noext',
        tokens: 100,
      };

      state.addFile(file);

      expect(useContextStore.getState().files[0].language).toBeUndefined();
    });

    it('should handle file with content property', () => {
      const state = useContextStore.getState();
      const file: ContextFile = {
        id: 'file-1',
        path: '/src/main.ts',
        name: 'main.ts',
        content: 'console.log("hello");',
        tokens: 100,
        language: 'typescript',
      };

      state.addFile(file);

      expect(useContextStore.getState().files[0].content).toBe('console.log("hello");');
    });

    it('should handle removing reference that does not exist', () => {
      const state = useContextStore.getState();
      state.removeReference('non-existent');

      expect(useContextStore.getState().references).toHaveLength(0);
    });

    it('should handle very large token values', () => {
      const state = useContextStore.getState();
      state.setMaxTokens(1000000);

      const file: ContextFile = {
        id: 'file-1',
        path: '/src/large.ts',
        name: 'large.ts',
        tokens: 500000,
        language: 'typescript',
      };

      state.addFile(file);

      expect(useContextStore.getState().totalTokens).toBe(500000);
      expect(state.getTokenPercentage()).toBe(50);
    });

    it('should handle maxTokens of 0', () => {
      const state = useContextStore.getState();
      state.setMaxTokens(0);

      const file: ContextFile = {
        id: 'file-1',
        path: '/src/main.ts',
        name: 'main.ts',
        tokens: 1,
        language: 'typescript',
      };

      state.addFile(file);

      expect(useContextStore.getState().files).toHaveLength(0);
    });
  });

  describe('Complex Scenarios', () => {
    it('should handle multiple files with precise token tracking', () => {
      const state = useContextStore.getState();
      const files: ContextFile[] = [
        { id: 'f1', path: '/src/f1.ts', name: 'f1.ts', tokens: 1500, language: 'typescript' },
        { id: 'f2', path: '/src/f2.ts', name: 'f2.ts', tokens: 2000, language: 'typescript' },
        { id: 'f3', path: '/src/f3.ts', name: 'f3.ts', tokens: 2500, language: 'typescript' },
        { id: 'f4', path: '/src/f4.ts', name: 'f4.ts', tokens: 2000, language: 'typescript' },
      ];

      files.forEach((file) => state.addFile(file));

      expect(useContextStore.getState().totalTokens).toBe(8000);
      expect(useContextStore.getState().files).toHaveLength(4);

      // Remove middle file
      state.removeFile('f2');
      expect(useContextStore.getState().totalTokens).toBe(6000);

      // Try to add new file
      const newFile: ContextFile = {
        id: 'f5',
        path: '/src/f5.ts',
        name: 'f5.ts',
        tokens: 1500,
        language: 'typescript',
      };
      state.addFile(newFile);

      expect(useContextStore.getState().totalTokens).toBe(7500);
      expect(useContextStore.getState().files).toHaveLength(4);
    });

    it('should maintain references and files independently', () => {
      const state = useContextStore.getState();

      const file: ContextFile = {
        id: 'file-1',
        path: '/src/main.ts',
        name: 'main.ts',
        tokens: 100,
        language: 'typescript',
      };

      const ref: ContextReference = {
        id: 'ref-1',
        type: 'function',
        name: 'getData',
        path: '/src/main.ts',
        tokens: 50,
      };

      state.addFile(file);
      state.addReference(ref);

      state.removeFile('file-1');

      expect(useContextStore.getState().files).toHaveLength(0);
      expect(useContextStore.getState().references).toHaveLength(1); // Reference still exists
    });
  });
});
