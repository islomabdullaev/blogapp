from core.repositories.base import BaseRepository
from sqlmodel.ext.asyncio.session import AsyncSession

from app.blogs.models.posts import Post

class PostRepository(BaseRepository[Post]):
    def __init__(self, db: AsyncSession):
        super().__init__(Post, db)
