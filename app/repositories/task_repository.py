from typing import List, Optional, Tuple
from sqlalchemy import func, select
from sqlalchemy.orm import Session
from app.models.task import Task
from app.schemas.task import TaskPriority, TaskStatus


class TaskRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, task_id: int) -> Optional[Task]:
        return self.db.get(Task, task_id)

    def get_tasks(
        self,
        page: int = 1,
        page_size: int = 10,
        status: Optional[TaskStatus] = None,
        priority: Optional[TaskPriority] = None,
        search: Optional[str] = None,
    ) -> Tuple[List[Task], int]:
        stmt = select(Task)
        count_stmt = select(func.count()).select_from(Task)

        if status:
            stmt = stmt.where(Task.status == status.value)
            count_stmt = count_stmt.where(Task.status == status.value)

        if priority:
            stmt = stmt.where(Task.priority == priority.value)
            count_stmt = count_stmt.where(Task.priority == priority.value)

        if search:
            keyword = f"%{search}%"
            condition = Task.title.ilike(keyword) | Task.description.ilike(keyword)
            stmt = stmt.where(condition)
            count_stmt = count_stmt.where(condition)

        stmt = stmt.order_by(Task.id.desc())

        offset = (page - 1) * page_size
        stmt = stmt.offset(offset).limit(page_size)

        total = self.db.scalar(count_stmt) or 0
        items = list(self.db.scalars(stmt).all())

        return items, total

    def create(self, task: Task) -> Task:
        self.db.add(task)
        self.db.commit()
        self.db.refresh(task)
        return task

    def update(self, task: Task, update_data: dict) -> Task:
        for key, value in update_data.items():
            if hasattr(task, key) and value is not None:
                setattr(task, key, value)
        self.db.commit()
        self.db.refresh(task)
        return task

    def delete(self, task: Task) -> None:
        self.db.delete(task)
        self.db.commit()
