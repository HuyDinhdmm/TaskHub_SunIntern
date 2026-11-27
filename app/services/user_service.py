from typing import Optional

from fastapi import HTTPException, status

from app.core.security import hash_password, verify_password
from app.models.user import User
from app.repositories.refresh_token_repository import RefreshTokenRepository
from app.repositories.user_repository import UserRepository
from app.schemas.auth import MessageResponse
from app.schemas.user import (
    ChangePasswordRequest,
    UserCreate,
    UserListResponse,
    UserResponse,
    UserUpdateProfile,
)


class UserService:
    def __init__(
        self,
        repository: UserRepository,
        token_repository: Optional[RefreshTokenRepository] = None,
    ):
        self.repository = repository
        self.token_repository = token_repository

    async def create_user(self, data: UserCreate) -> User:
        existing = await self.repository.get_by_email(data.email)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered",
            )
        user = User(
            email=data.email,
            full_name=data.full_name,
            hashed_password=hash_password(data.password),
            role=data.role,
        )
        return await self.repository.create(user)

    async def get_user(self, user_id: int) -> User:
        user = await self.repository.get_by_id(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User with id {user_id} not found",
            )
        return user

    async def list_users(self, page: int = 1, page_size: int = 10) -> UserListResponse:
        items, total = await self.repository.get_multi(
            page=page,
            page_size=page_size,
            order_by=User.id.desc(),
        )
        return UserListResponse(
            total=total,
            page=page,
            page_size=page_size,
            items=[UserResponse.model_validate(u) for u in items],
        )

    async def update_profile(self, current_user: User, data: UserUpdateProfile) -> User:
        update_data = data.model_dump(exclude_unset=True)
        if not update_data:
            return current_user

        if "email" in update_data and update_data["email"] != current_user.email:
            existing = await self.repository.get_by_email(update_data["email"])
            if existing:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Email already registered",
                )

        return await self.repository.update(current_user, update_data)

    async def change_password(
        self,
        current_user: User,
        data: ChangePasswordRequest,
    ) -> MessageResponse:
        if not verify_password(data.current_password, current_user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Current password is incorrect",
            )

        if data.new_password == data.current_password:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="New password must be different from current password",
            )

        await self.repository.update(
            current_user,
            {"hashed_password": hash_password(data.new_password)},
        )

        # Thu hoi cac refresh token cu sau khi doi mat khau
        if self.token_repository is not None:
            await self.token_repository.revoke_all_for_user(current_user.id)

        return MessageResponse(message="Password updated successfully")
