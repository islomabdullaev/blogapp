"""
Celery tasks for cleanup operations
"""

import asyncio
import logging
from datetime import datetime, timedelta

from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.auth.models.verification import EmailVerification
from app.auth.repositories.verification import VerificationRepository
from app.blogs.models.posts import Post
from app.blogs.repositories.posts import PostRepository
from app.users.repositories.users import UserRepository
from core.celery_app import celery_app
from core.settings import Settings

logger = logging.getLogger(__name__)

settings = Settings()
DATABASE_URL = settings.postgres.adsn


async def _cleanup_expired_unverified_users_async():
    """Async function to clean up unverified users older than 1 month"""
    # Create engine and session maker fresh for each task execution
    # This ensures they're tied to the current event loop created by asyncio.run()
    engine = create_async_engine(
        DATABASE_URL,
        echo=False,
        pool_pre_ping=True,
        pool_size=2,  # Smaller pool for individual tasks
        max_overflow=5,
    )
    AsyncSessionLocal = async_sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )

    try:
        async with AsyncSessionLocal() as db:
            try:
                verification_repo = VerificationRepository(db)
                user_repo = UserRepository(db)

                # Calculate date 1 month ago
                one_month_ago = datetime.utcnow() - timedelta(days=30)

                # Get unverified verifications older than 1 month
                statement = select(EmailVerification).where(
                    EmailVerification.is_verified.is_(False),
                    EmailVerification.created_at < one_month_ago,
                    EmailVerification.is_deleted.is_(False),
                )
                result = await db.exec(statement)
                expired_verifications = result.all()

                deleted_count = 0
                user_ids_to_delete = []

                for verification in expired_verifications:
                    user_ids_to_delete.append(str(verification.user_id))
                    # Delete verification record
                    await verification_repo.delete(verification)

                # Delete users
                if user_ids_to_delete:
                    users = await user_repo.get_users_by_user_ids(user_ids_to_delete)
                    for user in users:
                        await user_repo.delete(user)
                        deleted_count += 1

                await db.commit()
                logger.info(
                    f"Cleaned up {deleted_count} expired unverified users at {datetime.utcnow()}"
                )
                return {
                    "deleted_count": deleted_count,
                    "timestamp": datetime.utcnow().isoformat(),
                }
            except Exception as e:
                logger.error(f"Error cleaning up expired unverified users: {e}")
                await db.rollback()
                raise
    finally:
        # Dispose of the engine to close all connections
        await engine.dispose()


async def _cleanup_expired_posts_async():
    """Async function to clean up posts older than 1 month"""
    # Create engine and session maker fresh for each task execution
    # This ensures they're tied to the current event loop created by asyncio.run()
    engine = create_async_engine(
        DATABASE_URL,
        echo=False,
        pool_pre_ping=True,
        pool_size=2,  # Smaller pool for individual tasks
        max_overflow=5,
    )
    AsyncSessionLocal = async_sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )

    try:
        async with AsyncSessionLocal() as db:
            try:
                post_repo = PostRepository(db)

                # Calculate date 1 month ago
                one_month_ago = datetime.utcnow() - timedelta(days=30)

                # Get posts older than 1 month
                statement = select(Post).where(
                    Post.created_at < one_month_ago,
                    Post.is_deleted.is_(False),
                )

                result = await db.exec(statement)
                expired_posts = result.all()

                deleted_count = 0
                for post in expired_posts:
                    await post_repo.delete(post)
                    deleted_count += 1

                await db.commit()
                logger.info(
                    f"Cleaned up {deleted_count} expired posts at {datetime.utcnow()}"
                )
                return {
                    "deleted_count": deleted_count,
                    "timestamp": datetime.utcnow().isoformat(),
                }
            except Exception as e:
                logger.error(f"Error cleaning up expired posts: {e}")
                await db.rollback()
                raise
    finally:
        # Dispose of the engine to close all connections
        await engine.dispose()


@celery_app.task(name="core.tasks.cleanup.cleanup_expired_unverified_users")
def cleanup_expired_unverified_users():
    """Clean up unverified users older than 1 month (runs daily)"""
    # Use asyncio.run() which properly creates and manages the event loop
    # This ensures proper isolation between task executions and prevents
    # connection conflicts that occur when manually managing event loops
    return asyncio.run(_cleanup_expired_unverified_users_async())


@celery_app.task(name="core.tasks.cleanup.cleanup_expired_posts")
def cleanup_expired_posts():
    """Clean up posts older than 1 month (runs daily)"""
    # Use asyncio.run() which properly creates and manages the event loop
    # This ensures proper isolation between task executions and prevents
    # connection conflicts that occur when manually managing event loops
    return asyncio.run(_cleanup_expired_posts_async())
