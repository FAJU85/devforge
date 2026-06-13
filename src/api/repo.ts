/**
 * Repository API Client - local and remote repository operations
 */

import { ApiClient, ApiResponse, ApiConfig } from './client';

export interface FileInfo {
  path: string;
  name: string;
  type: 'file' | 'directory';
  size: number;
  language?: string;
  content?: string;
  encoding?: string;
}

export interface DirectoryTree {
  path: string;
  name: string;
  type: 'directory';
  children: Array<FileInfo | DirectoryTree>;
  size: number;
}

export interface SearchResult {
  path: string;
  type: 'file' | 'directory';
  matches: number;
  preview?: string;
}

export interface RepositoryInfo {
  path: string;
  name: string;
  isGit: boolean;
  currentBranch?: string;
  remoteUrl?: string;
  isDirty?: boolean;
}

export interface DiffResult {
  file: string;
  status: 'added' | 'modified' | 'deleted' | 'renamed';
  additions: number;
  deletions: number;
  diff?: string;
}

export class RepositoryClient extends ApiClient {
  constructor(baseUrl: string = 'http://localhost:3000/api') {
    const config: ApiConfig = {
      baseUrl,
      timeout: 30000,
      headers: {
        'Content-Type': 'application/json',
      },
    };

    super(config);
  }

  async getRepositoryInfo(repoPath: string): Promise<ApiResponse<RepositoryInfo>> {
    return this.get<RepositoryInfo>(`/repository/info?path=${encodeURIComponent(repoPath)}`);
  }

  async getFileContent(repoPath: string, filePath: string): Promise<ApiResponse<FileInfo>> {
    return this.get<FileInfo>(
      `/repository/file?repo=${encodeURIComponent(repoPath)}&path=${encodeURIComponent(filePath)}`
    );
  }

  async getDirectoryTree(repoPath: string, depth: number = 3): Promise<ApiResponse<DirectoryTree>> {
    return this.get<DirectoryTree>(
      `/repository/tree?path=${encodeURIComponent(repoPath)}&depth=${depth}`
    );
  }

  async searchFiles(
    repoPath: string,
    query: string,
    fileType?: string
  ): Promise<ApiResponse<SearchResult[]>> {
    let url = `/repository/search?repo=${encodeURIComponent(repoPath)}&query=${encodeURIComponent(query)}`;
    if (fileType) {
      url += `&type=${encodeURIComponent(fileType)}`;
    }
    return this.get<SearchResult[]>(url);
  }

  async listFiles(repoPath: string, dirPath?: string): Promise<ApiResponse<FileInfo[]>> {
    let url = `/repository/files?repo=${encodeURIComponent(repoPath)}`;
    if (dirPath) {
      url += `&dir=${encodeURIComponent(dirPath)}`;
    }
    return this.get<FileInfo[]>(url);
  }

  async getDiff(
    repoPath: string,
    fromRef: string,
    toRef: string
  ): Promise<ApiResponse<DiffResult[]>> {
    return this.get<DiffResult[]>(
      `/repository/diff?repo=${encodeURIComponent(repoPath)}&from=${fromRef}&to=${toRef}`
    );
  }

  async getFileDiff(repoPath: string, filePath: string): Promise<ApiResponse<DiffResult>> {
    return this.get<DiffResult>(
      `/repository/file-diff?repo=${encodeURIComponent(repoPath)}&path=${encodeURIComponent(filePath)}`
    );
  }

  async getCurrentBranch(repoPath: string): Promise<ApiResponse<{ branch: string }>> {
    return this.get<{ branch: string }>(
      `/repository/branch?path=${encodeURIComponent(repoPath)}`
    );
  }

  async listBranches(repoPath: string): Promise<ApiResponse<string[]>> {
    return this.get<string[]>(`/repository/branches?path=${encodeURIComponent(repoPath)}`);
  }

  async getLanguages(repoPath: string): Promise<ApiResponse<Record<string, number>>> {
    return this.get<Record<string, number>>(
      `/repository/languages?path=${encodeURIComponent(repoPath)}`
    );
  }

  async analyzeRepository(repoPath: string): Promise<ApiResponse<any>> {
    return this.get<any>(`/repository/analyze?path=${encodeURIComponent(repoPath)}`);
  }

  async findSymbol(repoPath: string, symbol: string): Promise<ApiResponse<SearchResult[]>> {
    return this.get<SearchResult[]>(
      `/repository/symbol?repo=${encodeURIComponent(repoPath)}&name=${encodeURIComponent(symbol)}`
    );
  }

  async validateStructure(repoPath: string): Promise<ApiResponse<{ valid: boolean; errors: string[] }>> {
    return this.get<{ valid: boolean; errors: string[] }>(
      `/repository/validate?path=${encodeURIComponent(repoPath)}`
    );
  }

  async getCodeStats(
    repoPath: string
  ): Promise<ApiResponse<{
    totalFiles: number;
    totalLines: number;
    languages: Record<string, number>;
  }>> {
    return this.get<{
      totalFiles: number;
      totalLines: number;
      languages: Record<string, number>;
    }>(`/repository/stats?path=${encodeURIComponent(repoPath)}`);
  }

  async writeFile(
    repoPath: string,
    filePath: string,
    content: string
  ): Promise<ApiResponse<{ success: boolean; path: string }>> {
    return this.post<{ success: boolean; path: string }>(
      `/repository/file?repo=${encodeURIComponent(repoPath)}`,
      {
        path: filePath,
        content,
      }
    );
  }

  async deleteFile(repoPath: string, filePath: string): Promise<ApiResponse<{ success: boolean }>> {
    return this.post<{ success: boolean }>(
      `/repository/file-delete?repo=${encodeURIComponent(repoPath)}`,
      {
        path: filePath,
      }
    );
  }
}
