from fastapi import APIRouter, Depends, Query, status
from app.api.deps import get_current_user, get_user_service
from app.models.user import User
from app.schemas.auth import MessageResponse
from app.schemas.user import (
    ChangePasswordRequest,
    UserCreate,
    UserListResponse,
    UserResponse,
    UserUpdateProfile,
)
from app.services.user_service import UserService

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me", response_model=UserResponse)
async def get_my_profile(current_user: User = Depends(get_current_user)):
    return current_user


@router.patch("/me", response_model=UserResponse)
async def update_my_profile(
    payload: UserUpdateProfile,
    current_user: User = Depends(get_current_user),
    user_service: UserService = Depends(get_user_service),
):
    return await user_service.update_profile(current_user, payload)


@router.patch("/me/password", response_model=MessageResponse)
async def change_my_password(
    payload: ChangePasswordRequest,
    current_user: User = Depends(get_current_user),
    user_service: UserService = Depends(get_user_service),
):
    return await user_service.change_password(current_user, payload)


@router.post("", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(
    user_in: UserCreate,
    user_service: UserService = Depends(get_user_service),
):
    return await user_service.create_user(user_in)


@router.get("", response_model=UserListResponse)
async def get_users(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=10, ge=1, le=100),
    user_service: UserService = Depends(get_user_service),
):
    return await user_service.list_users(page=page, page_size=page_size)


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: int,
    user_service: UserService = Depends(get_user_service),
):
    return await user_service.get_user(user_id)
