from datetime import datetime
from typing import List
from pydantic import BaseModel, ConfigDict, Field


class WorkspaceCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    owner_id: int


class WorkspaceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    owner_id: int
    created_at: datetime


class WorkspaceListResponse(BaseModel):
    total: int
    page: int
    page_size: int
    items: List[WorkspaceResponse]
