import json
import time
from typing import Any, Optional
from threading import Lock

class InMemoryCache:
    def __init__(self):
        self._cache = {}
        self._expirations = {}
        self._lock = Lock()
    
    async def connect(self):
        """Initialize cache connection (no-op for in-memory)"""
        pass
    
    async def close(self):
        """Close cache connection (no-op for in-memory)"""
        pass
    
    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        with self._lock:
            # Check if key has expired
            if key in self._expirations:
                if time.time() > self._expirations[key]:
                    # Remove expired key
                    del self._cache[key]
                    del self._expirations[key]
                    return None
            
            return self._cache.get(key)
    
    async def set(self, key: str, value: Any, expire: Optional[int] = None):
        """Set value in cache with optional expiration (in seconds)"""
        with self._lock:
            self._cache[key] = value
            if expire:
                self._expirations[key] = time.time() + expire
            else:
                # Remove from expirations if it was previously set to expire
                if key in self._expirations:
                    del self._expirations[key]
    
    async def delete(self, key: str):
        """Delete key from cache"""
        with self._lock:
            if key in self._cache:
                del self._cache[key]
            if key in self._expirations:
                del self._expirations[key]
    
    async def exists(self, key: str) -> bool:
        """Check if key exists in cache"""
        if key in self._expirations:
            # Check if it's expired
            if time.time() > self._expirations[key]:
                # Remove expired key
                with self._lock:
                    if key in self._cache:
                        del self._cache[key]
                    if key in self._expirations:
                        del self._expirations[key]
                return False
        return key in self._cache
    
    async def expire(self, key: str, ttl: int):
        """Set expiration time for a key"""
        with self._lock:
            if key in self._cache:
                self._expirations[key] = time.time() + ttl
    
    async def clear_pattern(self, pattern: str):
        """Delete all keys matching a pattern"""
        with self._lock:
            keys_to_delete = [key for key in self._cache.keys() if pattern in key]
            for key in keys_to_delete:
                if key in self._cache:
                    del self._cache[key]
                if key in self._expirations:
                    del self._expirations[key]

# Global cache instance
cache = InMemoryCache()

# Convenience methods for common cache operations
async def get_slot_status(slot_id: str):
    """Get cached slot status"""
    return await cache.get(f"slot:{slot_id}")

async def set_slot_status(slot_id: str, status: dict, ttl: int = 300):  # 5 minutes
    """Cache slot status"""
    await cache.set(f"slot:{slot_id}", status, ttl)

async def invalidate_slot_status(slot_id: str):
    """Remove slot status from cache"""
    await cache.delete(f"slot:{slot_id}")

async def get_user_bookings(user_id: str):
    """Get cached user bookings"""
    return await cache.get(f"user:{user_id}:bookings")

async def set_user_bookings(user_id: str, bookings: list, ttl: int = 60):  # 1 minute
    """Cache user bookings"""
    await cache.set(f"user:{user_id}:bookings", bookings, ttl)

async def invalidate_user_bookings(user_id: str):
    """Remove cached user bookings"""
    await cache.delete(f"user:{user_id}:bookings")

async def get_slot_list():
    """Get cached list of all slots"""
    return await cache.get("slots:all")

async def set_slot_list(slots: list, ttl: int = 300):  # 5 minutes
    """Cache list of all slots"""
    await cache.set("slots:all", slots, ttl)

async def invalidate_slot_list():
    """Remove cached slot list"""
    await cache.delete("slots:all")