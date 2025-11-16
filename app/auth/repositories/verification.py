from datetime import datetime
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession
from typing import Optional, List

from core.repositories.base import BaseRepository
from app.auth.models.verification import EmailVerification


class VerificationRepository(BaseRepository[EmailVerification]):
    def __init__(self, db: AsyncSession):
        super().__init__(EmailVerification, db)

    async def get_by_token(self, token: str) -> Optional[EmailVerification]:
        statement = select(EmailVerification).where(
            EmailVerification.token == token,
            EmailVerification.is_deleted == False,
        )
        result = await self.db.exec(statement)
        return result.first()

    async def get_by_user_id(self, user_id: str) -> Optional[EmailVerification]:
        statement = select(EmailVerification).where(
            EmailVerification.user_id == user_id,
            EmailVerification.is_deleted == False,
        )
        result = await self.db.exec(statement)
        return result.first()

    async def get_expired_unverified(self) -> List[EmailVerification]:
        """Get expired unverified email verifications"""
        now = datetime.utcnow()
        statement = (
            select(EmailVerification)
            .where(
                EmailVerification.is_verified == False,
                EmailVerification.expires_at < now,
                EmailVerification.is_deleted == False,
            )
        )
        result = await self.db.exec(statement)
        return result.all()

