from datetime import datetime
from typing import List

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import WorkspaceRole


class WorkspaceCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)


class WorkspaceUpdate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)


class WorkspaceMemberAdd(BaseModel):
    user_id: int
    role: WorkspaceRole = WorkspaceRole.VIEWER


class WorkspaceMemberUpdate(BaseModel):
    role: WorkspaceRole


class WorkspaceMemberResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    workspace_id: int
    user_id: int
    role: WorkspaceRole


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
