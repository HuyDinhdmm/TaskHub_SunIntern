from typing import List, Optional, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.enums import ProjectStatus
from app.models.project import Project
from app.repositories.base import BaseRepository


class ProjectRepository(BaseRepository[Project]):
    def __init__(self, db: AsyncSession):
        super().__init__(Project, db)

    async def get_projects(
        self,
        page: int = 1,
        page_size: int = 10,
        workspace_id: Optional[int] = None,
        status: Optional[ProjectStatus] = None,
    ) -> Tuple[List[Project], int]:
        filters = []
        if workspace_id is not None:
            filters.append(Project.workspace_id == workspace_id)
        if status is not None:
            filters.append(Project.status == status)

        return await self.get_multi(
            page=page,
            page_size=page_size,
            filters=filters,
            order_by=Project.id.desc(),
        )
