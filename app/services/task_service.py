import math
from typing import Optional

from fastapi import BackgroundTasks, HTTPException, status

from app.core.cache import delete_cache, get_cache, set_cache
from app.core.notifications import send_task_assignment_email
from app.core.permissions import AccessControl
from app.models.comment import Comment
from app.models.enums import TaskPriority, TaskStatus, WorkspaceRole
from app.models.label import Label
from app.models.task import Task
from app.models.user import User
from app.repositories.comment_repository import CommentRepository
from app.repositories.label_repository import LabelRepository
from app.repositories.project_repository import ProjectRepository
from app.repositories.task_repository import TaskRepository
from app.repositories.user_repository import UserRepository
from app.schemas.comment import CommentCreate
from app.schemas.label import LabelCreate, LabelUpdate
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
        label_repository: LabelRepository,
        comment_repository: CommentRepository,
        user_repository: UserRepository,
        access_control: AccessControl,
    ):
        self.repository = repository
        self.project_repository = project_repository
        self.label_repository = label_repository
        self.comment_repository = comment_repository
        self.user_repository = user_repository
        self.access_control = access_control

    async def _get_project_with_check(
        self,
        project_id: int,
        user: User,
        allowed_roles: list[WorkspaceRole],
    ):
        project = await self.project_repository.get_by_id(project_id)
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Project with id {project_id} not found",
            )
        await self.access_control.check_workspace_role(
            workspace_id=project.workspace_id,
            user=user,
            allowed_roles=allowed_roles,
        )
        return project

    async def create_task(
        self,
        project_id: int,
        data: TaskCreate,
        current_user: User,
        background_tasks: Optional[BackgroundTasks] = None,
    ) -> Task:
        # OWNER va EDITOR duoc tao task trong project
        await self._get_project_with_check(
            project_id=project_id,
            user=current_user,
            allowed_roles=[WorkspaceRole.OWNER, WorkspaceRole.EDITOR],
        )

        assignee = None
        if data.assignee_id is not None:
            assignee = await self.user_repository.get_by_id(data.assignee_id)
            if not assignee:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Assignee user with id {data.assignee_id} not found",
                )

        task = Task(
            project_id=project_id,
            assignee_id=data.assignee_id,
            title=data.title,
            description=data.description,
            status=data.status,
            priority=data.priority,
            due_date=data.due_date,
            created_by=current_user.id,
        )
        saved = await self.repository.create(task)

        # Gui email thong bao trong background neu co assignee
        if assignee and background_tasks is not None:
            background_tasks.add_task(
                send_task_assignment_email,
                to_email=assignee.email,
                recipient_name=assignee.full_name or assignee.email,
                task_title=saved.title,
                task_id=saved.id,
            )

        # Invalidate cache cua project nay
        await delete_cache(f"project:{project_id}:tasks:*")
        return await self.repository.get_detail(saved.id) or saved

    async def get_task(self, task_id: int, current_user: User) -> Task:
        task = await self.repository.get_detail(task_id)
        if not task:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Task with id {task_id} not found",
            )
        await self._get_project_with_check(
            project_id=task.project_id,
            user=current_user,
            allowed_roles=[WorkspaceRole.OWNER, WorkspaceRole.EDITOR, WorkspaceRole.VIEWER],
        )
        return task

    async def list_project_tasks(
        self,
        project_id: int,
        current_user: User,
        page: int = 1,
        page_size: int = 10,
        status_filter: Optional[TaskStatus] = None,
        priority_filter: Optional[TaskPriority] = None,
        assignee_id: Optional[int] = None,
        search: Optional[str] = None,
    ) -> TaskListResponse:
        await self._get_project_with_check(
            project_id=project_id,
            user=current_user,
            allowed_roles=[WorkspaceRole.OWNER, WorkspaceRole.EDITOR, WorkspaceRole.VIEWER],
        )

        cache_key = (
            f"project:{project_id}:tasks:p={page}:s={page_size}:"
            f"st={status_filter}:pr={priority_filter}:as={assignee_id}:q={search}"
        )
        cached_data = await get_cache(cache_key)
        if cached_data:
            return TaskListResponse.model_validate(cached_data)

        items, total = await self.repository.get_tasks(
            page=page,
            page_size=page_size,
            project_id=project_id,
            assignee_id=assignee_id,
            status=status_filter,
            priority=priority_filter,
            search=search,
        )
        total_pages = math.ceil(total / page_size) if total > 0 else 0
        response = TaskListResponse(
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
            items=[TaskResponse.model_validate(t) for t in items],
        )

        await set_cache(cache_key, response.model_dump(mode="json"), expire_seconds=60)
        return response

    async def update_task(
        self,
        task_id: int,
        data: TaskUpdate,
        current_user: User,
    ) -> Task:
        task = await self.repository.get_by_id(task_id)
        if not task:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Task with id {task_id} not found",
            )
        await self._get_project_with_check(
            project_id=task.project_id,
            user=current_user,
            allowed_roles=[WorkspaceRole.OWNER, WorkspaceRole.EDITOR],
        )

        update_data = data.model_dump()
        await self.repository.update(task, update_data)
        await delete_cache(f"project:{task.project_id}:tasks:*")
        return await self.repository.get_detail(task_id) or task

    async def patch_task(
        self,
        task_id: int,
        data: TaskPatch,
        current_user: User,
        background_tasks: Optional[BackgroundTasks] = None,
    ) -> Task:
        task = await self.repository.get_by_id(task_id)
        if not task:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Task with id {task_id} not found",
            )
        await self._get_project_with_check(
            project_id=task.project_id,
            user=current_user,
            allowed_roles=[WorkspaceRole.OWNER, WorkspaceRole.EDITOR],
        )

        old_assignee_id = task.assignee_id
        patch_data = data.model_dump(exclude_unset=True)

        new_assignee = None
        if "assignee_id" in patch_data and patch_data["assignee_id"] is not None:
            new_assignee_id = patch_data["assignee_id"]
            if new_assignee_id != old_assignee_id:
                new_assignee = await self.user_repository.get_by_id(new_assignee_id)
                if not new_assignee:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail=f"Assignee user with id {new_assignee_id} not found",
                    )

        await self.repository.update(task, patch_data)

        # Gui email thong bao neu co assignee moi
        if new_assignee and background_tasks is not None:
            background_tasks.add_task(
                send_task_assignment_email,
                to_email=new_assignee.email,
                recipient_name=new_assignee.full_name or new_assignee.email,
                task_title=task.title,
                task_id=task.id,
            )

        await delete_cache(f"project:{task.project_id}:tasks:*")
        return await self.repository.get_detail(task_id) or task

    async def delete_task(self, task_id: int, current_user: User) -> None:
        task = await self.repository.get_by_id(task_id)
        if not task:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Task with id {task_id} not found",
            )
        await self._get_project_with_check(
            project_id=task.project_id,
            user=current_user,
            allowed_roles=[WorkspaceRole.OWNER, WorkspaceRole.EDITOR],
        )
        await self.repository.delete(task)
        await delete_cache(f"project:{task.project_id}:tasks:*")

    # Labels
    async def create_label(self, project_id: int, data: LabelCreate, current_user: User) -> Label:
        await self._get_project_with_check(
            project_id=project_id,
            user=current_user,
            allowed_roles=[WorkspaceRole.OWNER, WorkspaceRole.EDITOR],
        )
        existing = await self.label_repository.get_by_project_and_name(project_id, data.name)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Label '{data.name}' already exists in this project",
            )
        label = Label(project_id=project_id, name=data.name, color=data.color)
        return await self.label_repository.create(label)

    async def list_project_labels(self, project_id: int, current_user: User) -> list[Label]:
        await self._get_project_with_check(
            project_id=project_id,
            user=current_user,
            allowed_roles=[WorkspaceRole.OWNER, WorkspaceRole.EDITOR, WorkspaceRole.VIEWER],
        )
        return await self.label_repository.get_project_labels(project_id)

    async def update_label(self, label_id: int, data: LabelUpdate, current_user: User) -> Label:
        label = await self.label_repository.get_by_id(label_id)
        if not label:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Label with id {label_id} not found",
            )
        await self._get_project_with_check(
            project_id=label.project_id,
            user=current_user,
            allowed_roles=[WorkspaceRole.OWNER, WorkspaceRole.EDITOR],
        )
        return await self.label_repository.update(label, data.model_dump())

    async def delete_label(self, label_id: int, current_user: User) -> None:
        label = await self.label_repository.get_by_id(label_id)
        if not label:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Label with id {label_id} not found",
            )
        await self._get_project_with_check(
            project_id=label.project_id,
            user=current_user,
            allowed_roles=[WorkspaceRole.OWNER, WorkspaceRole.EDITOR],
        )
        await self.label_repository.delete(label)

    async def add_label_to_task(self, task_id: int, label_id: int, current_user: User) -> Task:
        task = await self.repository.get_detail(task_id)
        if not task:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Task with id {task_id} not found",
            )
        await self._get_project_with_check(
            project_id=task.project_id,
            user=current_user,
            allowed_roles=[WorkspaceRole.OWNER, WorkspaceRole.EDITOR],
        )
        label = await self.label_repository.get_by_id(label_id)
        if not label or label.project_id != task.project_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Label with id {label_id} not found in this project",
            )

        if label not in task.labels:
            task.labels.append(label)
            await self.repository.db.commit()
            await self.repository.db.refresh(task)
            await delete_cache(f"project:{task.project_id}:tasks:*")
        return task

    async def remove_label_from_task(self, task_id: int, label_id: int, current_user: User) -> Task:
        task = await self.repository.get_detail(task_id)
        if not task:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Task with id {task_id} not found",
            )
        await self._get_project_with_check(
            project_id=task.project_id,
            user=current_user,
            allowed_roles=[WorkspaceRole.OWNER, WorkspaceRole.EDITOR],
        )
        label = await self.label_repository.get_by_id(label_id)
        if not label:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Label with id {label_id} not found",
            )

        if label in task.labels:
            task.labels.remove(label)
            await self.repository.db.commit()
            await self.repository.db.refresh(task)
            await delete_cache(f"project:{task.project_id}:tasks:*")
        return task

    # Comments
    async def add_comment(self, task_id: int, data: CommentCreate, current_user: User) -> Comment:
        task = await self.repository.get_by_id(task_id)
        if not task:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Task with id {task_id} not found",
            )
        await self._get_project_with_check(
            project_id=task.project_id,
            user=current_user,
            allowed_roles=[WorkspaceRole.OWNER, WorkspaceRole.EDITOR, WorkspaceRole.VIEWER],
        )

        comment = Comment(
            task_id=task_id,
            author_id=current_user.id,
            content=data.content,
        )
        return await self.comment_repository.create(comment)

    async def delete_comment(self, comment_id: int, current_user: User) -> None:
        comment = await self.comment_repository.get_by_id(comment_id)
        if not comment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Comment with id {comment_id} not found",
            )

        task = await self.repository.get_by_id(comment.task_id)
        if not task:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Task not found",
            )

        # Nguoi viet comment hoac OWNER duoc xoa
        if comment.author_id != current_user.id:
            await self._get_project_with_check(
                project_id=task.project_id,
                user=current_user,
                allowed_roles=[WorkspaceRole.OWNER],
            )

        await self.comment_repository.delete(comment)
