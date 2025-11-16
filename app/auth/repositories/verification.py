from datetime import datetime
from typing import List, Optional

from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.auth.models.verification import EmailVerification
from core.repositories.base import BaseRepository


class VerificationRepository(BaseRepository[EmailVerification]):
    def __init__(self, db: AsyncSession):
        super().__init__(EmailVerification, db)

    async def get_by_token(self, token: str) -> Optional[EmailVerification]:
        statement = select(EmailVerification).where(
            EmailVerification.token == token,
            EmailVerification.is_deleted.is_(False),
        )
        result = await self.db.exec(statement)
        return result.first()

    async def get_by_user_id(self, user_id: str) -> Optional[EmailVerification]:
        statement = select(EmailVerification).where(
            EmailVerification.user_id == user_id,
            EmailVerification.is_deleted.is_(False),
        )
        result = await self.db.exec(statement)
        return result.first()

    async def get_expired_unverified(self) -> List[EmailVerification]:
        """Get expired unverified email verifications"""
        now = datetime.utcnow()
        statement = select(EmailVerification).where(
            EmailVerification.is_verified.is_(False),
            EmailVerification.expires_at < now,
            EmailVerification.is_deleted.is_(False),
        )
        result = await self.db.exec(statement)
        return result.all()
