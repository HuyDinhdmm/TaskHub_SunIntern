from typing import Optional
from fastapi import HTTPException, status
from app.models.enums import ProjectStatus
from app.models.project import Project
from app.repositories.project_repository import ProjectRepository
from app.repositories.workspace_repository import WorkspaceRepository
from app.schemas.project import (
    ProjectCreate,
    ProjectListResponse,
    ProjectResponse,
    ProjectUpdate,
)


class ProjectService:
    def __init__(
        self,
        repository: ProjectRepository,
        workspace_repository: WorkspaceRepository,
    ):
        self.repository = repository
        self.workspace_repository = workspace_repository

    async def create_project(self, data: ProjectCreate) -> Project:
        workspace = await self.workspace_repository.get_by_id(data.workspace_id)
        if not workspace:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Workspace with id {data.workspace_id} not found",
            )
        project = Project(
            workspace_id=data.workspace_id,
            name=data.name,
            description=data.description,
            status=data.status,
        )
        return await self.repository.create(project)

    async def get_project(self, project_id: int) -> Project:
        project = await self.repository.get_by_id(project_id)
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Project with id {project_id} not found",
            )
        return project

    async def list_projects(
        self,
        page: int = 1,
        page_size: int = 10,
        workspace_id: Optional[int] = None,
        status: Optional[ProjectStatus] = None,
    ) -> ProjectListResponse:
        items, total = await self.repository.get_projects(
            page=page,
            page_size=page_size,
            workspace_id=workspace_id,
            status=status,
        )
        return ProjectListResponse(
            total=total,
            page=page,
            page_size=page_size,
            items=[ProjectResponse.model_validate(p) for p in items],
        )

    async def update_project(self, project_id: int, data: ProjectUpdate) -> Project:
        project = await self.get_project(project_id)
        update_data = data.model_dump(exclude_unset=True)
        return await self.repository.update(project, update_data)

    async def delete_project(self, project_id: int) -> None:
        project = await self.get_project(project_id)
        await self.repository.delete(project)
