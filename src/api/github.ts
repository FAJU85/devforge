/**
 * GitHub API Client - interactions with GitHub repositories and API
 */

import { ApiClient, ApiResponse, ApiConfig } from './client';

export interface GitHubUser {
  login: string;
  id: number;
  avatar_url: string;
  type: string;
  name?: string;
  bio?: string;
  public_repos: number;
}

export interface GitHubRepository {
  id: number;
  name: string;
  full_name: string;
  private: boolean;
  description?: string;
  url: string;
  clone_url: string;
  language?: string;
  stargazers_count: number;
  forks_count: number;
}

export interface GitHubCommit {
  sha: string;
  commit: {
    message: string;
    author: {
      name: string;
      email: string;
      date: string;
    };
  };
  author?: {
    login: string;
    avatar_url: string;
  };
  html_url: string;
}

export interface GitHubPullRequest {
  id: number;
  number: number;
  title: string;
  state: 'open' | 'closed';
  user: {
    login: string;
    avatar_url: string;
  };
  created_at: string;
  updated_at: string;
  html_url: string;
  draft: boolean;
}

export interface GitHubIssue {
  id: number;
  number: number;
  title: string;
  state: 'open' | 'closed';
  user: {
    login: string;
    avatar_url: string;
  };
  created_at: string;
  updated_at: string;
  html_url: string;
  labels: Array<{ name: string; color: string }>;
}

export class GitHubClient extends ApiClient {
  constructor(token?: string) {
    const config: ApiConfig = {
      baseUrl: 'https://api.github.com',
      timeout: 30000,
      headers: {
        'Accept': 'application/vnd.github.v3+json',
        'User-Agent': 'DevForge',
      },
    };

    if (token) {
      config.headers!['Authorization'] = `Bearer ${token}`;
    }

    super(config);
  }

  setRepository(_owner: string, _repo: string): void {
    // Repository context is passed in method calls directly
  }

  async getUser(username: string): Promise<ApiResponse<GitHubUser>> {
    return this.get<GitHubUser>(`/users/${username}`);
  }

  async getAuthenticatedUser(): Promise<ApiResponse<GitHubUser>> {
    return this.get<GitHubUser>('/user');
  }

  async getRepository(owner: string, repo: string): Promise<ApiResponse<GitHubRepository>> {
    return this.get<GitHubRepository>(`/repos/${owner}/${repo}`);
  }

  async listUserRepositories(username: string, page: number = 1): Promise<ApiResponse<GitHubRepository[]>> {
    return this.get<GitHubRepository[]>(`/users/${username}/repos?page=${page}&per_page=30`);
  }

  async getRepositoryCommits(
    owner: string,
    repo: string,
    page: number = 1
  ): Promise<ApiResponse<GitHubCommit[]>> {
    return this.get<GitHubCommit[]>(`/repos/${owner}/${repo}/commits?page=${page}&per_page=30`);
  }

  async getCommit(owner: string, repo: string, sha: string): Promise<ApiResponse<GitHubCommit>> {
    return this.get<GitHubCommit>(`/repos/${owner}/${repo}/commits/${sha}`);
  }

  async listPullRequests(
    owner: string,
    repo: string,
    state: 'open' | 'closed' | 'all' = 'open'
  ): Promise<ApiResponse<GitHubPullRequest[]>> {
    return this.get<GitHubPullRequest[]>(
      `/repos/${owner}/${repo}/pulls?state=${state}&per_page=30`
    );
  }

  async getPullRequest(
    owner: string,
    repo: string,
    number: number
  ): Promise<ApiResponse<GitHubPullRequest>> {
    return this.get<GitHubPullRequest>(`/repos/${owner}/${repo}/pulls/${number}`);
  }

  async listIssues(
    owner: string,
    repo: string,
    state: 'open' | 'closed' | 'all' = 'open'
  ): Promise<ApiResponse<GitHubIssue[]>> {
    return this.get<GitHubIssue[]>(`/repos/${owner}/${repo}/issues?state=${state}&per_page=30`);
  }

  async getIssue(owner: string, repo: string, number: number): Promise<ApiResponse<GitHubIssue>> {
    return this.get<GitHubIssue>(`/repos/${owner}/${repo}/issues/${number}`);
  }

  async createIssue(
    owner: string,
    repo: string,
    title: string,
    body?: string,
    labels?: string[]
  ): Promise<ApiResponse<GitHubIssue>> {
    return this.post<GitHubIssue>(`/repos/${owner}/${repo}/issues`, {
      title,
      body,
      labels,
    });
  }

  async updateIssue(
    owner: string,
    repo: string,
    number: number,
    updates: { title?: string; state?: string; body?: string }
  ): Promise<ApiResponse<GitHubIssue>> {
    return this.patch<GitHubIssue>(`/repos/${owner}/${repo}/issues/${number}`, updates);
  }

  async getFileContents(
    owner: string,
    repo: string,
    path: string
  ): Promise<ApiResponse<any>> {
    return this.get<any>(`/repos/${owner}/${repo}/contents/${path}`);
  }

  async searchRepositories(query: string, page: number = 1): Promise<ApiResponse<any>> {
    const encoded = encodeURIComponent(query);
    return this.get<any>(`/search/repositories?q=${encoded}&page=${page}&per_page=30`);
  }

  async searchCode(query: string, owner: string, repo: string): Promise<ApiResponse<any>> {
    const encoded = encodeURIComponent(`${query} repo:${owner}/${repo}`);
    return this.get<any>(`/search/code?q=${encoded}&per_page=30`);
  }
}
