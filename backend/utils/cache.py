"""Redis caching utilities for InventorySync"""

import json
import pickle
from typing import Optional, Any, Union
from datetime import timedelta
import redis.asyncio as redis
from functools import wraps
import hashlib
from config import settings
from utils.logging import logger

# Redis connection pool
redis_pool = None

async def get_redis_pool():
    """Get or create Redis connection pool"""
    global redis_pool
    if redis_pool is None:
        redis_pool = redis.ConnectionPool.from_url(
            settings.redis_url,
            decode_responses=True,
            max_connections=50
        )
    return redis_pool

async def get_redis_client():
    """Get Redis client"""
    pool = await get_redis_pool()
    return redis.Redis(connection_pool=pool)

class CacheManager:
    """Centralized cache management"""
    
    def __init__(self, prefix: str = "inventorysync"):
        self.prefix = prefix
        
    def _make_key(self, key: str) -> str:
        """Create namespaced cache key"""
        return f"{self.prefix}:{key}"
    
    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        try:
            client = await get_redis_client()
            value = await client.get(self._make_key(key))
            if value:
                return json.loads(value)
            return None
        except Exception as e:
            logger.warning(f"Cache get error: {e}")
            return None
    
    async def set(
        self, 
        key: str, 
        value: Any, 
        ttl: Optional[Union[int, timedelta]] = None
    ) -> bool:
        """Set value in cache"""
        try:
            client = await get_redis_client()
            serialized = json.dumps(value)
            
            if isinstance(ttl, timedelta):
                ttl = int(ttl.total_seconds())
            
            if ttl:
                await client.setex(self._make_key(key), ttl, serialized)
            else:
                await client.set(self._make_key(key), serialized)
            return True
        except Exception as e:
            logger.warning(f"Cache set error: {e}")
            return False
    
    async def delete(self, key: str) -> bool:
        """Delete value from cache"""
        try:
            client = await get_redis_client()
            await client.delete(self._make_key(key))
            return True
        except Exception as e:
            logger.warning(f"Cache delete error: {e}")
            return False
    
    async def delete_pattern(self, pattern: str) -> int:
        """Delete all keys matching pattern"""
        try:
            client = await get_redis_client()
            keys = []
            async for key in client.scan_iter(match=f"{self.prefix}:{pattern}"):
                keys.append(key)
            
            if keys:
                return await client.delete(*keys)
            return 0
        except Exception as e:
            logger.warning(f"Cache delete pattern error: {e}")
            return 0
    
    async def exists(self, key: str) -> bool:
        """Check if key exists"""
        try:
            client = await get_redis_client()
            return await client.exists(self._make_key(key)) > 0
        except Exception as e:
            logger.warning(f"Cache exists error: {e}")
            return False
    
    async def increment(self, key: str, amount: int = 1) -> Optional[int]:
        """Increment counter"""
        try:
            client = await get_redis_client()
            return await client.incrby(self._make_key(key), amount)
        except Exception as e:
            logger.warning(f"Cache increment error: {e}")
            return None
    
    async def expire(self, key: str, ttl: Union[int, timedelta]) -> bool:
        """Set expiration on existing key"""
        try:
            client = await get_redis_client()
            if isinstance(ttl, timedelta):
                ttl = int(ttl.total_seconds())
            return await client.expire(self._make_key(key), ttl)
        except Exception as e:
            logger.warning(f"Cache expire error: {e}")
            return False

# Global cache instance
cache = CacheManager()

def cache_key_wrapper(*args, **kwargs) -> str:
    """Generate cache key from function arguments"""
    key_parts = []
    for arg in args:
        if hasattr(arg, '__dict__'):
            # Skip self/cls arguments
            continue
        key_parts.append(str(arg))
    
    for k, v in sorted(kwargs.items()):
        key_parts.append(f"{k}:{v}")
    
    key_string = ":".join(key_parts)
    return hashlib.md5(key_string.encode()).hexdigest()

def cached(
    ttl: Union[int, timedelta] = 300,
    key_prefix: Optional[str] = None,
    key_func: Optional[callable] = None
):
    """Decorator for caching function results"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Generate cache key
            if key_func:
                cache_key = key_func(*args, **kwargs)
            else:
                cache_key = cache_key_wrapper(*args, **kwargs)
            
            if key_prefix:
                cache_key = f"{key_prefix}:{cache_key}"
            else:
                cache_key = f"{func.__module__}.{func.__name__}:{cache_key}"
            
            # Try to get from cache
            cached_value = await cache.get(cache_key)
            if cached_value is not None:
                logger.debug(f"Cache hit: {cache_key}")
                return cached_value
            
            # Execute function and cache result
            logger.debug(f"Cache miss: {cache_key}")
            result = await func(*args, **kwargs)
            
            if result is not None:
                await cache.set(cache_key, result, ttl)
            
            return result
        
        # Add cache control methods
        wrapper.invalidate = lambda *args, **kwargs: cache.delete(
            f"{key_prefix or f'{func.__module__}.{func.__name__}'}:{cache_key_wrapper(*args, **kwargs)}"
        )
        
        return wrapper
    return decorator

class RateLimiter:
    """Redis-based rate limiter"""
    
    def __init__(self, prefix: str = "ratelimit"):
        self.prefix = prefix
    
    async def is_allowed(
        self,
        key: str,
        limit: int,
        window: int = 60
    ) -> tuple[bool, int]:
        """Check if request is allowed under rate limit"""
        try:
            client = await get_redis_client()
            cache_key = f"{self.prefix}:{key}"
            
            # Use Redis pipeline for atomic operations
            pipe = client.pipeline()
            pipe.incr(cache_key)
            pipe.expire(cache_key, window)
            count, _ = await pipe.execute()
            
            remaining = max(0, limit - count)
            return count <= limit, remaining
        except Exception as e:
            logger.error(f"Rate limit error: {e}")
            # Fail open in case of Redis errors
            return True, limit

# Global rate limiter
rate_limiter = RateLimiter()

# Cache invalidation helpers
async def invalidate_product_cache(store_id: str, product_id: Optional[str] = None):
    """Invalidate product-related caches"""
    patterns = [
        f"products:{store_id}:*",
        f"inventory:{store_id}:*",
        f"dashboard:{store_id}:*"
    ]
    
    if product_id:
        patterns.extend([
            f"product:{product_id}:*",
            f"inventory:product:{product_id}:*"
        ])
    
    for pattern in patterns:
        await cache.delete_pattern(pattern)

async def invalidate_store_cache(store_id: str):
    """Invalidate all store-related caches"""
    await cache.delete_pattern(f"*:{store_id}:*")

# Session management
class SessionManager:
    """Redis-based session management"""
    
    def __init__(self, prefix: str = "session"):
        self.prefix = prefix
        self.ttl = timedelta(hours=24)
    
    async def create_session(self, session_id: str, data: dict) -> bool:
        """Create new session"""
        key = f"{self.prefix}:{session_id}"
        return await cache.set(key, data, self.ttl)
    
    async def get_session(self, session_id: str) -> Optional[dict]:
        """Get session data"""
        key = f"{self.prefix}:{session_id}"
        return await cache.get(key)
    
    async def update_session(self, session_id: str, data: dict) -> bool:
        """Update session data"""
        key = f"{self.prefix}:{session_id}"
        existing = await self.get_session(session_id)
        if existing:
            existing.update(data)
            return await cache.set(key, existing, self.ttl)
        return False
    
    async def delete_session(self, session_id: str) -> bool:
        """Delete session"""
        key = f"{self.prefix}:{session_id}"
        return await cache.delete(key)
    
    async def extend_session(self, session_id: str) -> bool:
        """Extend session TTL"""
        key = f"{self.prefix}:{session_id}"
        return await cache.expire(key, self.ttl)

# Global session manager
session_manager = SessionManager()
