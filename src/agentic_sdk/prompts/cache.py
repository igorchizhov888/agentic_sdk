"""Cache layer for prompt management"""
from typing import Optional, Dict
from datetime import datetime, timedelta
import threading


class PromptCache:
    """Thread-safe LRU cache for prompts"""
    
    def __init__(self, max_size: int = 100, ttl_seconds: int = 300):
        """
        Initialize prompt cache.
        
        Args:
            max_size: Maximum number of cached items
            ttl_seconds: Time to live for cached items (default 5 minutes)
        """
        self.max_size = max_size
        self.ttl_seconds = ttl_seconds
        self._cache: Dict[str, tuple[str, datetime]] = {}
        self._lock = threading.Lock()
    
    def get(self, key: str) -> Optional[str]:
        """Get cached prompt if not expired"""
        with self._lock:
            if key not in self._cache:
                return None
            
            prompt, timestamp = self._cache[key]
            
            # Check if expired
            if datetime.now() - timestamp > timedelta(seconds=self.ttl_seconds):
                del self._cache[key]
                return None
            
            return prompt
    
    def set(self, key: str, prompt: str):
        """Cache a prompt"""
        with self._lock:
            # If cache is full, remove oldest entry
            if len(self._cache) >= self.max_size:
                oldest_key = min(self._cache.keys(), 
                               key=lambda k: self._cache[k][1])
                del self._cache[oldest_key]
            
            self._cache[key] = (prompt, datetime.now())
    
    def invalidate(self, key: str):
        """Remove item from cache"""
        with self._lock:
            if key in self._cache:
                del self._cache[key]
    
    def clear(self):
        """Clear entire cache"""
        with self._lock:
            self._cache.clear()
    
    def stats(self) -> Dict[str, int]:
        """Get cache statistics"""
        with self._lock:
            return {
                "size": len(self._cache),
                "max_size": self.max_size,
                "ttl_seconds": self.ttl_seconds
            }
