import uuid

from datetime import datetime
from sqlmodel import SQLModel, Field


class BaseModel(SQLModel):
    id: uuid.UUID = Field(default_factory=lambda: uuid.uuid4(), primary_key=True, index=True)
    created_at: datetime = Field(default_factory=lambda: datetime.utcnow())
    updated_at: datetime = Field(default_factory=lambda: datetime.utcnow())
    is_deleted: bool = Field(default=False, nullable=False)
