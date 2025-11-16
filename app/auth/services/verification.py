import secrets
from datetime import datetime, timedelta
from uuid import UUID

from fastapi import HTTPException, status
from sqlmodel.ext.asyncio.session import AsyncSession

from app.auth.repositories.verification import VerificationRepository
from app.auth.schemas.auth import EmailVerificationSchema


class VerificationService:
    """Service for email verification"""

    VERIFICATION_TOKEN_EXPIRE_DAYS = 31

    def __init__(self, session: AsyncSession):
        self.repo = VerificationRepository(session)
        self.db = session

    def generate_verification_token(self) -> str:
        return secrets.token_urlsafe(32)

    async def create_verification_token(self, user_id: UUID) -> str:
        token = self.generate_verification_token()
        print("TOKEN GENERATED: ", token)
        expires_at = datetime.utcnow() + timedelta(
            days=self.VERIFICATION_TOKEN_EXPIRE_DAYS
        )
        print(expires_at, "EXPIREEEEEEEED")

        # Check if verification already exists
        existing = await self.repo.get_by_user_id(user_id)
        if existing:
            # Update existing verification
            existing.token = token
            existing.expires_at = expires_at
            existing.is_verified = False
            await self.db.commit()
            await self.db.refresh(existing)
            return token

        # Create new verification
        verification = EmailVerificationSchema(
            user_id=user_id, token=token, expires_at=expires_at
        )
        await self.repo.create(verification)

        return token

    async def verify_email(self, token: str) -> bool:
        """Verify user email by token"""
        verification = await self.repo.get_by_token(token)
        if not verification:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Invalid verification token",
            )

        if verification.is_verified:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already verified",
            )

        if verification.is_expired():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Verification token has expired",
            )

        verification.is_verified = True
        await self.db.commit()
        await self.db.refresh(verification)

        return True
