"""
Celery application configuration
"""

from celery import Celery
from celery.schedules import crontab

from core.settings import Settings

settings = Settings()

celery_app = Celery(
    "social_network",
    broker=settings.redis.dsn,
    backend=settings.redis.dsn,
    include=["core.tasks.cleanup"],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30 * 60,  # 30 minutes
    task_soft_time_limit=25 * 60,  # 25 minutes
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=1000,
)

# Celery Beat schedule
celery_app.conf.beat_schedule = {
    "cleanup-expired-unverified-users": {
        "task": "core.tasks.cleanup.cleanup_expired_unverified_users",
        "schedule": crontab(hour=23, minute=59),  # Run every day at 23:59 UTC
    },
    "cleanup-expired-posts": {
        "task": "core.tasks.cleanup.cleanup_expired_posts",
        "schedule": crontab(hour=23, minute=59),  # Run every day at 23:59 UTC
    },
}
