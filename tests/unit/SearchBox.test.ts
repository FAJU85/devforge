import { describe, it, expect, beforeEach, vi } from 'vitest';

class SearchBox {
  private query: string = '';
  private results: string[] = [];
  private onSearch: ((query: string) => Promise<string[]>) | null = null;
  private onChange: ((query: string) => void) | null = null;
  private isSearching: boolean = false;

  setQuery(query: string): void {
    this.query = query;
    this.onChange?.(query);
  }

  getQuery(): string {
    return this.query;
  }

  async search(): Promise<string[]> {
    if (!this.query.trim()) {
      this.results = [];
      return [];
    }

    this.isSearching = true;
    try {
      if (this.onSearch) {
        this.results = await this.onSearch(this.query);
      }
      return this.results;
    } finally {
      this.isSearching = false;
    }
  }

  getResults(): string[] {
    return [...this.results];
  }

  clear(): void {
    this.query = '';
    this.results = [];
  }

  onSearchHandler(handler: (query: string) => Promise<string[]>): void {
    this.onSearch = handler;
  }

  onQueryChange(handler: (query: string) => void): void {
    this.onChange = handler;
  }

  isSearching_(): boolean {
    return this.isSearching;
  }

  getResultCount(): number {
    return this.results.length;
  }

  hasResults(): boolean {
    return this.results.length > 0;
  }

  isEmpty(): boolean {
    return this.query.length === 0;
  }
}

describe('SearchBox', () => {
  let searchBox: SearchBox;

  beforeEach(() => {
    searchBox = new SearchBox();
  });

  it('should initialize empty', () => {
    expect(searchBox.getQuery()).toBe('');
    expect(searchBox.isEmpty()).toBe(true);
  });

  it('should set query', () => {
    searchBox.setQuery('test');
    expect(searchBox.getQuery()).toBe('test');
  });

  it('should clear query', () => {
    searchBox.setQuery('test');
    searchBox.clear();
    expect(searchBox.getQuery()).toBe('');
  });

  it('should detect empty state', () => {
    searchBox.setQuery('test');
    expect(searchBox.isEmpty()).toBe(false);
    searchBox.clear();
    expect(searchBox.isEmpty()).toBe(true);
  });

  it('should call onChange callback', () => {
    const callback = vi.fn();
    searchBox.onQueryChange(callback);
    searchBox.setQuery('query');
    expect(callback).toHaveBeenCalledWith('query');
  });

  it('should perform search', async () => {
    const mockHandler = vi.fn().mockResolvedValue(['result1', 'result2']);
    searchBox.onSearchHandler(mockHandler);
    searchBox.setQuery('test');

    const results = await searchBox.search();

    expect(results).toEqual(['result1', 'result2']);
    expect(mockHandler).toHaveBeenCalledWith('test');
  });

  it('should return empty results for empty query', async () => {
    const mockHandler = vi.fn().mockResolvedValue(['result1']);
    searchBox.onSearchHandler(mockHandler);
    searchBox.setQuery('');

    const results = await searchBox.search();

    expect(results).toEqual([]);
    expect(mockHandler).not.toHaveBeenCalled();
  });

  it('should get result count', async () => {
    const mockHandler = vi.fn().mockResolvedValue(['a', 'b', 'c']);
    searchBox.onSearchHandler(mockHandler);
    searchBox.setQuery('test');

    await searchBox.search();

    expect(searchBox.getResultCount()).toBe(3);
  });

  it('should detect if has results', async () => {
    const mockHandler = vi.fn().mockResolvedValue(['result']);
    searchBox.onSearchHandler(mockHandler);
    searchBox.setQuery('test');

    expect(searchBox.hasResults()).toBe(false);
    await searchBox.search();
    expect(searchBox.hasResults()).toBe(true);
  });

  it('should set searching state during search', async () => {
    const mockHandler = vi.fn(async (q: string) => {
      expect(searchBox.isSearching_()).toBe(true);
      return ['result'];
    });

    searchBox.onSearchHandler(mockHandler);
    searchBox.setQuery('test');

    expect(searchBox.isSearching_()).toBe(false);
    await searchBox.search();
    expect(searchBox.isSearching_()).toBe(false);
  });

  it('should clear results with query', () => {
    searchBox.clear();
    expect(searchBox.getResults()).toEqual([]);
  });

  it('should handle multiple searches', async () => {
    let callCount = 0;
    const mockHandler = vi.fn(async (q: string) => {
      callCount++;
      return [`result-${callCount}`];
    });

    searchBox.onSearchHandler(mockHandler);

    searchBox.setQuery('first');
    await searchBox.search();
    expect(searchBox.getResults()).toEqual(['result-1']);

    searchBox.setQuery('second');
    await searchBox.search();
    expect(searchBox.getResults()).toEqual(['result-2']);
  });

  it('should handle search errors gracefully', async () => {
    const mockHandler = vi.fn().mockRejectedValue(new Error('Search failed'));
    searchBox.onSearchHandler(mockHandler);
    searchBox.setQuery('test');

    try {
      await searchBox.search();
    } catch (e) {
      expect(searchBox.isSearching_()).toBe(false);
    }
  });

  it('should preserve whitespace in query', () => {
    searchBox.setQuery('  test query  ');
    expect(searchBox.getQuery()).toBe('  test query  ');
  });

  it('should handle case sensitivity', async () => {
    const mockHandler = vi.fn(async (q: string) => {
      return [q]; // Echo the query
    });

    searchBox.onSearchHandler(mockHandler);
    searchBox.setQuery('TestQuery');

    await searchBox.search();
    expect(searchBox.getResults()[0]).toBe('TestQuery');
  });
});
