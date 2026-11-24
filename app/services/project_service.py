from typing import Optional
from fastapi import HTTPException, status
from app.core.permissions import AccessControl
from app.models.enums import ProjectStatus, WorkspaceRole
from app.models.project import Project
from app.models.user import User
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
        access_control: AccessControl,
    ):
        self.repository = repository
        self.workspace_repository = workspace_repository
        self.access_control = access_control

    async def create_project_in_workspace(
        self,
        workspace_id: int,
        data: ProjectCreate,
        current_user: User,
    ) -> Project:
        # OWNER va EDITOR duoc tao project
        await self.access_control.check_workspace_role(
            workspace_id=workspace_id,
            user=current_user,
            allowed_roles=[WorkspaceRole.OWNER, WorkspaceRole.EDITOR],
        )

        project = Project(
            workspace_id=workspace_id,
            name=data.name,
            description=data.description,
            status=data.status,
        )
        return await self.repository.create(project)

    async def get_project(self, project_id: int, current_user: User) -> Project:
        project = await self.repository.get_by_id(project_id)
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Project with id {project_id} not found",
            )

        await self.access_control.check_workspace_role(
            workspace_id=project.workspace_id,
            user=current_user,
            allowed_roles=[WorkspaceRole.OWNER, WorkspaceRole.EDITOR, WorkspaceRole.VIEWER],
        )
        return project

    async def list_workspace_projects(
        self,
        workspace_id: int,
        current_user: User,
        page: int = 1,
        page_size: int = 10,
        status_filter: Optional[ProjectStatus] = None,
    ) -> ProjectListResponse:
        await self.access_control.check_workspace_role(
            workspace_id=workspace_id,
            user=current_user,
            allowed_roles=[WorkspaceRole.OWNER, WorkspaceRole.EDITOR, WorkspaceRole.VIEWER],
        )

        items, total = await self.repository.get_projects(
            page=page,
            page_size=page_size,
            workspace_id=workspace_id,
            status=status_filter,
        )
        return ProjectListResponse(
            total=total,
            page=page,
            page_size=page_size,
            items=[ProjectResponse.model_validate(p) for p in items],
        )

    async def update_project(
        self,
        project_id: int,
        data: ProjectUpdate,
        current_user: User,
    ) -> Project:
        project = await self.repository.get_by_id(project_id)
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Project with id {project_id} not found",
            )

        # OWNER va EDITOR duoc sua / archive project
        await self.access_control.check_workspace_role(
            workspace_id=project.workspace_id,
            user=current_user,
            allowed_roles=[WorkspaceRole.OWNER, WorkspaceRole.EDITOR],
        )

        update_data = data.model_dump(exclude_unset=True)
        return await self.repository.update(project, update_data)

    async def delete_project(self, project_id: int, current_user: User) -> None:
        project = await self.repository.get_by_id(project_id)
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Project with id {project_id} not found",
            )

        # Chi OWNER moi duoc xoa project
        await self.access_control.check_workspace_role(
            workspace_id=project.workspace_id,
            user=current_user,
            allowed_roles=[WorkspaceRole.OWNER],
        )
        await self.repository.delete(project)
