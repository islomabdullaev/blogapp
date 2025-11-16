from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies.jwt import JwtBearer
from app.users.models.users import User
from app.users.schemas.users import UserResponse, UserUpdate
from app.users.services.v1.users import UserService
from core.db.session import get_session

router = APIRouter(tags=["users"])

jwt_bearer = JwtBearer()


def get_user_service(session: AsyncSession = Depends(get_session)) -> UserService:
    return UserService(session)


@router.get("/me", response_model=UserResponse)
async def get_current_user(current_user: User = Depends(jwt_bearer.get_current_user)):
    """Get current authenticated user"""
    return current_user


@router.put("/me", response_model=UserResponse)
async def update_current_user(
    user_data: UserUpdate,
    current_user: User = Depends(jwt_bearer.get_current_user),
    service: UserService = Depends(get_user_service),
):
    """Update current authenticated user"""
    return await service.update_user(current_user, user_data)
