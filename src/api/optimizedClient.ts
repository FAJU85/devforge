/**
 * Optimized API Client - extends base client with caching and deduplication
 */

import { ApiClient, ApiResponse, ApiConfig } from './client';
import { RequestCache, createCacheKey } from '../utils/requestCache';
import { RequestDeduplicator } from '../utils/requestDeduplicator';
import { RequestBatcher } from '../utils/requestBatcher';

export interface OptimizedClientConfig extends ApiConfig {
  cacheEnabled?: boolean;
  dedupeEnabled?: boolean;
  batchEnabled?: boolean;
  cacheTTL?: number;
  cacheMaxSize?: number;
}

export class OptimizedApiClient extends ApiClient {
  private cache: RequestCache;
  private deduplicator: RequestDeduplicator;
  private batcher: RequestBatcher;
  private cacheEnabled: boolean;
  private dedupeEnabled: boolean;
  private batchEnabled: boolean;

  constructor(config: OptimizedClientConfig) {
    super(config);

    this.cacheEnabled = config.cacheEnabled ?? true;
    this.dedupeEnabled = config.dedupeEnabled ?? true;
    this.batchEnabled = config.batchEnabled ?? false;

    this.cache = new RequestCache({
      defaultTTL: config.cacheTTL ?? 5 * 60 * 1000,
      maxSize: config.cacheMaxSize ?? 100,
      enableStats: true,
    });

    this.deduplicator = new RequestDeduplicator();
    this.batcher = new RequestBatcher({ enabled: this.batchEnabled });
  }

  /**
   * GET with caching and deduplication
   */
  async get<T>(endpoint: string, options?: RequestInit): Promise<ApiResponse<T>> {
    const cacheKey = createCacheKey(endpoint, options);

    // Check cache
    if (this.cacheEnabled) {
      const cached = this.cache.get<ApiResponse<T>>(cacheKey);
      if (cached) {
        return cached;
      }
    }

    // Dedupe concurrent requests
    const fn = async () => {
      const response = await super.get<T>(endpoint, options);

      // Cache successful responses
      if (this.cacheEnabled && !response.error) {
        this.cache.set(cacheKey, response);
      }

      return response;
    };

    if (this.dedupeEnabled) {
      return this.deduplicator.dedupe(cacheKey, fn);
    }

    return fn();
  }

  /**
   * POST with deduplication (no caching by default)
   */
  async post<T>(
    endpoint: string,
    data?: any,
    options?: RequestInit
  ): Promise<ApiResponse<T>> {
    const cacheKey = createCacheKey(endpoint, { data, ...options });

    const fn = async () => super.post<T>(endpoint, data, options);

    if (this.dedupeEnabled) {
      return this.deduplicator.dedupe(cacheKey, fn);
    }

    return fn();
  }

  /**
   * PUT with deduplication
   */
  async put<T>(
    endpoint: string,
    data?: any,
    options?: RequestInit
  ): Promise<ApiResponse<T>> {
    const cacheKey = createCacheKey(endpoint, { data, ...options });

    const fn = async () => super.put<T>(endpoint, data, options);

    if (this.dedupeEnabled) {
      return this.deduplicator.dedupe(cacheKey, fn);
    }

    return fn();
  }

  /**
   * PATCH with deduplication
   */
  async patch<T>(
    endpoint: string,
    data?: any,
    options?: RequestInit
  ): Promise<ApiResponse<T>> {
    const cacheKey = createCacheKey(endpoint, { data, ...options });

    const fn = async () => super.patch<T>(endpoint, data, options);

    if (this.dedupeEnabled) {
      return this.deduplicator.dedupe(cacheKey, fn);
    }

    return fn();
  }

  /**
   * DELETE with deduplication
   */
  async delete<T>(endpoint: string, options?: RequestInit): Promise<ApiResponse<T>> {
    const cacheKey = createCacheKey(endpoint, options);

    const fn = async () => super.delete<T>(endpoint, options);

    if (this.dedupeEnabled) {
      return this.deduplicator.dedupe(cacheKey, fn);
    }

    return fn();
  }

  /**
   * Clear request cache
   */
  clearCache(): void {
    this.cache.clear();
  }

  /**
   * Invalidate cache entries matching pattern
   */
  invalidateCache(pattern: RegExp | string): number {
    return this.cache.invalidatePattern(pattern);
  }

  /**
   * Get cache statistics
   */
  getCacheStats() {
    return this.cache.getStats();
  }

  /**
   * Get deduplication statistics
   */
  getDedupeStats() {
    return this.deduplicator.getStats();
  }

  /**
   * Get batching statistics
   */
  getBatchStats() {
    return this.batcher.getStats();
  }

  /**
   * Get combined statistics
   */
  getStats() {
    return {
      cache: this.getCacheStats(),
      dedupe: this.getDedupeStats(),
      batch: this.getBatchStats(),
    };
  }

  /**
   * Flush all pending batched requests
   */
  async flushBatch(): Promise<void> {
    await this.batcher.flush();
  }

  /**
   * Enable/disable optimization features
   */
  setOptimizations(options: {
    cache?: boolean;
    dedupe?: boolean;
    batch?: boolean;
  }): void {
    if (options.cache !== undefined) {
      this.cacheEnabled = options.cache;
    }
    if (options.dedupe !== undefined) {
      this.dedupeEnabled = options.dedupe;
    }
    if (options.batch !== undefined) {
      this.batchEnabled = options.batch;
      this.batcher.setEnabled(options.batch);
    }
  }

  /**
   * Get optimization status
   */
  getOptimizationStatus() {
    return {
      cacheEnabled: this.cacheEnabled,
      dedupeEnabled: this.dedupeEnabled,
      batchEnabled: this.batchEnabled,
    };
  }
}
