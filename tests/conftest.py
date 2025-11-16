"""
Pytest configuration and fixtures
"""

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlmodel import SQLModel
from sqlmodel.ext.asyncio.session import AsyncSession

# Import all models to register them with SQLModel metadata
from app.auth.models.verification import EmailVerification
from app.blogs.models.posts import Comment, Post, PostLike
from app.main import app
from app.users.models.users import User
from core.settings import Settings

settings = Settings()
DATABASE_URL = settings.postgres.adsn


@pytest.fixture(scope="function")
async def test_engine():
    """Create a fresh engine for each test"""
    engine = create_async_engine(
        DATABASE_URL,
        echo=False,
        pool_pre_ping=True,
        pool_size=1,
        max_overflow=0,
    )
    yield engine
    await engine.dispose()


@pytest.fixture(scope="function")
async def db_session(test_engine):
    """Create a test database session"""
    AsyncSessionLocal = async_sessionmaker(
        test_engine, class_=AsyncSession, expire_on_commit=False
    )
    async with AsyncSessionLocal() as session:
        yield session
        await session.rollback()


@pytest.fixture
async def client(db_session):
    """Create a test client"""

    async def get_test_session():
        yield db_session

    app.dependency_overrides = {}
    # Override get_session dependency
    from core.db.session import get_session

    app.dependency_overrides[get_session] = get_test_session

    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()


@pytest.fixture(autouse=True, scope="function")
async def setup_db(test_engine):
    """Setup test database before each test"""
    async with test_engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.drop_all)
