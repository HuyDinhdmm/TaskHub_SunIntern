from fastapi import HTTPException, status

from app.core.permissions import AccessControl
from app.models.enums import WorkspaceRole
from app.models.user import User
from app.models.workspace import Workspace, WorkspaceMember
from app.repositories.user_repository import UserRepository
from app.repositories.workspace_member_repository import WorkspaceMemberRepository
from app.repositories.workspace_repository import WorkspaceRepository
from app.schemas.workspace import (
    WorkspaceCreate,
    WorkspaceListResponse,
    WorkspaceMemberAdd,
    WorkspaceMemberResponse,
    WorkspaceMemberUpdate,
    WorkspaceResponse,
    WorkspaceUpdate,
)


class WorkspaceService:
    def __init__(
        self,
        repository: WorkspaceRepository,
        member_repository: WorkspaceMemberRepository,
        user_repository: UserRepository,
        access_control: AccessControl,
    ):
        self.repository = repository
        self.member_repository = member_repository
        self.user_repository = user_repository
        self.access_control = access_control

    async def create_workspace(self, data: WorkspaceCreate, current_user: User) -> Workspace:
        workspace = Workspace(name=data.name, owner_id=current_user.id)
        saved = await self.repository.create(workspace)

        # Tu dong them owner vao danh sach workspace_members
        member = WorkspaceMember(
            workspace_id=saved.id,
            user_id=current_user.id,
            role=WorkspaceRole.OWNER,
        )
        await self.member_repository.create(member)
        return saved

    async def get_workspace(self, workspace_id: int, current_user: User) -> Workspace:
        await self.access_control.check_workspace_role(
            workspace_id=workspace_id,
            user=current_user,
            allowed_roles=[WorkspaceRole.OWNER, WorkspaceRole.EDITOR, WorkspaceRole.VIEWER],
        )
        workspace = await self.repository.get_by_id(workspace_id)
        if not workspace:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Workspace with id {workspace_id} not found",
            )
        return workspace

    async def list_my_workspaces(
        self,
        current_user: User,
        page: int = 1,
        page_size: int = 10,
    ) -> WorkspaceListResponse:
        items, total = await self.repository.get_user_workspaces(
            user_id=current_user.id,
            page=page,
            page_size=page_size,
        )
        return WorkspaceListResponse(
            total=total,
            page=page,
            page_size=page_size,
            items=[WorkspaceResponse.model_validate(w) for w in items],
        )

    async def update_workspace(
        self,
        workspace_id: int,
        data: WorkspaceUpdate,
        current_user: User,
    ) -> Workspace:
        # Chi OWNER moi duoc sua workspace
        await self.access_control.check_workspace_role(
            workspace_id=workspace_id,
            user=current_user,
            allowed_roles=[WorkspaceRole.OWNER],
        )
        workspace = await self.repository.get_by_id(workspace_id)
        if not workspace:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Workspace with id {workspace_id} not found",
            )
        return await self.repository.update(workspace, data.model_dump())

    async def delete_workspace(self, workspace_id: int, current_user: User) -> None:
        # Chi OWNER moi duoc xoa workspace
        await self.access_control.check_workspace_role(
            workspace_id=workspace_id,
            user=current_user,
            allowed_roles=[WorkspaceRole.OWNER],
        )
        workspace = await self.repository.get_by_id(workspace_id)
        if not workspace:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Workspace with id {workspace_id} not found",
            )
        await self.repository.delete(workspace)

    async def add_member(
        self,
        workspace_id: int,
        data: WorkspaceMemberAdd,
        current_user: User,
    ) -> WorkspaceMemberResponse:
        # Chi OWNER duoc invite thanh vien
        await self.access_control.check_workspace_role(
            workspace_id=workspace_id,
            user=current_user,
            allowed_roles=[WorkspaceRole.OWNER],
        )

        user = await self.user_repository.get_by_id(data.user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User with id {data.user_id} not found",
            )

        existing = await self.member_repository.get_member(workspace_id, data.user_id)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User is already a member of this workspace",
            )

        member = WorkspaceMember(
            workspace_id=workspace_id,
            user_id=data.user_id,
            role=data.role,
        )
        saved = await self.member_repository.create(member)
        return WorkspaceMemberResponse.model_validate(saved)

    async def remove_member(
        self,
        workspace_id: int,
        user_id: int,
        current_user: User,
    ) -> None:
        # Chi OWNER duoc remove thanh vien
        await self.access_control.check_workspace_role(
            workspace_id=workspace_id,
            user=current_user,
            allowed_roles=[WorkspaceRole.OWNER],
        )

        workspace = await self.repository.get_by_id(workspace_id)
        if not workspace:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Workspace with id {workspace_id} not found",
            )

        if user_id == workspace.owner_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot remove owner from workspace",
            )

        member = await self.member_repository.get_member(workspace_id, user_id)
        if not member:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Member not found in workspace",
            )

        await self.member_repository.delete(member)

    async def update_member_role(
        self,
        workspace_id: int,
        user_id: int,
        data: WorkspaceMemberUpdate,
        current_user: User,
    ) -> WorkspaceMemberResponse:
        # Chi OWNER moi duoc phan quyen lai cho thanh vien
        await self.access_control.check_workspace_role(
            workspace_id=workspace_id,
            user=current_user,
            allowed_roles=[WorkspaceRole.OWNER],
        )

        member = await self.member_repository.get_member(workspace_id, user_id)
        if not member:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Member not found in workspace",
            )

        updated = await self.member_repository.update(member, {"role": data.role})
        return WorkspaceMemberResponse.model_validate(updated)
