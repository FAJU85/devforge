/**
 * Request Cache - optimizes API calls with intelligent caching
 */

export interface CacheEntry<T> {
  data: T;
  timestamp: number;
  ttl: number; // Time to live in milliseconds
  hits: number;
}

export interface CacheConfig {
  defaultTTL?: number; // Default 5 minutes
  maxSize?: number; // Max cache entries, default 100
  enableStats?: boolean;
}

export class RequestCache {
  private cache = new Map<string, CacheEntry<any>>();
  private config: Required<CacheConfig>;
  private stats = {
    hits: 0,
    misses: 0,
    evictions: 0,
  };

  constructor(config: CacheConfig = {}) {
    this.config = {
      defaultTTL: config.defaultTTL ?? 5 * 60 * 1000, // 5 minutes
      maxSize: config.maxSize ?? 100,
      enableStats: config.enableStats ?? false,
    };
  }

  /**
   * Get cached value if valid, otherwise return null
   */
  get<T>(key: string): T | null {
    const entry = this.cache.get(key);

    if (!entry) {
      this.recordMiss();
      return null;
    }

    // Check if entry has expired
    if (Date.now() - entry.timestamp > entry.ttl) {
      this.cache.delete(key);
      this.recordMiss();
      return null;
    }

    // Update hit count
    entry.hits++;
    this.recordHit();

    return entry.data as T;
  }

  /**
   * Set cache value
   */
  set<T>(key: string, data: T, ttl?: number): void {
    // Enforce max size
    if (this.cache.size >= this.config.maxSize && !this.cache.has(key)) {
      this.evictLRU();
    }

    this.cache.set(key, {
      data,
      timestamp: Date.now(),
      ttl: ttl ?? this.config.defaultTTL,
      hits: 0,
    });
  }

  /**
   * Check if key exists and is valid
   */
  has(key: string): boolean {
    const entry = this.cache.get(key);

    if (!entry) {
      return false;
    }

    if (Date.now() - entry.timestamp > entry.ttl) {
      this.cache.delete(key);
      return false;
    }

    return true;
  }

  /**
   * Delete specific cache entry
   */
  delete(key: string): boolean {
    return this.cache.delete(key);
  }

  /**
   * Clear all cache
   */
  clear(): void {
    this.cache.clear();
  }

  /**
   * Get cache statistics
   */
  getStats() {
    const total = this.stats.hits + this.stats.misses;
    const hitRate = total > 0 ? (this.stats.hits / total) * 100 : 0;

    return {
      hits: this.stats.hits,
      misses: this.stats.misses,
      hitRate: hitRate.toFixed(2) + '%',
      evictions: this.stats.evictions,
      size: this.cache.size,
      capacity: this.config.maxSize,
    };
  }

  /**
   * Reset statistics
   */
  resetStats(): void {
    this.stats = { hits: 0, misses: 0, evictions: 0 };
  }

  /**
   * Evict least recently used entry
   */
  private evictLRU(): void {
    let lruKey: string | null = null;
    let minHits = Infinity;
    let oldestTime = Infinity;

    for (const [key, entry] of this.cache.entries()) {
      // Prefer evicting entries with fewer hits, then oldest timestamp
      if (entry.hits < minHits || (entry.hits === minHits && entry.timestamp < oldestTime)) {
        lruKey = key;
        minHits = entry.hits;
        oldestTime = entry.timestamp;
      }
    }

    if (lruKey) {
      this.cache.delete(lruKey);
      this.stats.evictions++;
    }
  }

  private recordHit(): void {
    if (this.config.enableStats) {
      this.stats.hits++;
    }
  }

  private recordMiss(): void {
    if (this.config.enableStats) {
      this.stats.misses++;
    }
  }

  /**
   * Get all cache keys
   */
  keys(): string[] {
    return Array.from(this.cache.keys());
  }

  /**
   * Get cache size in entries
   */
  size(): number {
    return this.cache.size;
  }

  /**
   * Invalidate cache entries by pattern
   */
  invalidatePattern(pattern: RegExp | string): number {
    const regex = typeof pattern === 'string' ? new RegExp(pattern) : pattern;
    let count = 0;

    for (const key of this.cache.keys()) {
      if (regex.test(key)) {
        this.cache.delete(key);
        count++;
      }
    }

    return count;
  }
}

/**
 * Create cache key from endpoint and options
 */
export function createCacheKey(endpoint: string, options?: Record<string, any>): string {
  if (!options || Object.keys(options).length === 0) {
    return endpoint;
  }

  const sorted = Object.keys(options)
    .sort()
    .map((key) => `${key}=${JSON.stringify(options[key])}`)
    .join('&');

  return `${endpoint}?${sorted}`;
}
