import { describe, it, expect, beforeEach, vi } from 'vitest';

class RequestCache {
  private cache: Map<string, { data: unknown; timestamp: number }> = new Map();
  private ttl: number = 60000; // 1 minute default

  constructor(ttl: number = 60000) {
    this.ttl = ttl;
  }

  set(key: string, data: unknown): void {
    this.cache.set(key, {
      data,
      timestamp: Date.now()
    });
  }

  get(key: string): unknown | null {
    const entry = this.cache.get(key);
    if (!entry) return null;

    const isExpired = Date.now() - entry.timestamp > this.ttl;
    if (isExpired) {
      this.cache.delete(key);
      return null;
    }

    return entry.data;
  }

  has(key: string): boolean {
    return this.get(key) !== null;
  }

  delete(key: string): boolean {
    return this.cache.delete(key);
  }

  clear(): void {
    this.cache.clear();
  }

  size(): number {
    return this.cache.size;
  }

  keys(): string[] {
    return Array.from(this.cache.keys());
  }

  values(): unknown[] {
    return Array.from(this.cache.values()).map(v => v.data);
  }

  prune(): number {
    let pruned = 0;
    const now = Date.now();
    for (const [key, entry] of this.cache) {
      if (now - entry.timestamp > this.ttl) {
        this.cache.delete(key);
        pruned++;
      }
    }
    return pruned;
  }

  getStats(): { size: number; entries: number } {
    return {
      size: this.cache.size,
      entries: this.cache.size
    };
  }
}

describe('RequestCache', () => {
  let cache: RequestCache;

  beforeEach(() => {
    cache = new RequestCache(1000); // 1 second TTL for testing
  });

  it('should initialize empty', () => {
    expect(cache.size()).toBe(0);
  });

  it('should set and get value', () => {
    cache.set('key1', 'value1');
    expect(cache.get('key1')).toBe('value1');
  });

  it('should return null for missing key', () => {
    expect(cache.get('missing')).toBeNull();
  });

  it('should check if key exists', () => {
    cache.set('key1', 'value1');
    expect(cache.has('key1')).toBe(true);
    expect(cache.has('missing')).toBe(false);
  });

  it('should delete key', () => {
    cache.set('key1', 'value1');
    expect(cache.delete('key1')).toBe(true);
    expect(cache.has('key1')).toBe(false);
  });

  it('should return false when deleting missing key', () => {
    expect(cache.delete('missing')).toBe(false);
  });

  it('should clear all entries', () => {
    cache.set('key1', 'value1');
    cache.set('key2', 'value2');
    cache.clear();
    expect(cache.size()).toBe(0);
  });

  it('should get cache size', () => {
    cache.set('key1', 'value1');
    cache.set('key2', 'value2');
    expect(cache.size()).toBe(2);
  });

  it('should get all keys', () => {
    cache.set('key1', 'value1');
    cache.set('key2', 'value2');
    const keys = cache.keys();
    expect(keys).toContain('key1');
    expect(keys).toContain('key2');
  });

  it('should get all values', () => {
    cache.set('key1', 'value1');
    cache.set('key2', 'value2');
    const values = cache.values();
    expect(values).toContain('value1');
    expect(values).toContain('value2');
  });

  it('should cache objects', () => {
    const obj = { name: 'test', id: 123 };
    cache.set('obj', obj);
    expect(cache.get('obj')).toEqual(obj);
  });

  it('should cache arrays', () => {
    const arr = [1, 2, 3];
    cache.set('arr', arr);
    expect(cache.get('arr')).toEqual(arr);
  });

  it('should expire entries after TTL', () => {
    cache.set('key1', 'value1');
    expect(cache.has('key1')).toBe(true);

    vi.useFakeTimers();
    vi.advanceTimersByTime(1100);

    expect(cache.has('key1')).toBe(false);
    vi.useRealTimers();
  });

  it('should prune expired entries', () => {
    cache.set('key1', 'value1');
    cache.set('key2', 'value2');

    vi.useFakeTimers();
    vi.advanceTimersByTime(1100);

    const pruned = cache.prune();
    expect(pruned).toBe(2);
    expect(cache.size()).toBe(0);
    vi.useRealTimers();
  });

  it('should get cache stats', () => {
    cache.set('key1', 'value1');
    cache.set('key2', 'value2');
    const stats = cache.getStats();
    expect(stats.size).toBe(2);
    expect(stats.entries).toBe(2);
  });

  it('should handle multiple set operations', () => {
    cache.set('key1', 'value1');
    cache.set('key1', 'updated');
    expect(cache.get('key1')).toBe('updated');
    expect(cache.size()).toBe(1);
  });

  it('should support custom TTL', () => {
    const shortCache = new RequestCache(100);
    shortCache.set('key1', 'value1');

    vi.useFakeTimers();
    vi.advanceTimersByTime(150);

    expect(shortCache.get('key1')).toBeNull();
    vi.useRealTimers();
  });
});
