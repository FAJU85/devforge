#!/usr/bin/env python3
"""
Cache Service - Phase 8.2
Multi-layer Redis-backed caching system with TTL and invalidation management
"""

import json
import logging
import os
from typing import Any, Optional, Dict, List
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class CacheService:
    """Redis-backed cache service with fallback to in-memory caching"""

    def __init__(self):
        self.redis_client = None
        self.redis_enabled = False
        self.in_memory_cache: Dict[str, tuple] = {}
        self._init_redis()

    def _init_redis(self):
        """Initialize Redis connection if available"""
        try:
            redis_url = os.environ.get("REDIS_URL", "redis://localhost:6379/0")

            try:
                import redis
                self.redis_client = redis.from_url(redis_url, decode_responses=True)
                self.redis_client.ping()
                self.redis_enabled = True
                logger.info("Redis cache enabled successfully")
            except ImportError:
                logger.warning("redis module not installed, using in-memory cache")
                self.redis_enabled = False
            except Exception as e:
                logger.warning(f"Failed to connect to Redis: {e}, using in-memory cache")
                self.redis_enabled = False

        except Exception as e:
            logger.error(f"Error initializing cache service: {e}")
            self.redis_enabled = False

    def _generate_cache_key(self, namespace: str, key_parts: List[str]) -> str:
        """Generate cache key with namespace"""
        full_key = f"{namespace}:" + ":".join(str(p) for p in key_parts)
        return full_key

    async def get(self, namespace: str, key_parts: List[str]) -> Optional[Any]:
        """Get value from cache"""
        try:
            cache_key = self._generate_cache_key(namespace, key_parts)

            if self.redis_enabled:
                try:
                    value = self.redis_client.get(cache_key)
                    if value:
                        return json.loads(value)
                except Exception as e:
                    logger.error(f"Redis get error: {e}, falling back to in-memory")
                    self.redis_enabled = False

            # In-memory fallback
            if cache_key in self.in_memory_cache:
                value, expiry = self.in_memory_cache[cache_key]
                if expiry > datetime.utcnow():
                    return value
                else:
                    del self.in_memory_cache[cache_key]

            return None
        except Exception as e:
            logger.error(f"Cache get error: {e}")
            return None

    async def set(
        self,
        namespace: str,
        key_parts: List[str],
        value: Any,
        ttl_seconds: int = 300
    ) -> bool:
        """Set value in cache with TTL"""
        try:
            cache_key = self._generate_cache_key(namespace, key_parts)
            expiry_time = datetime.utcnow() + timedelta(seconds=ttl_seconds)

            if self.redis_enabled:
                try:
                    self.redis_client.setex(
                        cache_key,
                        ttl_seconds,
                        json.dumps(value, default=str)
                    )
                except Exception as e:
                    logger.error(f"Redis set error: {e}, falling back to in-memory")
                    self.redis_enabled = False

            # In-memory fallback
            self.in_memory_cache[cache_key] = (value, expiry_time)

            # Cleanup old entries (simple LRU)
            if len(self.in_memory_cache) > 10000:
                oldest_key = min(
                    self.in_memory_cache.keys(),
                    key=lambda k: self.in_memory_cache[k][1]
                )
                del self.in_memory_cache[oldest_key]

            return True
        except Exception as e:
            logger.error(f"Cache set error: {e}")
            return False

    async def delete(self, namespace: str, key_parts: List[str]) -> bool:
        """Delete value from cache"""
        try:
            cache_key = self._generate_cache_key(namespace, key_parts)

            if self.redis_enabled:
                try:
                    self.redis_client.delete(cache_key)
                except Exception as e:
                    logger.warning(f"Redis delete error: {e}")

            if cache_key in self.in_memory_cache:
                del self.in_memory_cache[cache_key]

            return True
        except Exception as e:
            logger.error(f"Cache delete error: {e}")
            return False

    async def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        try:
            stats = {
                "in_memory_size": len(self.in_memory_cache),
                "redis_enabled": self.redis_enabled,
                "redis_memory_bytes": 0
            }

            if self.redis_enabled:
                try:
                    info = self.redis_client.info("memory")
                    stats["redis_memory_bytes"] = info.get("used_memory", 0)
                    stats["redis_keys"] = self.redis_client.dbsize()
                except Exception as e:
                    logger.warning(f"Redis stats error: {e}")

            return stats
        except Exception as e:
            logger.error(f"Cache stats error: {e}")
            return {}


class APIResponseCache:
    """API response caching with smart TTL by endpoint"""

    DEFAULT_TTLS = {
        "/api/models": 3600,
        "/api/config": 1800,
        "/api/chat/history": 300,
        "/api/repo": 300,
        "/api/providers": 3600,
    }

    def __init__(self, cache_service: CacheService):
        self.cache = cache_service
        self.hit_count = 0
        self.miss_count = 0

    def _get_ttl_for_endpoint(self, endpoint: str) -> int:
        """Get TTL for endpoint"""
        for pattern, ttl in self.DEFAULT_TTLS.items():
            if pattern in endpoint:
                return ttl
        return 300

    async def get_cached_response(self, user_id: str, method: str, endpoint: str) -> Optional[Dict]:
        """Get cached API response"""
        try:
            cache_key = [user_id, method, endpoint]
            result = await self.cache.get("api_response", cache_key)
            if result:
                self.hit_count += 1
            else:
                self.miss_count += 1
            return result
        except Exception as e:
            logger.error(f"Error getting cached response: {e}")
            return None

    async def cache_response(self, user_id: str, method: str, endpoint: str, response: Dict) -> bool:
        """Cache API response"""
        try:
            if method not in ["GET", "HEAD"]:
                return False
            ttl = self._get_ttl_for_endpoint(endpoint)
            cache_key = [user_id, method, endpoint]
            return await self.cache.set("api_response", cache_key, response, ttl)
        except Exception as e:
            logger.error(f"Error caching response: {e}")
            return False

    def get_hit_rate(self) -> float:
        """Get cache hit rate"""
        total = self.hit_count + self.miss_count
        return (self.hit_count / total * 100) if total > 0 else 0


cache_service = CacheService()
api_response_cache = APIResponseCache(cache_service)
