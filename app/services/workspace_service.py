from fastapi import HTTPException, status
from app.models.workspace import Workspace
from app.repositories.user_repository import UserRepository
from app.repositories.workspace_repository import WorkspaceRepository
from app.schemas.workspace import WorkspaceCreate, WorkspaceListResponse, WorkspaceResponse


class WorkspaceService:
    def __init__(self, repository: WorkspaceRepository, user_repository: UserRepository):
        self.repository = repository
        self.user_repository = user_repository

    async def create_workspace(self, data: WorkspaceCreate) -> Workspace:
        owner = await self.user_repository.get_by_id(data.owner_id)
        if not owner:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Owner user with id {data.owner_id} not found",
            )
        workspace = Workspace(name=data.name, owner_id=data.owner_id)
        return await self.repository.create(workspace)

    async def get_workspace(self, workspace_id: int) -> Workspace:
        workspace = await self.repository.get_by_id(workspace_id)
        if not workspace:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Workspace with id {workspace_id} not found",
            )
        return workspace

    async def list_workspaces(self, page: int = 1, page_size: int = 10) -> WorkspaceListResponse:
        items, total = await self.repository.get_multi(
            page=page,
            page_size=page_size,
            order_by=Workspace.id.desc(),
        )
        return WorkspaceListResponse(
            total=total,
            page=page,
            page_size=page_size,
            items=[WorkspaceResponse.model_validate(w) for w in items],
        )
