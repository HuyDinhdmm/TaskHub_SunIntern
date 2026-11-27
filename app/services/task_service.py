import math
from typing import Optional

from fastapi import HTTPException, status

from app.models.enums import TaskPriority, TaskStatus
from app.models.task import Task
from app.repositories.project_repository import ProjectRepository
from app.repositories.task_repository import TaskRepository
from app.schemas.task import (
    TaskCreate,
    TaskListResponse,
    TaskPatch,
    TaskResponse,
    TaskUpdate,
)


class TaskService:
    def __init__(
        self,
        repository: TaskRepository,
        project_repository: ProjectRepository,
    ):
        self.repository = repository
        self.project_repository = project_repository

    async def create_task(self, data: TaskCreate) -> Task:
        project = await self.project_repository.get_by_id(data.project_id)
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Project with id {data.project_id} not found",
            )
        task = Task(
            project_id=data.project_id,
            assignee_id=data.assignee_id,
            title=data.title,
            description=data.description,
            status=data.status,
            priority=data.priority,
            due_date=data.due_date,
            created_by=data.created_by,
        )
        return await self.repository.create(task)

    async def get_task(self, task_id: int) -> Task:
        task = await self.repository.get_by_id(task_id)
        if not task:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Task with id {task_id} not found",
            )
        return task

    async def list_tasks(
        self,
        page: int = 1,
        page_size: int = 10,
        project_id: Optional[int] = None,
        assignee_id: Optional[int] = None,
        status: Optional[TaskStatus] = None,
        priority: Optional[TaskPriority] = None,
        search: Optional[str] = None,
    ) -> TaskListResponse:
        items, total = await self.repository.get_tasks(
            page=page,
            page_size=page_size,
            project_id=project_id,
            assignee_id=assignee_id,
            status=status,
            priority=priority,
            search=search,
        )
        total_pages = math.ceil(total / page_size) if total > 0 else 0
        return TaskListResponse(
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
            items=[TaskResponse.model_validate(t) for t in items],
        )

    async def update_task(self, task_id: int, data: TaskUpdate) -> Task:
        task = await self.get_task(task_id)
        update_data = data.model_dump()
        return await self.repository.update(task, update_data)

    async def patch_task(self, task_id: int, data: TaskPatch) -> Task:
        task = await self.get_task(task_id)
        patch_data = data.model_dump(exclude_unset=True)
        return await self.repository.update(task, patch_data)

    async def delete_task(self, task_id: int) -> None:
        task = await self.get_task(task_id)
        await self.repository.delete(task)
