from typing import List, Tuple

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
        filters = [Workspace.members.any(WorkspaceMember.user_id == user_id)]
        return await self.get_multi(
            page=page,
            page_size=page_size,
            filters=filters,
            order_by=Workspace.id.desc(),
        )
