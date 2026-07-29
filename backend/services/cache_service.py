import time
import threading
from typing import Any, Optional, Dict

class TTLCache:
    """
    A simple, thread-safe, in-memory TTL (Time-To-Live) cache.
    Useful for minimizing external WooCommerce API and other resource retrievals.
    """
    def __init__(self, default_ttl: float = 300.0):
        self.default_ttl = default_ttl
        self.cache: Dict[str, Dict[str, Any]] = {}
        self.lock = threading.Lock()

    def set(self, key: str, value: Any, ttl: Optional[float] = None) -> None:
        """Set a value in the cache with a specific TTL (in seconds)."""
        duration = ttl if ttl is not None else self.default_ttl
        expire_at = time.time() + duration
        with self.lock:
            self.cache[key] = {
                "value": value,
                "expire_at": expire_at
            }

    def get(self, key: str) -> Optional[Any]:
        """Retrieve a value from the cache if it exists and has not expired."""
        with self.lock:
            item = self.cache.get(key)
            if not item:
                return None
            
            if time.time() > item["expire_at"]:
                # Item has expired
                del self.cache[key]
                return None
                
            return item["value"]

    def get_stale(self, key: str) -> Optional[Any]:
        """Retrieve the value regardless of expiration (useful as fallback during network failure)."""
        with self.lock:
            item = self.cache.get(key)
            return item["value"] if item else None

    def invalidate(self, key: str) -> None:
        """Manually invalidate a cache key."""
        with self.lock:
            self.cache.pop(key, None)

# Shared global cache instance
global_cache = TTLCache(default_ttl=300.0)  # 5 minutes default
