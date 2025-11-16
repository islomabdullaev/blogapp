from uuid import UUID

from fastapi import HTTPException, status
from sqlmodel.ext.asyncio.session import AsyncSession

from app.blogs.repositories.likes import PostLikeRepository
from app.blogs.repositories.posts import PostRepository
from app.blogs.schemas.posts import PostLikeSchema
from app.users.models.users import User


class PostLikeService:
    def __init__(self, db: AsyncSession):
        self.repo = PostLikeRepository(db)
        self.post_repo = PostRepository(db)

    async def toggle_like(self, post_id: UUID, user: User):
        if not user.is_verified:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Unverified users cannot create posts. Please verify your email first.",
            )
        # Check if post exists and is not expired
        post = await self.post_repo.get(post_id)
        if not post:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Post not found"
            )
        if post.is_expired():
            raise HTTPException(
                status_code=status.HTTP_410_GONE, detail="Post has expired"
            )

        # Check if user is trying to like their own post
        if post.user_id == user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You cannot like your own post",
            )

        existing_like = await self.repo.get_by_user_and_post(
            user_id=user.id, post_id=post_id
        )
        if existing_like:
            await self.repo.delete(existing_like)
            return {"liked": False, "message": "Post unliked"}
        else:
            data = PostLikeSchema(user_id=user.id, post_id=post.id)
            await self.repo.create(data)
            return {"liked": True, "message": "Post liked"}

    async def check_like(self, post_id: UUID, user: User) -> bool:
        like = await self.repo.get_by_user_and_post(user_id=user.id, post_id=post_id)
        return like is not None
