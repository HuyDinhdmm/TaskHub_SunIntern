from typing import Optional
from fastapi import HTTPException, status
from app.models.task import Task
from app.repositories.task_repository import TaskRepository
from app.schemas.task import (
    TaskCreate,
    TaskListResponse,
    TaskPatch,
    TaskPriority,
    TaskResponse,
    TaskStatus,
    TaskUpdate,
)


class TaskService:
    def __init__(self, repository: TaskRepository):
        self.repository = repository

    def create_task(self, data: TaskCreate) -> Task:
        task = Task(
            title=data.title,
            description=data.description,
            status=data.status.value,
            priority=data.priority.value,
            due_date=data.due_date,
        )
        return self.repository.create(task)

    def get_task(self, task_id: int) -> Task:
        task = self.repository.get_by_id(task_id)
        if not task:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Task with id {task_id} not found",
            )
        return task

    def list_tasks(
        self,
        page: int = 1,
        page_size: int = 10,
        status: Optional[TaskStatus] = None,
        priority: Optional[TaskPriority] = None,
        search: Optional[str] = None,
    ) -> TaskListResponse:
        items, total = self.repository.get_tasks(
            page=page,
            page_size=page_size,
            status=status,
            priority=priority,
            search=search,
        )
        return TaskListResponse(
            total=total,
            page=page,
            page_size=page_size,
            items=[TaskResponse.model_validate(t) for t in items],
        )

    def update_task(self, task_id: int, data: TaskUpdate) -> Task:
        task = self.get_task(task_id)
        update_data = {
            "title": data.title,
            "description": data.description,
            "status": data.status.value,
            "priority": data.priority.value,
            "due_date": data.due_date,
        }
        return self.repository.update(task, update_data)

    def patch_task(self, task_id: int, data: TaskPatch) -> Task:
        task = self.get_task(task_id)
        patch_data = data.model_dump(exclude_unset=True)

        if "status" in patch_data and patch_data["status"]:
            patch_data["status"] = patch_data["status"].value
        if "priority" in patch_data and patch_data["priority"]:
            patch_data["priority"] = patch_data["priority"].value

        return self.repository.update(task, patch_data)

    def delete_task(self, task_id: int) -> None:
        task = self.get_task(task_id)
        self.repository.delete(task)
