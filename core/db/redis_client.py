"""Redis client for caching and rate limiting"""

import redis.asyncio as redis

from core.settings import Settings

settings = Settings()
_redis_client: redis.Redis = None


async def get_redis_client() -> redis.Redis:
    """Get or create Redis client"""
    global _redis_client
    if _redis_client is None:
        try:
            _redis_client = redis.from_url(
                settings.redis.dsn, encoding="utf-8", decode_responses=True
            )
            # Test connection
            await _redis_client.ping()
        except Exception:
            # If Redis is not available, return None
            # The application will work without Redis, but without rate limiting
            _redis_client = None
    return _redis_client


async def close_redis_client():
    """Close Redis connection"""
    global _redis_client
    if _redis_client:
        await _redis_client.close()
        _redis_client = None
