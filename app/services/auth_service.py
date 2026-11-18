from datetime import datetime, timezone
import jwt
from fastapi import HTTPException, status
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)
from app.models.enums import UserRole
from app.models.refresh_token import RefreshToken
from app.models.user import User
from app.repositories.refresh_token_repository import RefreshTokenRepository
from app.repositories.user_repository import UserRepository
from app.schemas.auth import (
    LoginRequest,
    MessageResponse,
    RefreshTokenRequest,
    RegisterRequest,
    TokenResponse,
)


class AuthService:
    def __init__(
        self,
        user_repository: UserRepository,
        token_repository: RefreshTokenRepository,
    ):
        self.user_repository = user_repository
        self.token_repository = token_repository

    async def register(self, data: RegisterRequest) -> User:
        existing = await self.user_repository.get_by_email(data.email)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered",
            )

        user = User(
            email=data.email,
            full_name=data.full_name,
            hashed_password=hash_password(data.password),
            role=UserRole.MEMBER,
        )
        return await self.user_repository.create(user)

    async def login(self, data: LoginRequest) -> TokenResponse:
        user = await self.user_repository.get_by_email(data.email)
        if not user or not verify_password(data.password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password",
            )

        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User account is inactive",
            )

        return await self._issue_tokens(user)

    async def refresh_token(self, data: RefreshTokenRequest) -> TokenResponse:
        payload = self._decode_refresh_payload(data.refresh_token)
        jti = payload.get("jti")
        user_id = int(payload["sub"])

        stored_token = await self.token_repository.get_by_jti(jti)
        if not stored_token or stored_token.is_revoked:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Refresh token is invalid or revoked",
            )

        expires_at = stored_token.expires_at
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=timezone.utc)
        if expires_at < datetime.now(timezone.utc):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Refresh token has expired",
            )

        user = await self.user_repository.get_by_id(user_id)
        if not user or not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found or inactive",
            )

        # Thu hoi refresh token cu va cap cap token moi (token rotation)
        await self.token_repository.revoke(stored_token)
        return await self._issue_tokens(user)

    async def logout(self, data: RefreshTokenRequest) -> MessageResponse:
        payload = self._decode_refresh_payload(data.refresh_token)
        jti = payload.get("jti")

        stored_token = await self.token_repository.get_by_jti(jti)
        if not stored_token or stored_token.is_revoked:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Refresh token is invalid or already revoked",
            )

        await self.token_repository.revoke(stored_token)
        return MessageResponse(message="Logged out successfully")

    def _decode_refresh_payload(self, token: str) -> dict:
        try:
            payload = decode_token(token)
        except jwt.PyJWTError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired refresh token",
            )

        if payload.get("type") != "refresh" or not payload.get("jti") or not payload.get("sub"):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token type",
            )
        return payload

    async def _issue_tokens(self, user: User) -> TokenResponse:
        access_token = create_access_token(user_id=user.id, role=user.role.value)
        refresh_token, jti, expires_at = create_refresh_token(user_id=user.id)

        token_obj = RefreshToken(
            user_id=user.id,
            jti=jti,
            expires_at=expires_at,
        )
        await self.token_repository.create(token_obj)

        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
        )
