from datetime import datetime
from typing import List, Optional

from sqlalchemy.orm import selectinload
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.users.models.users import User
from core.repositories.base import BaseRepository


class UserRepository(BaseRepository[User]):
    def __init__(self, db: AsyncSession):
        super().__init__(User, db)

    async def get_by_username(self, username: str) -> Optional[User]:
        statement = select(User).where(
            User.username == username, User.is_deleted == False
        )
        result = await self.db.exec(statement)
        return result.first()

    async def get_by_email(self, email: str) -> Optional[User]:
        statement = (
            select(User)
            .options(selectinload(User.verification))
            .where(User.email == email, User.is_deleted == False)
        )
        result = await self.db.exec(statement)
        return result.first()

    async def get_users_by_user_ids(self, user_ids: List[str]) -> List[User]:
        """Get users by user IDs"""
        import uuid

        uuid_list = [uuid.UUID(uid) for uid in user_ids]
        statement = select(User).where(User.id.in_(uuid_list), User.is_deleted == False)
        result = await self.db.exec(statement)
        return result.all()
