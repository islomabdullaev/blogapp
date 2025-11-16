from sqlmodel import SQLModel
from sqlmodel.ext.asyncio.session import AsyncSession

from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.orm import sessionmaker

from core.settings import Settings

settings = Settings()
DATABASE_URL = settings.postgres.adsn

engine = create_async_engine(DATABASE_URL, echo=True)
AsyncSessionLocal = sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)

async def get_session():
    async with AsyncSessionLocal() as session:
        yield session

async def init_db():
    # Import all models to register them with SQLModel metadata
    # This must happen before create_all() is called
    from app.users.models.users import User  # noqa: F401
    from app.blogs.models.posts import Post, PostLike, Comment  # noqa: F401
    from app.auth.models.verification import EmailVerification  # noqa: F401

    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)
