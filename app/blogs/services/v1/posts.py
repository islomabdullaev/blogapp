import json
from datetime import datetime
from typing import List
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import JSON
from sqlmodel import and_, func, or_, select
from sqlmodel.ext.asyncio.session import AsyncSession

# models
from app.blogs.models.posts import Post, PostLike

# repo
from app.blogs.repositories.posts import PostRepository

# schemas
from app.blogs.schemas.posts import (
    ArticleSchema,
    PostCreateSchema,
    PostUpdateSchema,
    UserWithArticlesListResponseSchema,
    UserWithArticlesSchema,
)
from app.users.models.users import User

# security
from core.security.sanitizer import sanitize_string


class PostService:

    def __init__(self, db: AsyncSession):
        self.repo = PostRepository(db)

    async def create_post(self, data: PostCreateSchema, user: User) -> Post:
        if not user.is_verified:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Unverified users cannot create posts. Please verify your email first.",
            )

        # Sanitize input to prevent XSS
        post_data = data.model_dump()
        post_data["title"] = sanitize_string(post_data["title"])
        post_data["content"] = sanitize_string(post_data["content"])
        post_data["user_id"] = user.id
        return await self.repo.create(post_data)

    async def get_post(self, post_id: UUID) -> Post:
        post = await self.repo.get(post_id)
        if not post:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Post not found"
            )

        # Check if post is expired
        if post.is_expired():
            raise HTTPException(
                status_code=status.HTTP_410_GONE, detail="Post has expired"
            )

        return post

    async def list_posts(
        self,
        skip: int = 0,
        limit: int = 10,
        search: str = None,
        date_from: datetime = None,
        date_to: datetime = None,
    ):
        """List posts with pagination, search and date filtering"""
        statement = select(Post).where(
            Post.is_deleted.is_(False),
            or_(
                Post.expires_at.is_(None),
                Post.expires_at > datetime.utcnow(),
            ),
        )

        # Search by title or content
        if search:
            search_pattern = f"%{search}%"
            statement = statement.where(
                or_(
                    Post.title.ilike(search_pattern),
                    Post.content.ilike(search_pattern),
                )
            )

        # Date filtering
        if date_from:
            statement = statement.where(Post.created_at >= date_from)
        if date_to:
            statement = statement.where(Post.created_at <= date_to)

        # Order by created_at descending
        statement = statement.order_by(Post.created_at.desc())

        # Pagination
        statement = statement.offset(skip).limit(limit)

        result = await self.repo.db.exec(statement)
        posts = result.all()

        # Get total count
        count_statement = select(func.count(Post.id)).where(
            Post.is_deleted.is_(False),
            or_(
                Post.expires_at.is_(None),
                Post.expires_at > datetime.utcnow(),
            ),
        )
        if search:
            search_pattern = f"%{search}%"
            count_statement = count_statement.where(
                or_(
                    Post.title.ilike(search_pattern),
                    Post.content.ilike(search_pattern),
                )
            )
        if date_from:
            count_statement = count_statement.where(Post.created_at >= date_from)
        if date_to:
            count_statement = count_statement.where(Post.created_at <= date_to)

        count_result = await self.repo.db.exec(count_statement)
        total = count_result.one()

        return {"items": posts, "total": total, "skip": skip, "limit": limit}

    async def update_post(
        self, post_id: UUID, data: PostUpdateSchema, user: User
    ) -> Post:
        post = await self.get_post(post_id)
        if post.user_id != user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only update your own posts",
            )

        # Sanitize input to prevent XSS
        update_data = data.model_dump(exclude_unset=True)
        if "title" in update_data and update_data["title"]:
            update_data["title"] = sanitize_string(update_data["title"])
        if "content" in update_data and update_data["content"]:
            update_data["content"] = sanitize_string(update_data["content"])

        return await self.repo.update(post, update_data)

    async def delete_post(self, post_id: UUID, user: User):
        post = await self.get_post(post_id)
        if post.user_id != user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only delete your own posts",
            )
        await self.repo.delete(post)

    async def get_all_users_with_articles(
        self, skip: int = 0, limit: int = 10
    ) -> UserWithArticlesListResponseSchema:

        # 1️⃣ Total users count
        total_result = await self.repo.db.exec(
            select(func.count(User.id)).where(User.is_deleted.is_(False))
        )
        total = total_result.one()  # get integer directly

        # 2️⃣ Likes aggregation per post (with DISTINCT to avoid duplicates)
        # First, get distinct post_id and user_id pairs (excluding deleted likes)
        distinct_likes = (
            select(PostLike.post_id, PostLike.user_id)
            .where(PostLike.is_deleted.is_(False))
            .distinct()
            .subquery()
        )

        # Then aggregate the distinct user_ids per post
        likes_subq = (
            select(
                distinct_likes.c.post_id,
                func.coalesce(
                    func.json_agg(distinct_likes.c.user_id), func.cast("[]", JSON)
                ).label("likes"),
            )
            .group_by(distinct_likes.c.post_id)
            .subquery()
        )

        # 3️⃣ Posts aggregation per user into JSON
        articles_json = func.coalesce(
            func.json_agg(
                func.json_build_object(
                    "uuid",
                    Post.id,
                    "title",
                    Post.title,
                    "content",
                    Post.content,
                    "likes",
                    likes_subq.c.likes,
                )
            ).filter(Post.id.isnot(None)),
            func.cast("[]", JSON),
        ).label("articles")

        # 4️⃣ Main query: users + posts + likes
        query = (
            select(User.username, articles_json)
            .outerjoin(
                Post,
                and_(
                    User.id == Post.user_id,
                    Post.is_deleted.is_(False),
                ),
            )
            .outerjoin(likes_subq, likes_subq.c.post_id == Post.id)
            .where(User.is_deleted.is_(False))
            .group_by(User.id)
            .order_by(User.id)
            .offset(skip)
            .limit(limit)
        )

        result = await self.repo.db.exec(query)
        rows = result.all()

        # 5️⃣ Map to Pydantic models
        items: List[UserWithArticlesSchema] = []
        for row in rows:
            articles = row.articles or []
            # Parse if row.articles is a JSON string
            if isinstance(articles, str):
                articles = json.loads(articles)

            # Parse JSON strings if needed for each article
            parsed_articles = []
            for article in articles:
                if isinstance(article, str):
                    article = json.loads(article)
                parsed_articles.append(ArticleSchema(**article))

            items.append(
                UserWithArticlesSchema(username=row.username, articles=parsed_articles)
            )

        # 6️⃣ Return final paginated response
        return UserWithArticlesListResponseSchema(
            items=items, total=total, skip=skip, limit=limit
        )
