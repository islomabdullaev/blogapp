from fastapi import APIRouter, Depends, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.schemas.auth import LoginRequest, TokenResponse, UserCreate
from app.auth.services.auth import AuthService
from app.auth.services.verification import VerificationService
from core.db.session import get_session

router = APIRouter(tags=["auth"])


def get_auth_service(session: AsyncSession = Depends(get_session)) -> AuthService:
    return AuthService(session)


def get_verification_service(
    session: AsyncSession = Depends(get_session),
) -> VerificationService:
    return VerificationService(session)


@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register(
    user_data: UserCreate, service: AuthService = Depends(get_auth_service)
):
    return await service.register(user=user_data)


@router.post("/login", response_model=TokenResponse)
async def login(
    credentials: LoginRequest,
    request: Request,
    service: AuthService = Depends(get_auth_service),
):
    return await service.login(
        email=credentials.email, password=credentials.password, request=request
    )


@router.post("/verify-email/{token}", status_code=status.HTTP_200_OK)
async def verify_email(
    token: str,
    verification_service: VerificationService = Depends(get_verification_service),
):
    await verification_service.verify_email(token=token)
    return {"message": "Email verified successfully"}
