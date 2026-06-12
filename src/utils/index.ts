/**
 * Utilities - request optimization and performance utilities
 */

export { RequestCache, createCacheKey } from './requestCache';
export type { CacheEntry, CacheConfig } from './requestCache';

export { RequestDeduplicator } from './requestDeduplicator';
export type { PendingRequest } from './requestDeduplicator';

export { RequestBatcher } from './requestBatcher';
export type { BatchRequest, BatchConfig } from './requestBatcher';
