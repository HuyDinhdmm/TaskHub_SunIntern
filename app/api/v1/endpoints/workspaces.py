from fastapi import APIRouter, Depends, Query, status
from app.api.deps import get_workspace_service
from app.schemas.workspace import WorkspaceCreate, WorkspaceListResponse, WorkspaceResponse
from app.services.workspace_service import WorkspaceService

router = APIRouter(prefix="/workspaces", tags=["workspaces"])


@router.post("", response_model=WorkspaceResponse, status_code=status.HTTP_201_CREATED)
async def create_workspace(
    workspace_in: WorkspaceCreate,
    workspace_service: WorkspaceService = Depends(get_workspace_service),
):
    return await workspace_service.create_workspace(workspace_in)


@router.get("", response_model=WorkspaceListResponse)
async def get_workspaces(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=10, ge=1, le=100),
    workspace_service: WorkspaceService = Depends(get_workspace_service),
):
    return await workspace_service.list_workspaces(page=page, page_size=page_size)


@router.get("/{workspace_id}", response_model=WorkspaceResponse)
async def get_workspace(
    workspace_id: int,
    workspace_service: WorkspaceService = Depends(get_workspace_service),
):
    return await workspace_service.get_workspace(workspace_id)
