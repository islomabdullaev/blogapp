from datetime import datetime, timedelta

from fastapi import Depends, HTTPException, status

# fastapi
from fastapi.security import HTTPAuthorizationCredentials, OAuth2PasswordBearer
from fastapi.security.http import HTTPBearer

# jwt
from jose import JWTError, jwt
from sqlalchemy.ext.asyncio import AsyncSession

from app.users.repositories.users import UserRepository

# app
from core.db.session import get_session
from core.settings import Settings

settings = Settings()


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


class JwtBearer:

    def __init__(self):
        self.ACCESS_TOKEN_EXPIRE_MINUTES = settings.jwt.access_token_expire_minutes
        self.SECRET_KEY = settings.jwt.secret_key
        self.ALGORITHM = settings.jwt.algorithm

    async def create_access_token(self, data: dict):
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(minutes=self.ACCESS_TOKEN_EXPIRE_MINUTES)
        to_encode.update({"exp": expire})
        return jwt.encode(to_encode, self.SECRET_KEY, algorithm=self.ALGORITHM)

    async def decode_access_token(self, token: str):
        try:
            payload = jwt.decode(token, self.SECRET_KEY, algorithms=[self.ALGORITHM])
            return payload
        except JWTError:
            return None

    async def get_current_user(
        self,
        token: HTTPAuthorizationCredentials = Depends(HTTPBearer()),
        session: AsyncSession = Depends(get_session),
    ):
        payload = await self.decode_access_token(token.credentials)
        if not payload or "sub" not in payload:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )

        email = payload["sub"]
        user = await UserRepository(session).get_by_email(email)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
            )
        return user
