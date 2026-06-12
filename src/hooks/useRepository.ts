/**
 * useRepository Hook - custom hook for repository operations
 */

import { useCallback } from 'react';
import { useRepoStore } from '../stores/repoStore';
import { RepositoryService } from '../services/repoService';

export interface UseRepositoryReturn {
  // State
  repositories: ReturnType<typeof useRepoStore>['repositories'];
  fileTree: ReturnType<typeof useRepoStore>['fileTree'];
  openFiles: ReturnType<typeof useRepoStore>['openFiles'];

  // Repository
  loadRepository: (path: string) => Promise<any>;
  loadFileTree: (repoPath: string, depth?: number) => Promise<any>;
  getFileContent: (repoPath: string, filePath: string) => Promise<any>;

  // Files
  listFiles: (repoPath: string, dirPath?: string) => Promise<any[]>;
  searchFiles: (repoPath: string, query: string, fileType?: string) => Promise<any[]>;
  findSymbol: (repoPath: string, symbol: string) => Promise<any[]>;

  // Analysis
  getLanguages: (repoPath: string) => Promise<Record<string, number> | null>;
  analyzeRepository: (repoPath: string) => Promise<any>;
  getCodeStats: (repoPath: string) => Promise<any>;

  // Write Operations
  writeFile: (repoPath: string, filePath: string, content: string) => Promise<any>;
  deleteFile: (repoPath: string, filePath: string) => Promise<boolean>;

  // File Tab Management
  toggleFile: (repoPath: string, filePath: string) => void;
  closeFile: (repoPath: string, filePath: string) => void;
  getFile: (repoPath: string, filePath: string) => any;
}

export function useRepository(apiBaseUrl: string = 'http://localhost:3000/api'): UseRepositoryReturn {
  const repoStore = useRepoStore();
  const repoService = new RepositoryService(apiBaseUrl);

  const loadRepository = useCallback(
    async (path: string) => {
      try {
        return await repoService.loadRepository(path);
      } catch (error) {
        console.error('Failed to load repository:', error);
        throw error;
      }
    },
    [repoService]
  );

  const loadFileTree = useCallback(
    async (repoPath: string, depth: number = 3) => {
      try {
        return await repoService.loadFileTree(repoPath, depth);
      } catch (error) {
        console.error('Failed to load file tree:', error);
        throw error;
      }
    },
    [repoService]
  );

  const getFileContent = useCallback(
    async (repoPath: string, filePath: string) => {
      try {
        return await repoService.getFileContent(repoPath, filePath);
      } catch (error) {
        console.error('Failed to get file content:', error);
        throw error;
      }
    },
    [repoService]
  );

  const listFiles = useCallback(
    async (repoPath: string, dirPath?: string) => {
      try {
        return await repoService.listFiles(repoPath, dirPath);
      } catch (error) {
        console.error('Failed to list files:', error);
        throw error;
      }
    },
    [repoService]
  );

  const searchFiles = useCallback(
    async (repoPath: string, query: string, fileType?: string) => {
      try {
        return await repoService.searchFiles(repoPath, query, fileType);
      } catch (error) {
        console.error('Failed to search files:', error);
        throw error;
      }
    },
    [repoService]
  );

  const findSymbol = useCallback(
    async (repoPath: string, symbol: string) => {
      try {
        return await repoService.findSymbol(repoPath, symbol);
      } catch (error) {
        console.error('Failed to find symbol:', error);
        throw error;
      }
    },
    [repoService]
  );

  const getLanguages = useCallback(
    async (repoPath: string) => {
      try {
        return await repoService.getLanguages(repoPath);
      } catch (error) {
        console.error('Failed to get languages:', error);
        throw error;
      }
    },
    [repoService]
  );

  const analyzeRepository = useCallback(
    async (repoPath: string) => {
      try {
        return await repoService.analyzeRepository(repoPath);
      } catch (error) {
        console.error('Failed to analyze repository:', error);
        throw error;
      }
    },
    [repoService]
  );

  const getCodeStats = useCallback(
    async (repoPath: string) => {
      try {
        return await repoService.getCodeStats(repoPath);
      } catch (error) {
        console.error('Failed to get code stats:', error);
        throw error;
      }
    },
    [repoService]
  );

  const writeFile = useCallback(
    async (repoPath: string, filePath: string, content: string) => {
      try {
        return await repoService.writeFile(repoPath, filePath, content);
      } catch (error) {
        console.error('Failed to write file:', error);
        throw error;
      }
    },
    [repoService]
  );

  const deleteFile = useCallback(
    async (repoPath: string, filePath: string) => {
      try {
        return await repoService.deleteFile(repoPath, filePath);
      } catch (error) {
        console.error('Failed to delete file:', error);
        throw error;
      }
    },
    [repoService]
  );

  const toggleFile = useCallback(
    (repoPath: string, filePath: string) => {
      repoStore.toggleFile(repoPath, filePath);
    },
    [repoStore]
  );

  const closeFile = useCallback(
    (repoPath: string, filePath: string) => {
      repoStore.closeFile(repoPath, filePath);
    },
    [repoStore]
  );

  const getFile = useCallback(
    (repoPath: string, filePath: string) => {
      return repoStore.getFile(repoPath, filePath);
    },
    [repoStore]
  );

  return {
    repositories: repoStore.repositories,
    fileTree: repoStore.fileTree,
    openFiles: repoStore.openFiles,
    loadRepository,
    loadFileTree,
    getFileContent,
    listFiles,
    searchFiles,
    findSymbol,
    getLanguages,
    analyzeRepository,
    getCodeStats,
    writeFile,
    deleteFile,
    toggleFile,
    closeFile,
    getFile,
  };
}
