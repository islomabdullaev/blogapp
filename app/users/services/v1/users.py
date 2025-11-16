from uuid import UUID
from sqlmodel.ext.asyncio.session import AsyncSession
from fastapi import HTTPException, status

from app.users.repositories.users import UserRepository
from app.users.models.users import User
from app.users.schemas.users import UserUpdate


class UserService:
    def __init__(self, db: AsyncSession):
        self.repo = UserRepository(db)

    async def get_user(self, user_id: UUID) -> User:
        user = await self.repo.get(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        return user

    async def update_user(self, user: User, user_data: UserUpdate) -> User:
        update_data = user_data.model_dump(exclude_unset=True)
        
        # Check if username is being changed and if it's already taken
        if "username" in update_data:
            existing = await self.repo.get_by_username(update_data["username"])
            if existing and existing.id != user.id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Username already exists"
                )
        
        # Check if email is being changed and if it's already taken
        if "email" in update_data:
            existing = await self.repo.get_by_email(update_data["email"])
            if existing and existing.id != user.id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Email already exists"
                )
        
        return await self.repo.update(user, update_data)

