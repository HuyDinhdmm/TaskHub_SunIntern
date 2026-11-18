from datetime import datetime
from typing import List
from pydantic import BaseModel, ConfigDict, Field
from app.models.enums import UserRole


class UserCreate(BaseModel):
    email: str = Field(..., min_length=3, max_length=255)
    full_name: str = Field(..., min_length=1, max_length=255)
    password: str = Field(..., min_length=6, max_length=128)
    role: UserRole = UserRole.MEMBER


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: str
    full_name: str
    role: UserRole
    is_active: bool
    created_at: datetime


class UserListResponse(BaseModel):
    total: int
    page: int
    page_size: int
    items: List[UserResponse]
