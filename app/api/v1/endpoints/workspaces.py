from typing import Optional
from fastapi import APIRouter, Depends, Query, status
from app.api.deps import get_current_user, get_workspace_service
from app.models.user import User
from app.schemas.project import ProjectCreate, ProjectResponse
from app.schemas.workspace import (
    WorkspaceCreate,
    WorkspaceListResponse,
    WorkspaceMemberAdd,
    WorkspaceMemberResponse,
    WorkspaceMemberUpdate,
    WorkspaceResponse,
    WorkspaceUpdate,
)
from app.services.project_service import ProjectService
from app.services.workspace_service import WorkspaceService
from app.api.deps import get_project_service

router = APIRouter(prefix="/workspaces", tags=["workspaces"])


@router.post("", response_model=WorkspaceResponse, status_code=status.HTTP_201_CREATED)
async def create_workspace(
    workspace_in: WorkspaceCreate,
    current_user: User = Depends(get_current_user),
    workspace_service: WorkspaceService = Depends(get_workspace_service),
):
    return await workspace_service.create_workspace(workspace_in, current_user)


@router.get("", response_model=WorkspaceListResponse)
async def list_workspaces(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=10, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    workspace_service: WorkspaceService = Depends(get_workspace_service),
):
    return await workspace_service.list_my_workspaces(current_user, page=page, page_size=page_size)


@router.get("/{workspace_id}", response_model=WorkspaceResponse)
async def get_workspace(
    workspace_id: int,
    current_user: User = Depends(get_current_user),
    workspace_service: WorkspaceService = Depends(get_workspace_service),
):
    return await workspace_service.get_workspace(workspace_id, current_user)


@router.put("/{workspace_id}", response_model=WorkspaceResponse)
async def update_workspace(
    workspace_id: int,
    workspace_in: WorkspaceUpdate,
    current_user: User = Depends(get_current_user),
    workspace_service: WorkspaceService = Depends(get_workspace_service),
):
    return await workspace_service.update_workspace(workspace_id, workspace_in, current_user)


@router.delete("/{workspace_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_workspace(
    workspace_id: int,
    current_user: User = Depends(get_current_user),
    workspace_service: WorkspaceService = Depends(get_workspace_service),
):
    await workspace_service.delete_workspace(workspace_id, current_user)


@router.post("/{workspace_id}/members", response_model=WorkspaceMemberResponse, status_code=status.HTTP_201_CREATED)
async def add_workspace_member(
    workspace_id: int,
    payload: WorkspaceMemberAdd,
    current_user: User = Depends(get_current_user),
    workspace_service: WorkspaceService = Depends(get_workspace_service),
):
    return await workspace_service.add_member(workspace_id, payload, current_user)


@router.delete("/{workspace_id}/members/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_workspace_member(
    workspace_id: int,
    user_id: int,
    current_user: User = Depends(get_current_user),
    workspace_service: WorkspaceService = Depends(get_workspace_service),
):
    await workspace_service.remove_member(workspace_id, user_id, current_user)


@router.patch("/{workspace_id}/members/{user_id}", response_model=WorkspaceMemberResponse)
async def update_member_role(
    workspace_id: int,
    user_id: int,
    payload: WorkspaceMemberUpdate,
    current_user: User = Depends(get_current_user),
    workspace_service: WorkspaceService = Depends(get_workspace_service),
):
    return await workspace_service.update_member_role(workspace_id, user_id, payload, current_user)


# POST /api/v1/workspaces/{id}/projects (tao project trong workspace)
@router.post("/{workspace_id}/projects", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
async def create_workspace_project(
    workspace_id: int,
    project_in: ProjectCreate,
    current_user: User = Depends(get_current_user),
    project_service: ProjectService = Depends(get_project_service),
):
    return await project_service.create_project_in_workspace(workspace_id, project_in, current_user)
