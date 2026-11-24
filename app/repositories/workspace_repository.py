from typing import List, Optional, Tuple
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.workspace import Workspace, WorkspaceMember
from app.repositories.base import BaseRepository


class WorkspaceRepository(BaseRepository[Workspace]):
    def __init__(self, db: AsyncSession):
        super().__init__(Workspace, db)

    async def get_user_workspaces(
        self,
        user_id: int,
        page: int = 1,
        page_size: int = 10,
    ) -> Tuple[List[Workspace], int]:
        stmt = (
            select(Workspace)
            .join(WorkspaceMember, Workspace.id == WorkspaceMember.workspace_id)
            .where(WorkspaceMember.user_id == user_id)
            .order_by(Workspace.id.desc())
        )
        return await self.get_multi(
            page=page,
            page_size=page_size,
            order_by=Workspace.id.desc(),
        )
