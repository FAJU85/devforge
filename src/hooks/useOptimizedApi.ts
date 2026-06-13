/**
 * useOptimizedApi Hook - optimized API calls with caching and deduplication
 */

import { useCallback, useMemo } from 'react';
import { OptimizedApiClient, OptimizedClientConfig } from '../api/optimizedClient';

export interface UseOptimizedApiReturn {
  // Client instance
  client: OptimizedApiClient;

  // HTTP methods
  get: <T = any>(endpoint: string, options?: RequestInit) => Promise<any>;
  post: <T = any>(endpoint: string, data?: any, options?: RequestInit) => Promise<any>;
  put: <T = any>(endpoint: string, data?: any, options?: RequestInit) => Promise<any>;
  patch: <T = any>(endpoint: string, data?: any, options?: RequestInit) => Promise<any>;
  delete: <T = any>(endpoint: string, options?: RequestInit) => Promise<any>;

  // Cache management
  clearCache: () => void;
  invalidateCache: (pattern: RegExp | string) => number;
  getCacheStats: () => any;

  // Optimization control
  setOptimizations: (options: { cache?: boolean; dedupe?: boolean; batch?: boolean }) => void;
  getOptimizations: () => { cacheEnabled: boolean; dedupeEnabled: boolean; batchEnabled: boolean };
  getStats: () => any;

  // Batch operations
  flushBatch: () => Promise<void>;
}

export function useOptimizedApi(config: OptimizedClientConfig): UseOptimizedApiReturn {
  // Create client instance (memoized)
  const client = useMemo(() => new OptimizedApiClient(config), [config.baseUrl]);

  // HTTP methods
  const get = useCallback(
    async <T = any>(endpoint: string, options?: RequestInit) => {
      return client.get<T>(endpoint, options);
    },
    [client]
  );

  const post = useCallback(
    async <T = any>(endpoint: string, data?: any, options?: RequestInit) => {
      return client.post<T>(endpoint, data, options);
    },
    [client]
  );

  const put = useCallback(
    async <T = any>(endpoint: string, data?: any, options?: RequestInit) => {
      return client.put<T>(endpoint, data, options);
    },
    [client]
  );

  const patch = useCallback(
    async <T = any>(endpoint: string, data?: any, options?: RequestInit) => {
      return client.patch<T>(endpoint, data, options);
    },
    [client]
  );

  const del = useCallback(
    async <T = any>(endpoint: string, options?: RequestInit) => {
      return client.delete<T>(endpoint, options);
    },
    [client]
  );

  // Cache management
  const clearCache = useCallback(() => {
    client.clearCache();
  }, [client]);

  const invalidateCache = useCallback((pattern: RegExp | string) => {
    return client.invalidateCache(pattern);
  }, [client]);

  const getCacheStats = useCallback(() => {
    return client.getCacheStats();
  }, [client]);

  // Optimization control
  const setOptimizations = useCallback(
    (options: { cache?: boolean; dedupe?: boolean; batch?: boolean }) => {
      client.setOptimizations(options);
    },
    [client]
  );

  const getOptimizations = useCallback(() => {
    return client.getOptimizationStatus();
  }, [client]);

  const getStats = useCallback(() => {
    return client.getStats();
  }, [client]);

  // Batch operations
  const flushBatch = useCallback(async () => {
    await client.flushBatch();
  }, [client]);

  return {
    client,
    get,
    post,
    put,
    patch,
    delete: del,
    clearCache,
    invalidateCache,
    getCacheStats,
    setOptimizations,
    getOptimizations,
    getStats,
    flushBatch,
  };
}
