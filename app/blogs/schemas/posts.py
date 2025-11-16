from datetime import datetime
from typing import List
from uuid import UUID

from pydantic import BaseModel


class PostCreateSchema(BaseModel):
    title: str
    content: str


class PostUpdateSchema(BaseModel):
    title: str | None = None
    content: str | None = None


class PostResponseSchema(BaseModel):
    id: UUID
    user_id: UUID
    title: str
    content: str
    created_at: datetime

    class Config:
        from_attributes = True


class PostListResponseSchema(BaseModel):
    items: List[PostResponseSchema]
    total: int
    skip: int
    limit: int


class ArticleSchema(BaseModel):
    uuid: UUID
    title: str | None = None
    content: str | None = None
    likes: List[UUID] | None = None

    class Config:
        from_attributes = True


class UserWithArticlesSchema(BaseModel):
    username: str
    articles: List[ArticleSchema]

    class Config:
        from_attributes = True


class UserWithArticlesListResponseSchema(BaseModel):
    items: List[UserWithArticlesSchema]
    total: int
    skip: int
    limit: int


class PostLikeSchema(BaseModel):
    user_id: UUID
    post_id: UUID
