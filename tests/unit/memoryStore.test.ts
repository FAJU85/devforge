import { describe, it, expect, beforeEach } from 'vitest';
import { useMemoryStore, MemoryItem, ConversationMemory } from '../../src/stores/memoryStore';

describe('Memory Store', () => {
  beforeEach(() => {
    useMemoryStore.setState({
      memories: [],
      conversationMemories: [],
      recentContext: [],
      maxRecentContext: 20,
    });
  });

  describe('Initial State', () => {
    it('should have correct initial state', () => {
      const state = useMemoryStore.getState();
      expect(state.memories).toEqual([]);
      expect(state.conversationMemories).toEqual([]);
      expect(state.recentContext).toEqual([]);
      expect(state.maxRecentContext).toBe(20);
    });
  });

  describe('Memory Item Management', () => {
    it('should add a memory item', () => {
      const state = useMemoryStore.getState();
      const id = state.addMemory({
        key: 'user_preference',
        value: 'dark_mode',
        category: 'preference',
      });

      expect(id).toMatch(/^mem-\d+$/);
      expect(useMemoryStore.getState().memories).toHaveLength(1);
      expect(useMemoryStore.getState().memories[0].key).toBe('user_preference');
    });

    it('should add memory with all properties', () => {
      const state = useMemoryStore.getState();
      const id = state.addMemory({
        key: 'project_info',
        value: { name: 'DevForge', language: 'TypeScript' },
        category: 'project',
        metadata: { source: 'user_input' },
      });

      const memory = useMemoryStore.getState().memories[0];
      expect(memory.id).toBe(id);
      expect(memory.key).toBe('project_info');
      expect(memory.category).toBe('project');
      expect(memory.metadata?.source).toBe('user_input');
      expect(memory.createdAt).toBeInstanceOf(Date);
      expect(memory.updatedAt).toBeInstanceOf(Date);
    });

    it('should update a memory item', () => {
      const state = useMemoryStore.getState();
      const id = state.addMemory({
        key: 'user_preference',
        value: 'dark_mode',
        category: 'preference',
      });

      state.updateMemory(id, { value: 'light_mode' });

      const updated = useMemoryStore.getState().memories[0];
      expect(updated.value).toBe('light_mode');
      expect(updated.updatedAt.getTime()).toBeGreaterThan(updated.createdAt.getTime());
    });

    it('should remove a memory item', () => {
      const state = useMemoryStore.getState();
      const id = state.addMemory({
        key: 'user_preference',
        value: 'dark_mode',
        category: 'preference',
      });

      expect(useMemoryStore.getState().memories).toHaveLength(1);

      state.removeMemory(id);
      expect(useMemoryStore.getState().memories).toHaveLength(0);
    });

    it('should get memory by key', () => {
      const state = useMemoryStore.getState();
      state.addMemory({
        key: 'user_name',
        value: 'Alice',
        category: 'user',
      });

      const memory = state.getMemory('user_name');
      expect(memory).toBeDefined();
      expect(memory?.value).toBe('Alice');
    });

    it('should return undefined for non-existent key', () => {
      const state = useMemoryStore.getState();
      const memory = state.getMemory('non_existent');

      expect(memory).toBeUndefined();
    });
  });

  describe('Conversation Memory', () => {
    it('should save conversation memory', () => {
      const state = useMemoryStore.getState();
      const convMemory: Omit<ConversationMemory, 'createdAt' | 'updatedAt'> = {
        conversationId: 'conv-123',
        summary: 'Discussed project architecture',
        keyDecisions: ['Use TypeScript', 'Implement Zustand'],
        relatedFiles: ['src/stores/chatStore.ts', 'src/components/Chat.tsx'],
      };

      state.saveConversationMemory(convMemory);

      expect(useMemoryStore.getState().conversationMemories).toHaveLength(1);
    });

    it('should update existing conversation memory', () => {
      const state = useMemoryStore.getState();
      const convId = 'conv-123';

      state.saveConversationMemory({
        conversationId: convId,
        summary: 'Initial summary',
        keyDecisions: [],
        relatedFiles: [],
      });

      state.saveConversationMemory({
        conversationId: convId,
        summary: 'Updated summary',
        keyDecisions: ['Decision 1'],
        relatedFiles: ['file.ts'],
      });

      expect(useMemoryStore.getState().conversationMemories).toHaveLength(1);
      const memory = useMemoryStore.getState().conversationMemories[0];
      expect(memory.summary).toBe('Updated summary');
      expect(memory.keyDecisions).toHaveLength(1);
    });

    it('should remove conversation memory', () => {
      const state = useMemoryStore.getState();
      state.saveConversationMemory({
        conversationId: 'conv-123',
        summary: 'Test',
        keyDecisions: [],
        relatedFiles: [],
      });

      expect(useMemoryStore.getState().conversationMemories).toHaveLength(1);

      state.removeConversationMemory('conv-123');
      expect(useMemoryStore.getState().conversationMemories).toHaveLength(0);
    });

    it('should get conversation memory by ID', () => {
      const state = useMemoryStore.getState();
      state.saveConversationMemory({
        conversationId: 'conv-123',
        summary: 'Test summary',
        keyDecisions: ['Decision 1'],
        relatedFiles: ['file.ts'],
      });

      const memory = state.getConversationMemory('conv-123');
      expect(memory).toBeDefined();
      expect(memory?.summary).toBe('Test summary');
    });

    it('should return undefined for non-existent conversation', () => {
      const state = useMemoryStore.getState();
      const memory = state.getConversationMemory('non-existent');

      expect(memory).toBeUndefined();
    });
  });

  describe('Recent Context Management', () => {
    it('should add to recent context', () => {
      const state = useMemoryStore.getState();
      state.addToRecentContext('context-1');

      expect(useMemoryStore.getState().recentContext).toHaveLength(1);
      expect(useMemoryStore.getState().recentContext[0]).toBe('context-1');
    });

    it('should maintain order with newest first', () => {
      const state = useMemoryStore.getState();
      state.addToRecentContext('context-1');
      state.addToRecentContext('context-2');
      state.addToRecentContext('context-3');

      const context = useMemoryStore.getState().recentContext;
      expect(context[0]).toBe('context-3');
      expect(context[1]).toBe('context-2');
      expect(context[2]).toBe('context-1');
    });

    it('should respect max recent context limit', () => {
      const state = useMemoryStore.getState();

      // Add 25 items (exceeds maxRecentContext of 20)
      for (let i = 1; i <= 25; i++) {
        state.addToRecentContext(`context-${i}`);
      }

      const context = useMemoryStore.getState().recentContext;
      expect(context).toHaveLength(20);
      expect(context[0]).toBe('context-25'); // Most recent
      expect(context[19]).toBe('context-6'); // Oldest kept
    });

    it('should get recent context', () => {
      const state = useMemoryStore.getState();
      state.addToRecentContext('context-1');
      state.addToRecentContext('context-2');

      const context = state.getRecentContext();
      expect(context).toHaveLength(2);
    });

    it('should clear recent context', () => {
      const state = useMemoryStore.getState();
      state.addToRecentContext('context-1');
      state.addToRecentContext('context-2');

      expect(useMemoryStore.getState().recentContext).toHaveLength(2);

      state.clearRecentContext();
      expect(useMemoryStore.getState().recentContext).toHaveLength(0);
    });
  });

  describe('Memory Queries', () => {
    beforeEach(() => {
      const state = useMemoryStore.getState();
      state.addMemory({
        key: 'user_name',
        value: 'Alice',
        category: 'user',
      });
      state.addMemory({
        key: 'project_name',
        value: 'DevForge',
        category: 'project',
      });
      state.addMemory({
        key: 'theme',
        value: 'dark',
        category: 'preference',
      });
      state.addMemory({
        key: 'language',
        value: 'en',
        category: 'preference',
      });
    });

    it('should get memories by category', () => {
      const state = useMemoryStore.getState();
      const userMemories = state.getMemoriesByCategory('user');

      expect(userMemories).toHaveLength(1);
      expect(userMemories[0].key).toBe('user_name');
    });

    it('should get all memories of a category', () => {
      const state = useMemoryStore.getState();
      const preferences = state.getMemoriesByCategory('preference');

      expect(preferences).toHaveLength(2);
      expect(preferences.some((m) => m.key === 'theme')).toBe(true);
      expect(preferences.some((m) => m.key === 'language')).toBe(true);
    });

    it('should get all memories', () => {
      const state = useMemoryStore.getState();
      const all = state.getAllMemories();

      expect(all).toHaveLength(4);
    });

    it('should get memory size', () => {
      const state = useMemoryStore.getState();
      const size = state.getMemorySize();

      expect(size).toBe(4); // 4 memories + 0 conversation memories
    });

    it('should include conversation memories in memory size', () => {
      const state = useMemoryStore.getState();
      state.saveConversationMemory({
        conversationId: 'conv-1',
        summary: 'Test',
        keyDecisions: [],
        relatedFiles: [],
      });

      const size = state.getMemorySize();
      expect(size).toBe(5); // 4 memories + 1 conversation memory
    });
  });

  describe('Edge Cases', () => {
    it('should handle null values', () => {
      const state = useMemoryStore.getState();
      const id = state.addMemory({
        key: 'nullable_field',
        value: null,
        category: 'user',
      });

      const memory = state.getMemory('nullable_field');
      expect(memory?.value).toBeNull();
    });

    it('should handle complex object values', () => {
      const state = useMemoryStore.getState();
      const complexValue = {
        nested: {
          deep: {
            value: 'test',
            array: [1, 2, 3],
          },
        },
      };

      state.addMemory({
        key: 'complex',
        value: complexValue,
        category: 'context',
      });

      const memory = state.getMemory('complex');
      expect(memory?.value.nested.deep.value).toBe('test');
      expect(memory?.value.nested.deep.array).toEqual([1, 2, 3]);
    });

    it('should handle array values', () => {
      const state = useMemoryStore.getState();
      const arrayValue = ['item1', 'item2', 'item3'];

      state.addMemory({
        key: 'items',
        value: arrayValue,
        category: 'context',
      });

      const memory = state.getMemory('items');
      expect(Array.isArray(memory?.value)).toBe(true);
      expect(memory?.value).toHaveLength(3);
    });

    it('should handle empty strings', () => {
      const state = useMemoryStore.getState();
      state.addMemory({
        key: 'empty',
        value: '',
        category: 'user',
      });

      const memory = state.getMemory('empty');
      expect(memory?.value).toBe('');
    });

    it('should handle duplicate keys', () => {
      const state = useMemoryStore.getState();
      const id1 = state.addMemory({
        key: 'duplicate',
        value: 'value1',
        category: 'user',
      });
      const id2 = state.addMemory({
        key: 'duplicate',
        value: 'value2',
        category: 'user',
      });

      expect(useMemoryStore.getState().memories).toHaveLength(2);
      // getMemory should return the first one
      expect(state.getMemory('duplicate')?.id).toBe(id1);
    });

    it('should handle special characters in keys and values', () => {
      const state = useMemoryStore.getState();
      state.addMemory({
        key: 'key-with-special!@#$%',
        value: '<script>alert("xss")</script>',
        category: 'context',
      });

      const memory = state.getMemory('key-with-special!@#$%');
      expect(memory?.value).toBe('<script>alert("xss")</script>');
    });
  });

  describe('Multiple Concurrent Operations', () => {
    it('should handle multiple memory items and conversations', () => {
      const state = useMemoryStore.getState();

      // Add multiple memories
      const id1 = state.addMemory({
        key: 'key1',
        value: 'value1',
        category: 'user',
      });
      const id2 = state.addMemory({
        key: 'key2',
        value: 'value2',
        category: 'project',
      });

      // Add conversation memories
      state.saveConversationMemory({
        conversationId: 'conv-1',
        summary: 'Summary 1',
        keyDecisions: [],
        relatedFiles: [],
      });
      state.saveConversationMemory({
        conversationId: 'conv-2',
        summary: 'Summary 2',
        keyDecisions: [],
        relatedFiles: [],
      });

      // Add recent context
      state.addToRecentContext('context-1');
      state.addToRecentContext('context-2');

      expect(useMemoryStore.getState().memories).toHaveLength(2);
      expect(useMemoryStore.getState().conversationMemories).toHaveLength(2);
      expect(useMemoryStore.getState().recentContext).toHaveLength(2);
      expect(state.getMemorySize()).toBe(4);
    });

    it('should handle updates without affecting other items', () => {
      const state = useMemoryStore.getState();
      const id1 = state.addMemory({
        key: 'key1',
        value: 'value1',
        category: 'user',
      });
      const id2 = state.addMemory({
        key: 'key2',
        value: 'value2',
        category: 'user',
      });

      state.updateMemory(id1, { value: 'updated1' });

      const mem1 = state.getMemory('key1');
      const mem2 = state.getMemory('key2');

      expect(mem1?.value).toBe('updated1');
      expect(mem2?.value).toBe('value2');
    });
  });
});
