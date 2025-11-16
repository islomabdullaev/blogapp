from uuid import UUID
from sqlmodel.ext.asyncio.session import AsyncSession
from fastapi import HTTPException, status

from app.blogs.repositories.comments import CommentRepository
from app.blogs.repositories.posts import PostRepository
from app.blogs.models.posts import Comment, Post
from app.users.models.users import User
from app.blogs.schemas.comments import CommentCreateSchema
from core.security.sanitizer import sanitize_string


class CommentService:
    def __init__(self, db: AsyncSession):
        self.repo = CommentRepository(db)
        self.post_repo = PostRepository(db)

    async def create_comment(
        self, post_id: UUID, data: CommentCreateSchema, user: User
    ) -> Comment:
        # Check if user is verified
        if not user.is_verified:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Unverified users cannot create comments. Please verify your email first.",
            )

        # Check if post exists and is not expired
        post = await self.post_repo.get(post_id)
        if not post:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Post not found"
            )
        comment_data = data.model_dump()
        # Sanitize input to prevent XSS
        comment_data["text"] = sanitize_string(comment_data["text"])
        comment_data["post_id"] = post_id
        comment_data["user_id"] = user.id
        return await self.repo.create(comment_data)

    async def get_comments_by_post(self, post_id: UUID):
        return await self.repo.get_by_post_id(post_id)

    async def delete_comment(self, post_id: UUID, comment_id: UUID, user: User):
        comment = await self.repo.get(comment_id)
        if not comment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Comment not found"
            )

        # Verify comment belongs to the post
        if comment.post_id != post_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Comment does not belong to this post",
            )

        if comment.user_id != user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only delete your own comments",
            )
        await self.repo.delete(comment)

    async def delete_comment_by_id(self, comment_id: UUID, user: User):
        """Delete comment by its UUID only"""
        comment = await self.repo.get(comment_id)
        if not comment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Comment not found"
            )

        if comment.user_id != user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only delete your own comments",
            )
        await self.repo.delete(comment)

    async def delete_all_comments_by_post(self, post_id: UUID, user: User):
        """Delete all comments of a post - only post owner can do this"""
        # Check if post exists
        post = await self.post_repo.get(post_id)
        if not post:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Post not found"
            )

        # Only post owner can delete all comments
        if post.user_id != user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only delete comments from your own posts",
            )

        deleted_count = await self.repo.delete_all_by_post_id(post_id)
        return {"deleted_count": deleted_count, "message": f"Deleted {deleted_count} comment(s)"}

