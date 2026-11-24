from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.label import Label
from app.repositories.base import BaseRepository


class LabelRepository(BaseRepository[Label]):
    def __init__(self, db: AsyncSession):
        super().__init__(Label, db)

    async def get_by_project_and_name(
        self,
        project_id: int,
        name: str,
    ) -> Optional[Label]:
        stmt = select(Label).where(
            Label.project_id == project_id,
            Label.name == name,
        )
        result = await self.db.scalars(stmt)
        return result.first()

    async def get_project_labels(self, project_id: int) -> List[Label]:
        stmt = select(Label).where(Label.project_id == project_id).order_by(Label.id.asc())
        result = await self.db.scalars(stmt)
        return list(result.all())
