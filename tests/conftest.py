"""
Pytest configuration and fixtures
"""
import pytest
from httpx import AsyncClient
from sqlmodel.ext.asyncio.session import AsyncSession

from app.main import app
from core.db.session import AsyncSessionLocal, engine
from sqlmodel import SQLModel


@pytest.fixture
async def db_session():
    """Create a test database session"""
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


@pytest.fixture(autouse=True)
async def setup_db():
    """Setup test database before each test"""
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.drop_all)

