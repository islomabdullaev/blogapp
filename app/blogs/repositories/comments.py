from typing import List

from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.blogs.models.posts import Comment
from core.repositories.base import BaseRepository


class CommentRepository(BaseRepository[Comment]):
    def __init__(self, db: AsyncSession):
        super().__init__(Comment, db)

    async def get_by_post_id(self, post_id) -> List[Comment]:
        statement = select(Comment).where(
            Comment.post_id == post_id, Comment.is_deleted == False
        )
        result = await self.db.exec(statement)
        return result.all()

    async def delete_all_by_post_id(self, post_id):
        """Delete all comments of a post (soft delete)"""
        statement = select(Comment).where(
            Comment.post_id == post_id, Comment.is_deleted == False
        )
        result = await self.db.exec(statement)
        comments = result.all()

        for comment in comments:
            comment.is_deleted = True

        await self.db.commit()
        return len(comments)
