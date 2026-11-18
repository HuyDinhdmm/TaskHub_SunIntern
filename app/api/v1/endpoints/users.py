from fastapi import APIRouter, Depends, Query, status
from app.api.deps import get_user_service
from app.schemas.user import UserCreate, UserListResponse, UserResponse
from app.services.user_service import UserService

router = APIRouter(prefix="/users", tags=["users"])


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
