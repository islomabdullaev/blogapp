from datetime import datetime, timedelta

from fastapi import HTTPException, Request, status
from passlib.context import CryptContext
from sqlmodel.ext.asyncio.session import AsyncSession

from app.auth.dependencies.jwt import JwtBearer
from app.auth.schemas.auth import UserCreate
from app.auth.services.verification import VerificationService
from app.users.models.users import User
from app.users.repositories.users import UserRepository
from core.db.redis_client import get_redis_client
from core.security.brute_force import BruteForceProtection
from core.security.sanitizer import sanitize_string

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class AuthService:
    def __init__(self, session: AsyncSession):
        self.repo = UserRepository(session)
        self.jwt_bearer = JwtBearer()
        self.verification_service = VerificationService(session)
        self.brute_force_protection = None  # Will be initialized with Redis

    async def register(self, user: UserCreate):
        # Sanitize user input to prevent XSS
        user.username = sanitize_string(user.username)
        user.email = sanitize_string(user.email)
        user.full_name = sanitize_string(user.full_name)

        existing = await self.repo.get_by_username(user.username)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already exists",
            )

        existing_email = await self.repo.get_by_email(user.email)
        if existing_email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already exists",
            )

        hashed_password = pwd_context.hash(user.password)

        user.password = hashed_password

        user_obj = await self.repo.create(user)

        print("USER CREATED")

        # Generate verification token
        verification_token = await self.verification_service.create_verification_token(
            user_obj.id
        )
        print("VERIFICATION CREATED")

        # TODO: can later add email servie part for now just used token on response
        return {
            "message": "User registered successfully. Please verify your email.",
            "verification_token": verification_token,
            "user_id": str(user_obj.id),
        }

    async def login(self, email: str, password: str, request: Request = None):
        # Initialize brute force protection if not already done
        if self.brute_force_protection is None:
            redis_client = await get_redis_client()
            self.brute_force_protection = BruteForceProtection(redis_client)

        # Sanitize email input
        email = sanitize_string(email)

        # Get client IP for brute force protection
        client_ip = request.client.host if request else "unknown"
        identifier = f"{client_ip}:{email}"

        # Check brute force protection
        await self.brute_force_protection.check_attempts(identifier)

        user = await self.repo.get_by_email(email)
        if not user or not pwd_context.verify(password, user.password):
            # Record failed attempt
            await self.brute_force_protection.record_failed_attempt(identifier)

            # Check if we should block after this attempt
            attempts_key = f"brute_force:{identifier}"
            redis_client = await get_redis_client()
            if redis_client:
                try:
                    attempts = await redis_client.get(attempts_key)
                    if (
                        attempts
                        and int(attempts)
                        >= self.brute_force_protection.max_attempts - 1
                    ):
                        await self.brute_force_protection.block_identifier(identifier)
                except Exception:
                    pass

            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials"
            )

        # Clear failed attempts on successful login
        await self.brute_force_protection.record_successful_login(identifier)

        token = await self.jwt_bearer.create_access_token({"sub": user.email})
        return {"access_token": token, "token_type": "bearer"}
