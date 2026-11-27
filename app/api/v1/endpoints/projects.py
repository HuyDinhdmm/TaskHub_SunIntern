from typing import Optional

from fastapi import APIRouter, Depends, Query, status

from app.api.deps import get_current_user, get_project_service
from app.models.enums import ProjectStatus
from app.models.user import User
from app.schemas.project import ProjectListResponse, ProjectResponse, ProjectUpdate
from app.services.project_service import ProjectService

router = APIRouter(prefix="/projects", tags=["projects"])


@router.get("/{project_id}", response_model=ProjectResponse)
async def get_project(
    project_id: int,
    current_user: User = Depends(get_current_user),
    project_service: ProjectService = Depends(get_project_service),
):
    return await project_service.get_project(project_id, current_user)


@router.get("", response_model=ProjectListResponse)
async def list_projects(
    workspace_id: int = Query(...),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=10, ge=1, le=100),
    status: Optional[ProjectStatus] = None,
    current_user: User = Depends(get_current_user),
    project_service: ProjectService = Depends(get_project_service),
):
    return await project_service.list_workspace_projects(
        workspace_id=workspace_id,
        current_user=current_user,
        page=page,
        page_size=page_size,
        status_filter=status,
    )


@router.patch("/{project_id}", response_model=ProjectResponse)
async def update_project(
    project_id: int,
    project_in: ProjectUpdate,
    current_user: User = Depends(get_current_user),
    project_service: ProjectService = Depends(get_project_service),
):
    return await project_service.update_project(project_id, project_in, current_user)


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_project(
    project_id: int,
    current_user: User = Depends(get_current_user),
    project_service: ProjectService = Depends(get_project_service),
):
    await project_service.delete_project(project_id, current_user)
