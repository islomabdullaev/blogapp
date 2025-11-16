from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, EmailStr


class UserResponse(BaseModel):
    id: UUID
    email: EmailStr
    full_name: str
    username: str
    is_verified: bool
    created_at: datetime
    updated_at: datetime | None

    class Config:
        from_attributes = True


class UserUpdate(BaseModel):
    email: EmailStr | None = None
    full_name: str | None = None
    username: str | None = None
