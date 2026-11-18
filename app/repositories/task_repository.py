from typing import List, Optional, Tuple
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from app.models.enums import TaskPriority, TaskStatus
from app.models.task import Task
from app.repositories.base import BaseRepository


class TaskRepository(BaseRepository[Task]):
    def __init__(self, db: AsyncSession):
        super().__init__(Task, db)

    async def get_detail(self, task_id: int) -> Optional[Task]:
        stmt = (
            select(Task)
            .options(
                selectinload(Task.labels),
                selectinload(Task.comments),
            )
            .where(Task.id == task_id)
        )
        result = await self.db.scalars(stmt)
        return result.first()

    async def get_tasks(
        self,
        page: int = 1,
        page_size: int = 10,
        project_id: Optional[int] = None,
        assignee_id: Optional[int] = None,
        status: Optional[TaskStatus] = None,
        priority: Optional[TaskPriority] = None,
        search: Optional[str] = None,
    ) -> Tuple[List[Task], int]:
        filters = []
        if project_id is not None:
            filters.append(Task.project_id == project_id)
        if assignee_id is not None:
            filters.append(Task.assignee_id == assignee_id)
        if status is not None:
            filters.append(Task.status == status)
        if priority is not None:
            filters.append(Task.priority == priority)
        if search:
            keyword = f"%{search}%"
            filters.append(Task.title.ilike(keyword) | Task.description.ilike(keyword))

        return await self.get_multi(
            page=page,
            page_size=page_size,
            filters=filters,
            order_by=Task.id.desc(),
        )
