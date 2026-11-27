from typing import List

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.comment import Comment
from app.repositories.base import BaseRepository


class CommentRepository(BaseRepository[Comment]):
    def __init__(self, db: AsyncSession):
        super().__init__(Comment, db)

    async def get_task_comments(self, task_id: int) -> List[Comment]:
        stmt = select(Comment).where(Comment.task_id == task_id).order_by(Comment.id.asc())
        result = await self.db.scalars(stmt)
        return list(result.all())
