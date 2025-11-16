from datetime import datetime
from uuid import UUID
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from core.db.session import get_session
from app.auth.dependencies.jwt import JwtBearer
from app.users.models.users import User
from app.blogs.services.v1.posts import PostService
from app.blogs.services.v1.comments import CommentService
from app.blogs.services.v1.likes import PostLikeService
from app.blogs.schemas.posts import (
    PostCreateSchema,
    PostListResponseSchema,
    PostUpdateSchema,
    PostResponseSchema,
    UserWithArticlesSchema,
    UserWithArticlesListResponseSchema,
)
from app.blogs.schemas.comments import CommentCreateSchema, CommentResponseSchema

router = APIRouter(tags=["blogs"])

jwt_bearer = JwtBearer()


def get_post_service(session: AsyncSession = Depends(get_session)) -> PostService:
    return PostService(session)


def get_comment_service(session: AsyncSession = Depends(get_session)) -> CommentService:
    return CommentService(session)


def get_like_service(session: AsyncSession = Depends(get_session)) -> PostLikeService:
    return PostLikeService(session)


@router.get("/", response_model=PostListResponseSchema)
async def posts(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    search: str = Query(None),
    date_from: datetime = Query(None),
    date_to: datetime = Query(None),
    service: PostService = Depends(get_post_service),
):
    return await service.list_posts(skip=skip, limit=limit, search=search, date_from=date_from, date_to=date_to)


@router.post("/", response_model=PostResponseSchema)
async def create_post(
    data: PostCreateSchema,
    current_user: User = Depends(jwt_bearer.get_current_user),
    service: PostService = Depends(get_post_service)
):
    return await service.create_post(data=data, user=current_user)


@router.get("/all", response_model=UserWithArticlesListResponseSchema)
async def get_all_users_with_articles(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    service: PostService = Depends(get_post_service)
):
    return await service.get_all_users_with_articles(skip=skip, limit=limit)


@router.get("/{post_id}", response_model=PostResponseSchema)
async def get_post(
    post_id: UUID,
    service: PostService = Depends(get_post_service)
):
    return await service.get_post(post_id=post_id)


@router.put("/{post_id}", response_model=PostResponseSchema)
async def update_post(
    post_id: UUID,
    data: PostUpdateSchema,
    current_user: User = Depends(jwt_bearer.get_current_user),
    service: PostService = Depends(get_post_service)
):
    return await service.update_post(post_id=post_id, data=data, user=current_user)


@router.delete("/{post_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_post(
    post_id: UUID,
    current_user: User = Depends(jwt_bearer.get_current_user),
    service: PostService = Depends(get_post_service)
):
    await service.delete_post(post_id=post_id, user=current_user)


# Comment endpoints
@router.post("/{post_id}/comments", response_model=CommentResponseSchema)
async def create_comment(
    post_id: UUID,
    data: CommentCreateSchema,
    current_user: User = Depends(jwt_bearer.get_current_user),
    service: CommentService = Depends(get_comment_service)
):
    return await service.create_comment(post_id=post_id, data=data, user=current_user)


@router.get("/{post_id}/comments", response_model=list[CommentResponseSchema])
async def get_comments(
    post_id: UUID,
    service: CommentService = Depends(get_comment_service)
):
    return await service.get_comments_by_post(post_id)


@router.delete("/{post_id}/comments", status_code=status.HTTP_200_OK)
async def delete_all_comments(
    post_id: UUID,
    current_user: User = Depends(jwt_bearer.get_current_user),
    service: CommentService = Depends(get_comment_service),
):
    return await service.delete_all_comments_by_post(post_id=post_id, user=current_user)


@router.delete("/{post_id}/comments/{comment_id}")
async def delete_comment(
    post_id: UUID,
    comment_id: UUID,
    current_user: User = Depends(jwt_bearer.get_current_user),
    service: CommentService = Depends(get_comment_service),
):
    await service.delete_comment(post_id=post_id, comment_id=comment_id, user=current_user)


# Like endpoints
@router.post("/{post_id}/like")
async def toggle_like(
    post_id: UUID,
    current_user: User = Depends(jwt_bearer.get_current_user),
    service: PostLikeService = Depends(get_like_service)
):
    return await service.toggle_like(post_id=post_id, user=current_user)


@router.get("/{post_id}/like")
async def check_like(
    post_id: UUID,
    current_user: User = Depends(jwt_bearer.get_current_user),
    service: PostLikeService = Depends(get_like_service)
):
    liked = await service.check_like(post_id=post_id, user=current_user)
    return {"liked": liked}
