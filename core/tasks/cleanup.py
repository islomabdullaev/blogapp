"""
Celery tasks for cleanup operations
"""
import asyncio
import logging
from datetime import datetime

from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlmodel.ext.asyncio.session import AsyncSession

from core.celery_app import celery_app
from core.settings import Settings
from app.auth.repositories.verification import VerificationRepository
from app.users.repositories.users import UserRepository
from app.blogs.repositories.posts import PostRepository
from app.blogs.models.posts import Post
from sqlmodel import select

logger = logging.getLogger(__name__)

settings = Settings()
DATABASE_URL = settings.postgres.adsn

engine = create_async_engine(DATABASE_URL, echo=False)
AsyncSessionLocal = sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)


async def _cleanup_expired_unverified_users_async():
    """Async function to clean up expired unverified users"""
    async with AsyncSessionLocal() as db:
        try:
            verification_repo = VerificationRepository(db)
            user_repo = UserRepository(db)

            # Get expired unverified verifications
            expired_verifications = await verification_repo.get_expired_unverified()

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


async def _cleanup_expired_posts_async():
    """Async function to clean up expired posts"""
    async with AsyncSessionLocal() as db:
        try:
            post_repo = PostRepository(db)
            now = datetime.utcnow()

            # Get expired posts
            statement = select(Post).where(
                Post.expires_at.isnot(None),
                Post.expires_at < now,
                Post.is_deleted == False,
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


@celery_app.task(name="core.tasks.cleanup.cleanup_expired_unverified_users")
def cleanup_expired_unverified_users():
    """Clean up users whose email verification has expired (runs daily)"""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(_cleanup_expired_unverified_users_async())
    finally:
        loop.close()


@celery_app.task(name="core.tasks.cleanup.cleanup_expired_posts")
def cleanup_expired_posts():
    """Clean up expired posts (runs daily)"""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(_cleanup_expired_posts_async())
    finally:
        loop.close()
