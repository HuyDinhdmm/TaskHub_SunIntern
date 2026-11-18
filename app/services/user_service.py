import hashlib
from fastapi import HTTPException, status
from app.models.user import User
from app.repositories.user_repository import UserRepository
from app.schemas.user import UserCreate, UserListResponse, UserResponse


class UserService:
    def __init__(self, repository: UserRepository):
        self.repository = repository

    async def create_user(self, data: UserCreate) -> User:
        existing = await self.repository.get_by_email(data.email)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered",
            )
        # Tam thoi hash bang sha256, se nang cap sang bcrypt/argon2 o Day 3 (Auth)
        hashed = hashlib.sha256(data.password.encode()).hexdigest()
        user = User(
            email=data.email,
            full_name=data.full_name,
            hashed_password=hashed,
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
