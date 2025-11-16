import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

# routers
from app.auth.routers.auth import router as auth_router
from app.blogs.routers.router import router as blog_router
from app.users.routers.router import router as user_router
from core.db.redis_client import close_redis_client, get_redis_client
from core.db.session import init_db
from core.middleware.rate_limit import RateLimitMiddleware
from core.middleware.security_headers import SecurityHeadersMiddleware

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup and shutdown events"""
    # Startup
    await init_db()
    logger.info("Database initialized")

    # Initialize Redis connection
    redis_client = await get_redis_client()
    if redis_client:
        logger.info("Redis connection established")
    else:
        logger.warning(
            "Redis not available - rate limiting and brute force protection disabled"
        )

    yield

    # Shutdown
    await close_redis_client()
    logger.info("Application shutting down")


app = FastAPI(title="Social Network API", lifespan=lifespan)

# Add security middleware
app.add_middleware(SecurityHeadersMiddleware)

# Add rate limiting middleware (Redis will be initialized asynchronously in middleware)
app.add_middleware(RateLimitMiddleware)

app.include_router(auth_router, prefix="/api/auth")
app.include_router(user_router, prefix="/api/user")
app.include_router(blog_router, prefix="/api/blog")
