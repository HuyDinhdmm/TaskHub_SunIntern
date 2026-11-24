from typing import Sequence
from fastapi import HTTPException, status
from app.models.enums import UserRole, WorkspaceRole
from app.models.user import User
from app.models.workspace import WorkspaceMember
from app.repositories.workspace_member_repository import WorkspaceMemberRepository
from app.repositories.workspace_repository import WorkspaceRepository


class AccessControl:
    def __init__(
        self,
        workspace_repo: WorkspaceRepository,
        member_repo: WorkspaceMemberRepository,
    ):
        self.workspace_repo = workspace_repo
        self.member_repo = member_repo

    async def check_workspace_role(
        self,
        workspace_id: int,
        user: User,
        allowed_roles: Sequence[WorkspaceRole],
    ) -> WorkspaceMember:
        # ADMIN he thong co toan quyen
        if user.role == UserRole.ADMIN:
            return WorkspaceMember(
                workspace_id=workspace_id,
                user_id=user.id,
                role=WorkspaceRole.OWNER,
            )

        workspace = await self.workspace_repo.get_by_id(workspace_id)
        if not workspace:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Workspace with id {workspace_id} not found",
            )

        member = await self.member_repo.get_member(workspace_id, user.id)
        if not member:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You are not a member of this workspace",
            )

        if member.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission denied. Required role in: {[r.value for r in allowed_roles]}",
            )

        return member
