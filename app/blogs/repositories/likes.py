from typing import Optional
from uuid import UUID

from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.blogs.models.posts import PostLike
from core.repositories.base import BaseRepository


class PostLikeRepository(BaseRepository[PostLike]):
    def __init__(self, db: AsyncSession):
        self.db = db
        self.model = PostLike

    async def get_by_user_and_post(
        self, user_id: UUID, post_id: UUID
    ) -> Optional[PostLike]:
        statement = select(PostLike).where(
            PostLike.user_id == user_id,
            PostLike.post_id == post_id,
            PostLike.is_deleted == False,
        )
        result = await self.db.exec(statement)
        return result.first()
