/**
 * Repository Store - repository state and file management
 */

import { create } from 'zustand';
import { devtools, persist } from 'zustand/middleware';

export interface FileNode {
  id: string;
  name: string;
  path: string;
  type: 'file' | 'folder';
  size?: number;
  language?: string;
  lastModified?: Date;
  isOpen?: boolean;
  children?: FileNode[];
}

export interface Repository {
  id: string;
  name: string;
  owner: string;
  url: string;
  branch: string;
  lastSynced?: Date;
}

export interface RepoState {
  // Current repository
  repositories: Repository[];
  currentRepoId: string | null;

  // File tree
  fileTree: FileNode[];
  selectedFileId: string | null;
  openFiles: string[]; // file IDs of open tabs

  // Search and filter
  searchQuery: string;
  filteredFiles: FileNode[];

  // Actions
  addRepository: (repo: Repository) => void;
  removeRepository: (id: string) => void;
  setCurrentRepository: (id: string | null) => void;

  // File operations
  setFileTree: (tree: FileNode[]) => void;
  selectFile: (id: string | null) => void;
  openFile: (id: string) => void;
  closeFile: (id: string) => void;
  toggleFolder: (id: string) => void;

  // Search
  setSearchQuery: (query: string) => void;
  searchFiles: (query: string) => FileNode[];

  // Getters
  getCurrentRepository: () => Repository | undefined;
  getFile: (id: string) => FileNode | undefined;
  getOpenFileCount: () => number;
}

export const useRepoStore = create<RepoState>()(
  devtools(
    persist(
      (set, get) => ({
        repositories: [],
        currentRepoId: null,
        fileTree: [],
        selectedFileId: null,
        openFiles: [],
        searchQuery: '',
        filteredFiles: [],

        addRepository: (repo) =>
          set((state) => ({
            repositories: [...state.repositories, repo],
            currentRepoId: state.currentRepoId || repo.id,
          })),

        removeRepository: (id) =>
          set((state) => ({
            repositories: state.repositories.filter((r) => r.id !== id),
            currentRepoId: state.currentRepoId === id ? null : state.currentRepoId,
          })),

        setCurrentRepository: (id) => set({ currentRepoId: id }),

        setFileTree: (tree) => set({ fileTree: tree }),

        selectFile: (id) => set({ selectedFileId: id }),

        openFile: (id) =>
          set((state) => ({
            openFiles: state.openFiles.includes(id) ? state.openFiles : [...state.openFiles, id],
            selectedFileId: id,
          })),

        closeFile: (id) =>
          set((state) => ({
            openFiles: state.openFiles.filter((f) => f !== id),
            selectedFileId: state.selectedFileId === id ? null : state.selectedFileId,
          })),

        toggleFolder: (id) => {
          const findAndToggle = (nodes: FileNode[]): FileNode[] =>
            nodes.map((node) =>
              node.id === id
                ? { ...node, isOpen: !node.isOpen }
                : node.children
                  ? { ...node, children: findAndToggle(node.children) }
                  : node
            );

          set((state) => ({
            fileTree: findAndToggle(state.fileTree),
          }));
        },

        setSearchQuery: (query) => {
          set((state) => ({
            searchQuery: query,
            filteredFiles: get().searchFiles(query),
          }));
        },

        searchFiles: (query) => {
          if (!query) return [];

          const search = (nodes: FileNode[]): FileNode[] => {
            return nodes.flatMap((node) => {
              const matches = node.name.toLowerCase().includes(query.toLowerCase());
              const childMatches = node.children ? search(node.children) : [];
              return matches ? [{ ...node, children: childMatches }] : childMatches;
            });
          };

          return search(get().fileTree);
        },

        getCurrentRepository: () => {
          const state = get();
          return state.repositories.find((r) => r.id === state.currentRepoId);
        },

        getFile: (id) => {
          const find = (nodes: FileNode[]): FileNode | undefined => {
            for (const node of nodes) {
              if (node.id === id) return node;
              if (node.children) {
                const result = find(node.children);
                if (result) return result;
              }
            }
            return undefined;
          };
          return find(get().fileTree);
        },

        getOpenFileCount: () => get().openFiles.length,
      }),
      {
        name: 'repo-store',
        version: 1,
      }
    ),
    { name: 'RepoStore' }
  )
);
