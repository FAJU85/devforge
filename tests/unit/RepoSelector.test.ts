import { describe, it, expect, beforeEach, vi } from 'vitest';

interface Repo {
  id: string;
  name: string;
  owner: string;
  url: string;
  isPrivate: boolean;
  language?: string;
}

class RepoSelector {
  private repos: Repo[] = [];
  private selectedRepo: Repo | null = null;
  private onSelect: ((repo: Repo) => void) | null = null;
  private onLoad: ((repos: Repo[]) => void) | null = null;

  async loadRepositories(): Promise<Repo[]> {
    // Simulated load
    this.onLoad?.(this.repos);
    return this.repos;
  }

  setRepositories(repos: Repo[]): void {
    this.repos = repos;
  }

  selectRepository(repoId: string): boolean {
    const repo = this.repos.find(r => r.id === repoId);
    if (repo) {
      this.selectedRepo = repo;
      this.onSelect?.(repo);
      return true;
    }
    return false;
  }

  getSelectedRepository(): Repo | null {
    return this.selectedRepo;
  }

  getRepositories(): Repo[] {
    return [...this.repos];
  }

  searchRepositories(query: string): Repo[] {
    const lowerQuery = query.toLowerCase();
    return this.repos.filter(r =>
      r.name.toLowerCase().includes(lowerQuery) ||
      r.owner.toLowerCase().includes(lowerQuery)
    );
  }

  filterByLanguage(language: string): Repo[] {
    return this.repos.filter(r => r.language === language);
  }

  filterByVisibility(isPrivate: boolean): Repo[] {
    return this.repos.filter(r => r.isPrivate === isPrivate);
  }

  getRepositoryCount(): number {
    return this.repos.length;
  }

  getPublicRepositories(): Repo[] {
    return this.filterByVisibility(false);
  }

  getPrivateRepositories(): Repo[] {
    return this.filterByVisibility(true);
  }

  onRepositorySelect(callback: (repo: Repo) => void): void {
    this.onSelect = callback;
  }

  onRepositoriesLoad(callback: (repos: Repo[]) => void): void {
    this.onLoad = callback;
  }

  addRepository(repo: Repo): void {
    if (!this.repos.find(r => r.id === repo.id)) {
      this.repos.push(repo);
    }
  }

  removeRepository(repoId: string): boolean {
    const index = this.repos.findIndex(r => r.id === repoId);
    if (index > -1) {
      this.repos.splice(index, 1);
      if (this.selectedRepo?.id === repoId) {
        this.selectedRepo = null;
      }
      return true;
    }
    return false;
  }

  clear(): void {
    this.repos = [];
    this.selectedRepo = null;
  }
}

describe('RepoSelector', () => {
  let selector: RepoSelector;
  const mockRepos: Repo[] = [
    {
      id: '1',
      name: 'devforge',
      owner: 'faju85',
      url: 'https://github.com/faju85/devforge',
      isPrivate: false,
      language: 'TypeScript'
    },
    {
      id: '2',
      name: 'private-repo',
      owner: 'faju85',
      url: 'https://github.com/faju85/private-repo',
      isPrivate: true,
      language: 'Python'
    },
    {
      id: '3',
      name: 'web-app',
      owner: 'team',
      url: 'https://github.com/team/web-app',
      isPrivate: false,
      language: 'JavaScript'
    }
  ];

  beforeEach(() => {
    selector = new RepoSelector();
    selector.setRepositories(mockRepos);
  });

  it('should initialize empty', () => {
    const newSelector = new RepoSelector();
    expect(newSelector.getRepositoryCount()).toBe(0);
  });

  it('should set repositories', () => {
    expect(selector.getRepositoryCount()).toBe(3);
  });

  it('should get repositories', () => {
    const repos = selector.getRepositories();
    expect(repos).toHaveLength(3);
  });

  it('should select repository', () => {
    const selected = selector.selectRepository('1');
    expect(selected).toBe(true);
    expect(selector.getSelectedRepository()?.name).toBe('devforge');
  });

  it('should return false when selecting nonexistent repo', () => {
    const selected = selector.selectRepository('nonexistent');
    expect(selected).toBe(false);
  });

  it('should call onSelect callback', () => {
    const callback = vi.fn();
    selector.onRepositorySelect(callback);
    selector.selectRepository('1');
    expect(callback).toHaveBeenCalledWith(mockRepos[0]);
  });

  it('should search repositories', () => {
    const results = selector.searchRepositories('devforge');
    expect(results).toHaveLength(1);
    expect(results[0].name).toBe('devforge');
  });

  it('should search case-insensitive', () => {
    const results = selector.searchRepositories('DEVFORGE');
    expect(results).toHaveLength(1);
  });

  it('should search by owner', () => {
    const results = selector.searchRepositories('faju85');
    expect(results).toHaveLength(2);
  });

  it('should filter by language', () => {
    const tsRepos = selector.filterByLanguage('TypeScript');
    expect(tsRepos).toHaveLength(1);
    expect(tsRepos[0].name).toBe('devforge');
  });

  it('should filter by visibility', () => {
    const publicRepos = selector.filterByVisibility(false);
    expect(publicRepos).toHaveLength(2);
  });

  it('should get public repositories', () => {
    const publicRepos = selector.getPublicRepositories();
    expect(publicRepos).toHaveLength(2);
    expect(publicRepos.every(r => !r.isPrivate)).toBe(true);
  });

  it('should get private repositories', () => {
    const privateRepos = selector.getPrivateRepositories();
    expect(privateRepos).toHaveLength(1);
    expect(privateRepos[0].isPrivate).toBe(true);
  });

  it('should add repository', () => {
    const newRepo: Repo = {
      id: '4',
      name: 'new-repo',
      owner: 'user',
      url: 'https://github.com/user/new-repo',
      isPrivate: false
    };
    selector.addRepository(newRepo);
    expect(selector.getRepositoryCount()).toBe(4);
  });

  it('should not add duplicate repositories', () => {
    selector.addRepository(mockRepos[0]);
    expect(selector.getRepositoryCount()).toBe(3);
  });

  it('should remove repository', () => {
    const removed = selector.removeRepository('1');
    expect(removed).toBe(true);
    expect(selector.getRepositoryCount()).toBe(2);
  });

  it('should clear selected when removing', () => {
    selector.selectRepository('1');
    selector.removeRepository('1');
    expect(selector.getSelectedRepository()).toBeNull();
  });

  it('should return false when removing nonexistent repo', () => {
    const removed = selector.removeRepository('nonexistent');
    expect(removed).toBe(false);
  });

  it('should clear all repositories', () => {
    selector.clear();
    expect(selector.getRepositoryCount()).toBe(0);
    expect(selector.getSelectedRepository()).toBeNull();
  });

  it('should call onLoad callback', async () => {
    const callback = vi.fn();
    selector.onRepositoriesLoad(callback);
    await selector.loadRepositories();
    expect(callback).toHaveBeenCalledWith(mockRepos);
  });

  it('should handle empty search results', () => {
    const results = selector.searchRepositories('nonexistent');
    expect(results).toHaveLength(0);
  });
});
