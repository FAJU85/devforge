import { describe, it, expect, beforeEach, vi } from 'vitest';

interface GithubRepo {
  id: number;
  name: string;
  owner: string;
  url: string;
}

class GithubApiClient {
  private token: string = '';
  private baseUrl: string = 'https://api.github.com';

  setToken(token: string): void {
    this.token = token;
  }

  isAuthenticated(): boolean {
    return this.token.length > 0;
  }

  async getUser(): Promise<{ login: string } | null> {
    if (!this.isAuthenticated()) return null;
    return { login: 'test-user' };
  }

  async getRepositories(owner: string): Promise<GithubRepo[]> {
    if (!this.isAuthenticated()) return [];
    return [
      { id: 1, name: 'repo1', owner, url: `${this.baseUrl}/${owner}/repo1` },
      { id: 2, name: 'repo2', owner, url: `${this.baseUrl}/${owner}/repo2` }
    ];
  }

  async searchRepositories(query: string): Promise<GithubRepo[]> {
    if (!this.isAuthenticated()) return [];
    return [];
  }

  getAuthorizationUrl(): string {
    return `https://github.com/login/oauth/authorize?client_id=test`;
  }

  revokeToken(): void {
    this.token = '';
  }
}

describe('GithubApiClient', () => {
  let client: GithubApiClient;

  beforeEach(() => {
    client = new GithubApiClient();
  });

  it('should initialize unauthenticated', () => {
    expect(client.isAuthenticated()).toBe(false);
  });

  it('should set token', () => {
    client.setToken('test-token');
    expect(client.isAuthenticated()).toBe(true);
  });

  it('should get user when authenticated', async () => {
    client.setToken('token');
    const user = await client.getUser();
    expect(user?.login).toBe('test-user');
  });

  it('should return null when not authenticated', async () => {
    const user = await client.getUser();
    expect(user).toBeNull();
  });

  it('should get repositories', async () => {
    client.setToken('token');
    const repos = await client.getRepositories('owner');
    expect(repos).toHaveLength(2);
  });

  it('should return empty when unauthenticated', async () => {
    const repos = await client.getRepositories('owner');
    expect(repos).toEqual([]);
  });

  it('should get authorization URL', () => {
    const url = client.getAuthorizationUrl();
    expect(url).toContain('github.com');
    expect(url).toContain('oauth');
  });

  it('should revoke token', () => {
    client.setToken('token');
    client.revokeToken();
    expect(client.isAuthenticated()).toBe(false);
  });
});
