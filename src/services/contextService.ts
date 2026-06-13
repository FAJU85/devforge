/**
 * Context Service - integrates ContextStore with API calls
 */

import { useContextStore } from '../stores/contextStore';
import { RepositoryClient } from '../api/repo';
import type { ContextFile } from '../stores/contextStore';

export class ContextService {
  private repoClient: RepositoryClient;
  private contextStore: ReturnType<typeof useContextStore>;

  constructor(apiBaseUrl: string = 'http://localhost:3000/api') {
    this.repoClient = new RepositoryClient(apiBaseUrl);
    this.contextStore = useContextStore();
  }

  async addFileToContext(repoPath: string, filePath: string): Promise<ContextFile | null> {
    try {
      // Get file content
      const fileResponse = await this.repoClient.getFileContent(repoPath, filePath);

      if (fileResponse.error || !fileResponse.data) {
        throw new Error(fileResponse.error || 'Failed to load file');
      }

      const file = fileResponse.data;
      const tokens = this.estimateTokens(file.content || '');

      // Check if there's room in context
      if (!this.contextStore.canAddFile(tokens)) {
        throw new Error(
          `File would exceed context limit. Available: ${this.contextStore.getAvailableTokens()} tokens, Required: ${tokens} tokens`
        );
      }

      // Create context file
      const contextFile: ContextFile = {
        id: `ctx-${Date.now()}`,
        path: file.path,
        name: file.name,
        content: file.content,
        tokens,
        language: file.language,
      };

      // Add to store
      this.contextStore.addFile(contextFile);

      return contextFile;
    } catch (error) {
      throw new Error(`Failed to add file to context: ${error}`);
    }
  }

  async addMultipleFilesToContext(
    repoPath: string,
    filePaths: string[]
  ): Promise<ContextFile[]> {
    const added: ContextFile[] = [];

    for (const filePath of filePaths) {
      try {
        const file = await this.addFileToContext(repoPath, filePath);
        if (file) {
          added.push(file);
        }
      } catch (error) {
        console.warn(`Failed to add ${filePath} to context:`, error);
      }
    }

    return added;
  }

  async removeFileFromContext(fileId: string): Promise<boolean> {
    try {
      this.contextStore.removeFile(fileId);
      return true;
    } catch (error) {
      throw new Error(`Failed to remove file from context: ${error}`);
    }
  }

  async updateFileInContext(fileId: string, content: string): Promise<boolean> {
    try {
      const newTokens = this.estimateTokens(content);
      this.contextStore.updateFile(fileId, { content, tokens: newTokens });
      return true;
    } catch (error) {
      throw new Error(`Failed to update file in context: ${error}`);
    }
  }

  clearContext(): void {
    this.contextStore.clearFiles();
    this.contextStore.clearReferences();
  }

  getContextSummary(): {
    filesCount: number;
    totalTokens: number;
    availableTokens: number;
    percentageUsed: number;
    maxTokens: number;
  } {
    const store = this.contextStore;
    return {
      filesCount: store.getContextSize(),
      totalTokens: store.getTokenUsage(),
      availableTokens: store.getAvailableTokens(),
      percentageUsed: store.getTokenPercentage(),
      maxTokens: store.maxTokens,
    };
  }

  setMaxContextTokens(max: number): void {
    this.contextStore.setMaxTokens(max);
  }

  getAvailableTokens(): number {
    return this.contextStore.getAvailableTokens();
  }

  hasRoom(tokens: number): boolean {
    return this.contextStore.hasRoom(tokens);
  }

  async searchAndAddFiles(
    repoPath: string,
    query: string,
    maxFiles: number = 5
  ): Promise<ContextFile[]> {
    try {
      const searchResponse = await this.repoClient.searchFiles(repoPath, query);

      if (searchResponse.error) {
        throw new Error(searchResponse.error);
      }

      const files = searchResponse.data || [];
      const results = files.slice(0, maxFiles);
      const added: ContextFile[] = [];

      for (const result of results) {
        try {
          const file = await this.addFileToContext(repoPath, result.path);
          if (file) {
            added.push(file);
          }
        } catch (error) {
          console.warn(`Failed to add ${result.path}:`, error);
        }
      }

      return added;
    } catch (error) {
      throw new Error(`Failed to search and add files: ${error}`);
    }
  }

  async addRelatedFiles(
    repoPath: string,
    filePath: string,
    maxFiles: number = 5
  ): Promise<ContextFile[]> {
    try {
      // Extract potential related patterns from filename
      const filenameParts = filePath.split('/').pop()?.split('.')[0] || '';
      const searchResults = await this.repoClient.searchFiles(repoPath, filenameParts);

      if (searchResults.error) {
        throw new Error(searchResults.error);
      }

      const files = searchResults.data || [];
      const added: ContextFile[] = [];

      for (const file of files.slice(0, maxFiles)) {
        try {
          const contextFile = await this.addFileToContext(repoPath, file.path);
          if (contextFile) {
            added.push(contextFile);
          }
        } catch (error) {
          console.warn(`Failed to add ${file.path}:`, error);
        }
      }

      return added;
    } catch (error) {
      throw new Error(`Failed to add related files: ${error}`);
    }
  }

  private estimateTokens(content: string): number {
    return Math.ceil(content.length / 4);
  }

  setBaseUrl(url: string): void {
    this.repoClient.setBaseUrl(url);
  }

  setAuthToken(token: string): void {
    this.repoClient.setAuthHeader(token, 'Bearer');
  }
}
