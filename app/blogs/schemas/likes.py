from uuid import UUID

from pydantic import BaseModel


class PostLikeResponseSchema(BaseModel):
    user_id: UUID
    post_id: UUID

    class Config:
        from_attributes = True
