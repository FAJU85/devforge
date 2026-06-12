/**
 * Memory Store - conversation memory and long-term context
 */

import { create } from 'zustand';
import { devtools, persist } from 'zustand/middleware';

export interface MemoryItem {
  id: string;
  key: string;
  value: any;
  category: 'user' | 'project' | 'context' | 'preference';
  createdAt: Date;
  updatedAt: Date;
  metadata?: Record<string, any>;
}

export interface ConversationMemory {
  conversationId: string;
  summary: string;
  keyDecisions: string[];
  relatedFiles: string[];
  createdAt: Date;
  updatedAt: Date;
}

export interface MemoryState {
  // Long-term memory
  memories: MemoryItem[];

  // Conversation memories
  conversationMemories: ConversationMemory[];

  // Recent context
  recentContext: string[];
  maxRecentContext: number;

  // Actions
  addMemory: (item: Omit<MemoryItem, 'id' | 'createdAt' | 'updatedAt'>) => string;
  updateMemory: (id: string, updates: Partial<MemoryItem>) => void;
  removeMemory: (id: string) => void;
  getMemory: (key: string) => MemoryItem | undefined;

  // Conversation memory
  saveConversationMemory: (memory: Omit<ConversationMemory, 'createdAt' | 'updatedAt'>) => void;
  removeConversationMemory: (conversationId: string) => void;
  getConversationMemory: (conversationId: string) => ConversationMemory | undefined;

  // Recent context
  addToRecentContext: (context: string) => void;
  getRecentContext: () => string[];
  clearRecentContext: () => void;

  // Getters
  getMemoriesByCategory: (category: MemoryItem['category']) => MemoryItem[];
  getAllMemories: () => MemoryItem[];
  getMemorySize: () => number;
}

export const useMemoryStore = create<MemoryState>()(
  devtools(
    persist(
      (set, get) => ({
        memories: [],
        conversationMemories: [],
        recentContext: [],
        maxRecentContext: 20,

        addMemory: (item) => {
          const id = `mem-${Date.now()}`;
          const now = new Date();

          set((state) => ({
            memories: [
              ...state.memories,
              {
                ...item,
                id,
                createdAt: now,
                updatedAt: now,
              },
            ],
          }));

          return id;
        },

        updateMemory: (id, updates) =>
          set((state) => ({
            memories: state.memories.map((m) =>
              m.id === id ? { ...m, ...updates, updatedAt: new Date() } : m
            ),
          })),

        removeMemory: (id) =>
          set((state) => ({
            memories: state.memories.filter((m) => m.id !== id),
          })),

        getMemory: (key) => {
          const state = get();
          return state.memories.find((m) => m.key === key);
        },

        saveConversationMemory: (memory) =>
          set((state) => {
            const existing = state.conversationMemories.find(
              (m) => m.conversationId === memory.conversationId
            );

            if (existing) {
              return {
                conversationMemories: state.conversationMemories.map((m) =>
                  m.conversationId === memory.conversationId
                    ? { ...memory, createdAt: m.createdAt, updatedAt: new Date() }
                    : m
                ),
              };
            }

            return {
              conversationMemories: [
                ...state.conversationMemories,
                { ...memory, createdAt: new Date(), updatedAt: new Date() },
              ],
            };
          }),

        removeConversationMemory: (conversationId) =>
          set((state) => ({
            conversationMemories: state.conversationMemories.filter(
              (m) => m.conversationId !== conversationId
            ),
          })),

        getConversationMemory: (conversationId) => {
          const state = get();
          return state.conversationMemories.find((m) => m.conversationId === conversationId);
        },

        addToRecentContext: (context) =>
          set((state) => {
            const updated = [context, ...state.recentContext].slice(0, state.maxRecentContext);
            return { recentContext: updated };
          }),

        getRecentContext: () => get().recentContext,

        clearRecentContext: () => set({ recentContext: [] }),

        getMemoriesByCategory: (category) => {
          const state = get();
          return state.memories.filter((m) => m.category === category);
        },

        getAllMemories: () => get().memories,

        getMemorySize: () => {
          const state = get();
          return state.memories.length + state.conversationMemories.length;
        },
      }),
      {
        name: 'memory-store',
        version: 1,
      }
    ),
    { name: 'MemoryStore' }
  )
);
