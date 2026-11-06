from typing import Optional
from fastapi import APIRouter, Depends, Query, status
from app.api.deps import get_task_service
from app.schemas.task import (
    TaskCreate,
    TaskListResponse,
    TaskPatch,
    TaskPriority,
    TaskResponse,
    TaskStatus,
    TaskUpdate,
)
from app.services.task_service import TaskService

router = APIRouter(prefix="/tasks", tags=["tasks"])


@router.post("", response_model=TaskResponse, status_code=status.HTTP_201_CREATED)
def create_task(
    task_in: TaskCreate,
    task_service: TaskService = Depends(get_task_service),
):
    return task_service.create_task(task_in)


@router.get("", response_model=TaskListResponse)
def get_tasks(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=10, ge=1, le=100),
    status: Optional[TaskStatus] = None,
    priority: Optional[TaskPriority] = None,
    search: Optional[str] = None,
    task_service: TaskService = Depends(get_task_service),
):
    return task_service.list_tasks(
        page=page,
        page_size=page_size,
        status=status,
        priority=priority,
        search=search,
    )


@router.get("/{task_id}", response_model=TaskResponse)
def get_task(
    task_id: int,
    task_service: TaskService = Depends(get_task_service),
):
    return task_service.get_task(task_id)


@router.put("/{task_id}", response_model=TaskResponse)
def update_task(
    task_id: int,
    task_in: TaskUpdate,
    task_service: TaskService = Depends(get_task_service),
):
    return task_service.update_task(task_id, task_in)


@router.patch("/{task_id}", response_model=TaskResponse)
def patch_task(
    task_id: int,
    task_in: TaskPatch,
    task_service: TaskService = Depends(get_task_service),
):
    return task_service.patch_task(task_id, task_in)


@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_task(
    task_id: int,
    task_service: TaskService = Depends(get_task_service),
):
    task_service.delete_task(task_id)
