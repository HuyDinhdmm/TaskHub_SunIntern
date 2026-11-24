from typing import Optional
from fastapi import APIRouter, Depends, Query, status
from app.api.deps import get_current_user, get_task_service
from app.models.enums import TaskPriority, TaskStatus
from app.models.user import User
from app.schemas.comment import CommentCreate, CommentResponse
from app.schemas.label import LabelCreate, LabelResponse, LabelUpdate
from app.schemas.task import (
    TaskCreate,
    TaskListResponse,
    TaskPatch,
    TaskResponse,
    TaskUpdate,
)
from app.services.task_service import TaskService

router = APIRouter(tags=["tasks"])


# GET /api/v1/projects/{id}/tasks (filter + pagination + cache)
@router.get("/projects/{project_id}/tasks", response_model=TaskListResponse)
async def list_project_tasks(
    project_id: int,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=10, ge=1, le=100),
    status: Optional[TaskStatus] = None,
    priority: Optional[TaskPriority] = None,
    assignee_id: Optional[int] = None,
    search: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    task_service: TaskService = Depends(get_task_service),
):
    return await task_service.list_project_tasks(
        project_id=project_id,
        current_user=current_user,
        page=page,
        page_size=page_size,
        status_filter=status,
        priority_filter=priority,
        assignee_id=assignee_id,
        search=search,
    )


# POST /api/v1/projects/{id}/tasks
@router.post("/projects/{project_id}/tasks", response_model=TaskResponse, status_code=status.HTTP_201_CREATED)
async def create_project_task(
    project_id: int,
    task_in: TaskCreate,
    current_user: User = Depends(get_current_user),
    task_service: TaskService = Depends(get_task_service),
):
    return await task_service.create_task(project_id, task_in, current_user)


# GET /api/v1/tasks/{id}
@router.get("/tasks/{task_id}", response_model=TaskResponse)
async def get_task(
    task_id: int,
    current_user: User = Depends(get_current_user),
    task_service: TaskService = Depends(get_task_service),
):
    return await task_service.get_task(task_id, current_user)


# PATCH /api/v1/tasks/{id}
@router.patch("/tasks/{task_id}", response_model=TaskResponse)
async def patch_task(
    task_id: int,
    task_in: TaskPatch,
    current_user: User = Depends(get_current_user),
    task_service: TaskService = Depends(get_task_service),
):
    return await task_service.patch_task(task_id, task_in, current_user)


# DELETE /api/v1/tasks/{id}
@router.delete("/tasks/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_task(
    task_id: int,
    current_user: User = Depends(get_current_user),
    task_service: TaskService = Depends(get_task_service),
):
    await task_service.delete_task(task_id, current_user)


# POST /api/v1/tasks/{id}/labels/{label_id}
@router.post("/tasks/{task_id}/labels/{label_id}", response_model=TaskResponse)
async def add_label_to_task(
    task_id: int,
    label_id: int,
    current_user: User = Depends(get_current_user),
    task_service: TaskService = Depends(get_task_service),
):
    return await task_service.add_label_to_task(task_id, label_id, current_user)


# DELETE /api/v1/tasks/{id}/labels/{label_id}
@router.delete("/tasks/{task_id}/labels/{label_id}", response_model=TaskResponse)
async def remove_label_from_task(
    task_id: int,
    label_id: int,
    current_user: User = Depends(get_current_user),
    task_service: TaskService = Depends(get_task_service),
):
    return await task_service.remove_label_from_task(task_id, label_id, current_user)


# POST /api/v1/tasks/{id}/comments
@router.post("/tasks/{task_id}/comments", response_model=CommentResponse, status_code=status.HTTP_201_CREATED)
async def add_comment(
    task_id: int,
    comment_in: CommentCreate,
    current_user: User = Depends(get_current_user),
    task_service: TaskService = Depends(get_task_service),
):
    return await task_service.add_comment(task_id, comment_in, current_user)


# DELETE /api/v1/comments/{id}
@router.delete("/comments/{comment_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_comment(
    comment_id: int,
    current_user: User = Depends(get_current_user),
    task_service: TaskService = Depends(get_task_service),
):
    await task_service.delete_comment(comment_id, current_user)


# Labels CRUD per project
@router.post("/projects/{project_id}/labels", response_model=LabelResponse, status_code=status.HTTP_201_CREATED)
async def create_label(
    project_id: int,
    label_in: LabelCreate,
    current_user: User = Depends(get_current_user),
    task_service: TaskService = Depends(get_task_service),
):
    return await task_service.create_label(project_id, label_in, current_user)


@router.get("/projects/{project_id}/labels", response_model=list[LabelResponse])
async def list_labels(
    project_id: int,
    current_user: User = Depends(get_current_user),
    task_service: TaskService = Depends(get_task_service),
):
    return await task_service.list_project_labels(project_id, current_user)


@router.patch("/labels/{label_id}", response_model=LabelResponse)
async def update_label(
    label_id: int,
    label_in: LabelUpdate,
    current_user: User = Depends(get_current_user),
    task_service: TaskService = Depends(get_task_service),
):
    return await task_service.update_label(label_id, label_in, current_user)


@router.delete("/labels/{label_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_label(
    label_id: int,
    current_user: User = Depends(get_current_user),
    task_service: TaskService = Depends(get_task_service),
):
    await task_service.delete_label(label_id, current_user)
