from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class CommentCreateSchema(BaseModel):
    text: str = Field(..., max_length=5000)


class CommentResponseSchema(BaseModel):
    id: UUID
    post_id: UUID
    user_id: UUID
    text: str
    created_at: datetime
    updated_at: datetime | None

    class Config:
        from_attributes = True
