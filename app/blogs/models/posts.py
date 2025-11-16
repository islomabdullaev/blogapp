import re
import uuid
from datetime import datetime
from typing import TYPE_CHECKING, List, Optional

from pydantic import field_validator
from sqlmodel import Field, Relationship

# models
from core.models.base import BaseModel

if TYPE_CHECKING:
    from app.users.models.users import User


class Post(BaseModel, table=True):
    __tablename__ = "post"

    user_id: uuid.UUID = Field(foreign_key="users.id")
    user: "User" = Relationship(back_populates="posts")

    title: str = Field(..., min_length=6, max_length=1000)
    content: str = Field(..., max_length=10_000)
    expires_at: Optional[datetime] = Field(default=None, nullable=True)

    comments: List["Comment"] = Relationship(back_populates="post")
    likes: List["PostLike"] = Relationship(back_populates="post")

    def is_expired(self) -> bool:
        """Check if post has expired"""
        if not self.expires_at:
            return False
        return datetime.utcnow() > self.expires_at

    @field_validator("title")
    @classmethod
    def validate_title(cls, v):
        # Only letters (latin/cyrillic) and spaces
        pattern = r"^[a-zа-яёA-ZА-ЯЁ0-9\s]+$"
        if not re.fullmatch(pattern, v):
            raise ValueError(
                "Title должен содержать только буквы латиницы/кириллицы, цифры и пробелы"
            )
        if not (5 < len(v) < 1000):
            raise ValueError("Title должен быть больше 5 и меньше 1000 символов")
        return v

    @field_validator("content")
    @classmethod
    def validate_content(cls, v):
        if len(v) > 10_000:
            raise ValueError("Content должен быть меньше 10_000 символов")
        return v


class PostLike(BaseModel, table=True):
    __tablename__ = "postlike"

    user_id: uuid.UUID = Field(foreign_key="users.id", primary_key=True)
    post_id: uuid.UUID = Field(foreign_key="post.id", primary_key=True)

    post: "Post" = Relationship(back_populates="likes")
    user: "User" = Relationship(back_populates="likes")


class Comment(BaseModel, table=True):
    __tablename__ = "comment"

    post_id: uuid.UUID = Field(foreign_key="post.id", nullable=False)
    user_id: uuid.UUID = Field(foreign_key="users.id", nullable=False)

    text: str = Field(max_length=5000, nullable=False)
    # Relationships (optional)
    post: "Post" = Relationship(back_populates="comments")
    user: "User" = Relationship(back_populates="comments")
