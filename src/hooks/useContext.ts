/**
 * useContext Hook - custom hook for context management (avoid conflict with React.useContext)
 */

import { useCallback } from 'react';
import { useContextStore } from '../stores/contextStore';
import { ContextService } from '../services/contextService';

export interface UseContextValue {
  // State
  files: ReturnType<typeof useContextStore>['files'];
  totalTokens: number;
  availableTokens: number;
  tokenPercentage: number;
  maxTokens: number;

  // File Management
  addFile: (repoPath: string, filePath: string) => Promise<any>;
  addMultipleFiles: (repoPath: string, filePaths: string[]) => Promise<any[]>;
  removeFile: (fileId: string) => Promise<boolean>;
  updateFile: (fileId: string, content: string) => Promise<boolean>;
  clearContext: () => void;

  // Search & Discovery
  searchAndAddFiles: (repoPath: string, query: string, maxFiles?: number) => Promise<any[]>;
  addRelatedFiles: (repoPath: string, filePath: string, maxFiles?: number) => Promise<any[]>;

  // Information
  getContextSummary: () => any;
  canAddFile: (tokens: number) => boolean;
  hasRoom: (tokens: number) => boolean;

  // Configuration
  setMaxTokens: (max: number) => void;
}

export function useContextValue(apiBaseUrl: string = 'http://localhost:3000/api'): UseContextValue {
  const contextStore = useContextStore();
  const contextService = new ContextService(apiBaseUrl);

  const addFile = useCallback(
    async (repoPath: string, filePath: string) => {
      try {
        return await contextService.addFileToContext(repoPath, filePath);
      } catch (error) {
        console.error('Failed to add file to context:', error);
        throw error;
      }
    },
    [contextService]
  );

  const addMultipleFiles = useCallback(
    async (repoPath: string, filePaths: string[]) => {
      try {
        return await contextService.addMultipleFilesToContext(repoPath, filePaths);
      } catch (error) {
        console.error('Failed to add multiple files to context:', error);
        throw error;
      }
    },
    [contextService]
  );

  const removeFile = useCallback(
    async (fileId: string) => {
      try {
        return await contextService.removeFileFromContext(fileId);
      } catch (error) {
        console.error('Failed to remove file from context:', error);
        throw error;
      }
    },
    [contextService]
  );

  const updateFile = useCallback(
    async (fileId: string, content: string) => {
      try {
        return await contextService.updateFileInContext(fileId, content);
      } catch (error) {
        console.error('Failed to update file in context:', error);
        throw error;
      }
    },
    [contextService]
  );

  const clearContext = useCallback(() => {
    contextService.clearContext();
  }, [contextService]);

  const searchAndAddFiles = useCallback(
    async (repoPath: string, query: string, maxFiles: number = 5) => {
      try {
        return await contextService.searchAndAddFiles(repoPath, query, maxFiles);
      } catch (error) {
        console.error('Failed to search and add files:', error);
        throw error;
      }
    },
    [contextService]
  );

  const addRelatedFiles = useCallback(
    async (repoPath: string, filePath: string, maxFiles: number = 5) => {
      try {
        return await contextService.addRelatedFiles(repoPath, filePath, maxFiles);
      } catch (error) {
        console.error('Failed to add related files:', error);
        throw error;
      }
    },
    [contextService]
  );

  const getContextSummary = useCallback(() => {
    return contextService.getContextSummary();
  }, [contextService]);

  const canAddFile = useCallback(
    (tokens: number) => {
      return contextStore.canAddFile(tokens);
    },
    [contextStore]
  );

  const hasRoom = useCallback(
    (tokens: number) => {
      return contextStore.hasRoom(tokens);
    },
    [contextStore]
  );

  const setMaxTokens = useCallback(
    (max: number) => {
      contextService.setMaxContextTokens(max);
    },
    [contextService]
  );

  return {
    files: contextStore.files,
    totalTokens: contextStore.totalTokens,
    availableTokens: contextStore.getAvailableTokens(),
    tokenPercentage: contextStore.getTokenPercentage(),
    maxTokens: contextStore.maxTokens,
    addFile,
    addMultipleFiles,
    removeFile,
    updateFile,
    clearContext,
    searchAndAddFiles,
    addRelatedFiles,
    getContextSummary,
    canAddFile,
    hasRoom,
    setMaxTokens,
  };
}
