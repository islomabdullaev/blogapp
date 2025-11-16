import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlmodel import Field, Relationship

from core.models.base import BaseModel

if TYPE_CHECKING:
    from app.users.models.users import User


class EmailVerification(BaseModel, table=True):
    __tablename__ = "email_verification"

    user_id: uuid.UUID = Field(
        foreign_key="users.id", unique=True, nullable=False, index=True
    )
    token: str = Field(..., unique=True, index=True)
    expires_at: datetime = Field(default_factory=lambda: datetime.utcnow())
    is_verified: bool = Field(default=False, nullable=False)

    user: "User" = Relationship(back_populates="verification")

    def is_expired(self) -> bool:
        """Check if verification token has expired"""
        return datetime.utcnow() > self.expires_at

