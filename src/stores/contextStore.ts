/**
 * Context Store - current context and memory management
 */

import { create } from 'zustand';
import { devtools, persist } from 'zustand/middleware';

export interface ContextFile {
  id: string;
  path: string;
  name: string;
  content?: string;
  tokens: number;
  language?: string;
}

export interface ContextReference {
  id: string;
  type: 'function' | 'class' | 'variable' | 'type' | 'file';
  name: string;
  path: string;
  lineStart?: number;
  lineEnd?: number;
  tokens: number;
}

export interface ContextState {
  // Files in context
  files: ContextFile[];
  totalTokens: number;
  maxTokens: number;

  // References
  references: ContextReference[];

  // Metadata
  createdAt: Date;
  lastUpdated: Date;

  // Actions
  addFile: (file: ContextFile) => void;
  removeFile: (id: string) => void;
  updateFile: (id: string, updates: Partial<ContextFile>) => void;
  clearFiles: () => void;

  // References
  addReference: (ref: ContextReference) => void;
  removeReference: (id: string) => void;
  clearReferences: () => void;

  // Token management
  setMaxTokens: (max: number) => void;
  getAvailableTokens: () => number;
  canAddFile: (tokens: number) => boolean;

  // Getters
  getContextSize: () => number;
  getTokenUsage: () => number;
  getTokenPercentage: () => number;
  hasRoom: (tokens: number) => boolean;
}

export const useContextStore = create<ContextState>()(
  devtools(
    persist(
      (set, get) => ({
        files: [],
        totalTokens: 0,
        maxTokens: 8000,
        references: [],
        createdAt: new Date(),
        lastUpdated: new Date(),

        addFile: (file) =>
          set((state) => {
            const newTotal = state.totalTokens + file.tokens;
            if (newTotal > state.maxTokens) {
              console.warn('Adding file would exceed token limit');
              return state;
            }
            return {
              files: [...state.files, file],
              totalTokens: newTotal,
              lastUpdated: new Date(),
            };
          }),

        removeFile: (id) =>
          set((state) => {
            const file = state.files.find((f) => f.id === id);
            return {
              files: state.files.filter((f) => f.id !== id),
              totalTokens: state.totalTokens - (file?.tokens || 0),
              lastUpdated: new Date(),
            };
          }),

        updateFile: (id, updates) =>
          set((state) => {
            const file = state.files.find((f) => f.id === id);
            if (!file) return state;

            const tokenDiff = (updates.tokens || file.tokens) - file.tokens;
            const newTotal = state.totalTokens + tokenDiff;

            if (newTotal > state.maxTokens) {
              console.warn('Updating file would exceed token limit');
              return state;
            }

            return {
              files: state.files.map((f) => (f.id === id ? { ...f, ...updates } : f)),
              totalTokens: newTotal,
              lastUpdated: new Date(),
            };
          }),

        clearFiles: () =>
          set({
            files: [],
            totalTokens: 0,
            lastUpdated: new Date(),
          }),

        addReference: (ref) =>
          set((state) => ({
            references: [...state.references, ref],
            lastUpdated: new Date(),
          })),

        removeReference: (id) =>
          set((state) => ({
            references: state.references.filter((r) => r.id !== id),
            lastUpdated: new Date(),
          })),

        clearReferences: () =>
          set({
            references: [],
            lastUpdated: new Date(),
          }),

        setMaxTokens: (max) => set({ maxTokens: max }),

        getAvailableTokens: () => {
          const state = get();
          return state.maxTokens - state.totalTokens;
        },

        canAddFile: (tokens) => {
          const state = get();
          return state.totalTokens + tokens <= state.maxTokens;
        },

        getContextSize: () => get().files.length,

        getTokenUsage: () => get().totalTokens,

        getTokenPercentage: () => {
          const state = get();
          return (state.totalTokens / state.maxTokens) * 100;
        },

        hasRoom: (tokens) => {
          const state = get();
          return state.totalTokens + tokens <= state.maxTokens;
        },
      }),
      {
        name: 'context-store',
        version: 1,
      }
    ),
    { name: 'ContextStore' }
  )
);
