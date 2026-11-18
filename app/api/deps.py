from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.repositories.project_repository import ProjectRepository
from app.repositories.task_repository import TaskRepository
from app.repositories.user_repository import UserRepository
from app.repositories.workspace_repository import WorkspaceRepository
from app.services.project_service import ProjectService
from app.services.task_service import TaskService
from app.services.user_service import UserService
from app.services.workspace_service import WorkspaceService


def get_user_repository(db: AsyncSession = Depends(get_db)) -> UserRepository:
    return UserRepository(db)


def get_workspace_repository(db: AsyncSession = Depends(get_db)) -> WorkspaceRepository:
    return WorkspaceRepository(db)


def get_project_repository(db: AsyncSession = Depends(get_db)) -> ProjectRepository:
    return ProjectRepository(db)


def get_task_repository(db: AsyncSession = Depends(get_db)) -> TaskRepository:
    return TaskRepository(db)


def get_user_service(repo: UserRepository = Depends(get_user_repository)) -> UserService:
    return UserService(repo)


def get_workspace_service(
    repo: WorkspaceRepository = Depends(get_workspace_repository),
    user_repo: UserRepository = Depends(get_user_repository),
) -> WorkspaceService:
    return WorkspaceService(repo, user_repo)


def get_project_service(
    repo: ProjectRepository = Depends(get_project_repository),
    workspace_repo: WorkspaceRepository = Depends(get_workspace_repository),
) -> ProjectService:
    return ProjectService(repo, workspace_repo)


def get_task_service(
    repo: TaskRepository = Depends(get_task_repository),
    project_repo: ProjectRepository = Depends(get_project_repository),
) -> TaskService:
    return TaskService(repo, project_repo)
