/**
 * Repository Service - integrates RepoStore with API calls
 */

import { useRepoStore } from '../stores/repoStore';
import { RepositoryClient } from '../api/repo';
import type { DirectoryTree, FileInfo, SearchResult, RepositoryInfo } from '../api/repo';

export class RepositoryService {
  private repoClient: RepositoryClient;
  private repoStore: ReturnType<typeof useRepoStore>;

  constructor(apiBaseUrl: string = 'http://localhost:3000/api') {
    this.repoClient = new RepositoryClient(apiBaseUrl);
    this.repoStore = useRepoStore();
  }

  async loadRepository(path: string): Promise<RepositoryInfo | null> {
    try {
      const response = await this.repoClient.getRepositoryInfo(path);

      if (response.error || !response.data) {
        throw new Error(response.error || 'Failed to load repository');
      }

      this.repoStore.addRepository({
        id: response.data.path,
        name: response.data.name,
        path: response.data.path,
        isGit: response.data.isGit,
        branch: response.data.currentBranch,
        remoteUrl: response.data.remoteUrl,
        files: [],
      });

      return response.data;
    } catch (error) {
      throw new Error(`Failed to load repository: ${error}`);
    }
  }

  async loadFileTree(repoPath: string, depth: number = 3): Promise<DirectoryTree | null> {
    try {
      const response = await this.repoClient.getDirectoryTree(repoPath, depth);

      if (response.error || !response.data) {
        throw new Error(response.error || 'Failed to load file tree');
      }

      // Update store with file tree
      this.repoStore.setFileTree(repoPath, this.convertTreeToNodes(response.data));

      return response.data;
    } catch (error) {
      throw new Error(`Failed to load file tree: ${error}`);
    }
  }

  async getFileContent(repoPath: string, filePath: string): Promise<FileInfo | null> {
    try {
      const response = await this.repoClient.getFileContent(repoPath, filePath);

      if (response.error || !response.data) {
        throw new Error(response.error || 'Failed to load file');
      }

      return response.data;
    } catch (error) {
      throw new Error(`Failed to get file content: ${error}`);
    }
  }

  async searchFiles(
    repoPath: string,
    query: string,
    fileType?: string
  ): Promise<SearchResult[]> {
    try {
      const response = await this.repoClient.searchFiles(repoPath, query, fileType);

      if (response.error) {
        throw new Error(response.error);
      }

      return response.data || [];
    } catch (error) {
      throw new Error(`Failed to search files: ${error}`);
    }
  }

  async listFiles(repoPath: string, dirPath?: string): Promise<FileInfo[]> {
    try {
      const response = await this.repoClient.listFiles(repoPath, dirPath);

      if (response.error) {
        throw new Error(response.error);
      }

      return response.data || [];
    } catch (error) {
      throw new Error(`Failed to list files: ${error}`);
    }
  }

  async getLanguages(repoPath: string): Promise<Record<string, number> | null> {
    try {
      const response = await this.repoClient.getLanguages(repoPath);

      if (response.error) {
        throw new Error(response.error);
      }

      return response.data || null;
    } catch (error) {
      throw new Error(`Failed to get languages: ${error}`);
    }
  }

  async analyzeRepository(repoPath: string): Promise<any> {
    try {
      const response = await this.repoClient.analyzeRepository(repoPath);

      if (response.error) {
        throw new Error(response.error);
      }

      return response.data || null;
    } catch (error) {
      throw new Error(`Failed to analyze repository: ${error}`);
    }
  }

  async findSymbol(repoPath: string, symbol: string): Promise<SearchResult[]> {
    try {
      const response = await this.repoClient.findSymbol(repoPath, symbol);

      if (response.error) {
        throw new Error(response.error);
      }

      return response.data || [];
    } catch (error) {
      throw new Error(`Failed to find symbol: ${error}`);
    }
  }

  async validateStructure(repoPath: string): Promise<{ valid: boolean; errors: string[] }> {
    try {
      const response = await this.repoClient.validateStructure(repoPath);

      if (response.error) {
        throw new Error(response.error);
      }

      return response.data || { valid: false, errors: [] };
    } catch (error) {
      throw new Error(`Failed to validate structure: ${error}`);
    }
  }

  async getCodeStats(repoPath: string): Promise<any> {
    try {
      const response = await this.repoClient.getCodeStats(repoPath);

      if (response.error) {
        throw new Error(response.error);
      }

      return response.data || null;
    } catch (error) {
      throw new Error(`Failed to get code stats: ${error}`);
    }
  }

  async writeFile(
    repoPath: string,
    filePath: string,
    content: string
  ): Promise<{ success: boolean; path: string } | null> {
    try {
      const response = await this.repoClient.writeFile(repoPath, filePath, content);

      if (response.error || !response.data) {
        throw new Error(response.error || 'Failed to write file');
      }

      return response.data;
    } catch (error) {
      throw new Error(`Failed to write file: ${error}`);
    }
  }

  async deleteFile(repoPath: string, filePath: string): Promise<boolean> {
    try {
      const response = await this.repoClient.deleteFile(repoPath, filePath);

      if (response.error || !response.data?.success) {
        throw new Error(response.error || 'Failed to delete file');
      }

      return true;
    } catch (error) {
      throw new Error(`Failed to delete file: ${error}`);
    }
  }

  private convertTreeToNodes(tree: DirectoryTree): any[] {
    const nodes: any[] = [];

    const traverse = (item: any, parentPath: string = ''): any => {
      const path = parentPath ? `${parentPath}/${item.name}` : item.name;
      return {
        id: path,
        name: item.name,
        path,
        type: item.type,
        size: item.size,
        children: item.children?.map((child: any) => traverse(child, path)) || [],
        isOpen: false,
      };
    };

    tree.children?.forEach((child: any) => {
      nodes.push(traverse(child));
    });

    return nodes;
  }

  setBaseUrl(url: string): void {
    this.repoClient.setBaseUrl(url);
  }

  setAuthToken(token: string): void {
    this.repoClient.setAuthHeader(token, 'Bearer');
  }
}
