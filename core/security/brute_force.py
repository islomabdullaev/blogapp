"""Brute force protection utilities"""

from typing import Optional

import redis.asyncio as redis
from fastapi import HTTPException, status

from core.settings import Settings

settings = Settings()


class BruteForceProtection:
    """Protection against brute force attacks"""

    def __init__(self, redis_client: Optional[redis.Redis] = None):
        self.redis_client = redis_client
        self.max_attempts = 5  # Maximum failed login attempts
        self.lockout_duration = 900  # 15 minutes in seconds
        self.attempt_window = 300  # 5 minutes window for counting attempts

    async def check_attempts(self, identifier: str) -> None:
        """
        Check if identifier (IP or email) has exceeded max attempts
        Raises HTTPException if blocked
        """
        if not self.redis_client:
            return  # Skip protection if Redis is not available

        key = f"brute_force:{identifier}"
        try:
            attempts = await self.redis_client.get(key)
            if attempts and int(attempts) >= self.max_attempts:
                # Check if still in lockout period
                ttl = await self.redis_client.ttl(key)
                if ttl > 0:
                    raise HTTPException(
                        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                        detail=f"Too many failed login attempts. Please try again in {ttl // 60} minutes.",
                    )
        except redis.RedisError:
            pass  # If Redis fails, allow the request

    async def record_failed_attempt(self, identifier: str) -> None:
        """Record a failed login attempt"""
        if not self.redis_client:
            return

        key = f"brute_force:{identifier}"
        try:
            pipe = self.redis_client.pipeline()
            pipe.incr(key)
            pipe.expire(key, self.attempt_window)
            await pipe.execute()
        except redis.RedisError:
            pass

    async def record_successful_login(self, identifier: str) -> None:
        """Clear failed attempts on successful login"""
        if not self.redis_client:
            return

        key = f"brute_force:{identifier}"
        try:
            await self.redis_client.delete(key)
        except redis.RedisError:
            pass

    async def block_identifier(self, identifier: str) -> None:
        """Block identifier for lockout duration"""
        if not self.redis_client:
            return

        key = f"brute_force:{identifier}"
        try:
            await self.redis_client.setex(key, self.lockout_duration, self.max_attempts)
        except redis.RedisError:
            pass
