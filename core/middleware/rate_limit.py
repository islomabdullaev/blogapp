"""Rate limiting middleware for DOS protection"""

from typing import Callable, Optional

import redis.asyncio as redis
from fastapi import HTTPException, Request, status
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

from core.db.redis_client import get_redis_client
from core.settings import Settings

settings = Settings()


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Middleware to limit request rate per IP address"""

    def __init__(self, app, redis_client: Optional[redis.Redis] = None):
        super().__init__(app)
        self._redis_client = redis_client
        # Rate limits: requests per window (in seconds)
        self.limits = {
            "/api/auth/login": (5, 60),  # 5 requests per 60 seconds
            "/api/auth/register": (3, 60),  # 3 requests per 60 seconds
            "default": (100, 60),  # 100 requests per 60 seconds for other endpoints
        }

    async def _get_redis(self) -> Optional[redis.Redis]:
        """Get Redis client, initializing if needed"""
        if self._redis_client is None:
            self._redis_client = await get_redis_client()
        return self._redis_client

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Skip rate limiting for documentation endpoints
        path = request.url.path
        excluded_paths = ["/docs", "/redoc", "/openapi.json", "/docs/oauth2-redirect"]
        if any(path.startswith(excluded) for excluded in excluded_paths):
            return await call_next(request)

        # Get client IP
        client_ip = request.client.host
        if not client_ip:
            client_ip = "unknown"

        # Get rate limit for this endpoint
        limit, window = self.limits.get(path, self.limits["default"])

        redis_client = await self._get_redis()
        if redis_client:
            # Check rate limit using Redis
            key = f"rate_limit:{client_ip}:{path}"
            try:
                current = await redis_client.get(key)
                if current and int(current) >= limit:
                    raise HTTPException(
                        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                        detail=f"Rate limit exceeded. Maximum {limit} requests per {window} seconds.",
                    )

                # Increment counter
                pipe = redis_client.pipeline()
                pipe.incr(key)
                pipe.expire(key, window)
                await pipe.execute()
            except redis.RedisError:
                # If Redis is unavailable, allow request but log warning
                pass

        response = await call_next(request)
        return response
