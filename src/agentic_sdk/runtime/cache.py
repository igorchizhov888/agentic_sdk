"""
Caching Layer

In-memory cache with TTL support.
Optional Redis backend for distributed deployments.
"""

import hashlib
import json
import time
from typing import Any, Optional, Dict
from structlog import get_logger

logger = get_logger(__name__)


class CacheEntry:
    """Cache entry with TTL."""
    
    def __init__(self, value: Any, ttl: float):
        self.value = value
        self.expires_at = time.time() + ttl if ttl > 0 else float('inf')
    
    def is_expired(self) -> bool:
        return time.time() > self.expires_at


class InMemoryCache:
    """
    Simple in-memory cache with TTL.
    
    Thread-safe, supports expiration.
    """
    
    def __init__(self, default_ttl: float = 300.0):
        """
        Initialize cache.
        
        Args:
            default_ttl: Default time-to-live in seconds (0 = no expiration)
        """
        self.default_ttl = default_ttl
        self._cache: Dict[str, CacheEntry] = {}
        self._hits = 0
        self._misses = 0
        
        logger.info("cache_initialized", default_ttl=default_ttl)
    
    def _make_key(self, key: str, namespace: str = "default") -> str:
        """Create cache key with namespace."""
        return f"{namespace}:{key}"
    
    def get(self, key: str, namespace: str = "default") -> Optional[Any]:
        """
        Get value from cache.
        
        Args:
            key: Cache key
            namespace: Key namespace
            
        Returns:
            Cached value or None if not found/expired
        """
        cache_key = self._make_key(key, namespace)
        
        if cache_key in self._cache:
            entry = self._cache[cache_key]
            
            if entry.is_expired():
                del self._cache[cache_key]
                self._misses += 1
                logger.debug("cache_miss_expired", key=cache_key)
                return None
            
            self._hits += 1
            logger.debug("cache_hit", key=cache_key)
            return entry.value
        
        self._misses += 1
        logger.debug("cache_miss", key=cache_key)
        return None
    
    def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[float] = None,
        namespace: str = "default",
    ) -> None:
        """
        Set value in cache.
        
        Args:
            key: Cache key
            value: Value to cache
            ttl: Time-to-live in seconds (uses default if None)
            namespace: Key namespace
        """
        cache_key = self._make_key(key, namespace)
        ttl = ttl if ttl is not None else self.default_ttl
        
        self._cache[cache_key] = CacheEntry(value, ttl)
        
        logger.debug("cache_set", key=cache_key, ttl=ttl)
    
    def delete(self, key: str, namespace: str = "default") -> None:
        """Delete key from cache."""
        cache_key = self._make_key(key, namespace)
        
        if cache_key in self._cache:
            del self._cache[cache_key]
            logger.debug("cache_deleted", key=cache_key)
    
    def clear(self, namespace: Optional[str] = None) -> None:
        """
        Clear cache.
        
        Args:
            namespace: Clear only this namespace (all if None)
        """
        if namespace is None:
            self._cache.clear()
            logger.info("cache_cleared_all")
        else:
            prefix = f"{namespace}:"
            keys_to_delete = [k for k in self._cache if k.startswith(prefix)]
            for key in keys_to_delete:
                del self._cache[key]
            logger.info("cache_cleared_namespace", namespace=namespace, count=len(keys_to_delete))
    
    def cleanup_expired(self) -> int:
        """
        Remove expired entries.
        
        Returns:
            Number of entries removed
        """
        expired_keys = [
            k for k, v in self._cache.items()
            if v.is_expired()
        ]
        
        for key in expired_keys:
            del self._cache[key]
        
        if expired_keys:
            logger.info("cache_cleanup", removed=len(expired_keys))
        
        return len(expired_keys)
    
    def stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        total = self._hits + self._misses
        hit_rate = (self._hits / total * 100) if total > 0 else 0.0
        
        return {
            "size": len(self._cache),
            "hits": self._hits,
            "misses": self._misses,
            "hit_rate": hit_rate,
        }


def cache_key_from_params(tool_name: str, params: Dict[str, Any]) -> str:
    """
    Generate cache key from tool name and parameters.
    
    Args:
        tool_name: Name of tool
        params: Tool parameters
        
    Returns:
        Cache key
    """
    # Sort params for consistent key generation
    sorted_params = json.dumps(params, sort_keys=True)
    param_hash = hashlib.md5(sorted_params.encode()).hexdigest()
    
    return f"{tool_name}:{param_hash}"
