import re
from typing import List, Optional, TYPE_CHECKING

# sqlmodel
from sqlmodel import Field, Relationship

# models
from core.models.base import BaseModel

if TYPE_CHECKING:
    from app.blogs.models.posts import Post, Comment, PostLike
    from app.auth.models.verification import EmailVerification

# pydantic
from pydantic import EmailStr, validator


class User(BaseModel, table=True):
    __tablename__ = "users"

    email: EmailStr = Field(..., unique=True)
    full_name: str = Field(..., min_length=1, max_length=100)
    username: str = Field(..., min_length=6, max_length=1000)
    password: str

    posts: List["Post"] = Relationship(back_populates="user")
    comments: List["Comment"] = Relationship(back_populates="user")
    likes: List["PostLike"] = Relationship(back_populates="user")
    verification: Optional["EmailVerification"] = Relationship(
        back_populates="user", sa_relationship_kwargs={"uselist": False}
    )

    @property
    def is_verified(self) -> bool:
        """Check if user email is verified"""
        return self.verification is not None and self.verification.is_verified

    @validator("full_name")
    def validate_full_name(cls, v):
        pattern = r"^[a-zа-яё\s]+$"
        if not re.fullmatch(pattern, v):
            raise ValueError(
                "Полное имя должно содержать только буквы латиницы/кириллицы и в нижнем регистре"
            )
        return v