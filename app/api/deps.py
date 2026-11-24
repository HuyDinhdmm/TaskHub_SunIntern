import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.permissions import AccessControl
from app.core.security import decode_token
from app.models.user import User
from app.repositories.project_repository import ProjectRepository
from app.repositories.refresh_token_repository import RefreshTokenRepository
from app.repositories.task_repository import TaskRepository
from app.repositories.user_repository import UserRepository
from app.repositories.workspace_member_repository import WorkspaceMemberRepository
from app.repositories.workspace_repository import WorkspaceRepository
from app.services.auth_service import AuthService
from app.services.project_service import ProjectService
from app.services.task_service import TaskService
from app.services.user_service import UserService
from app.services.workspace_service import WorkspaceService

bearer_scheme = HTTPBearer(auto_error=False)


def get_user_repository(db: AsyncSession = Depends(get_db)) -> UserRepository:
    return UserRepository(db)


def get_refresh_token_repository(
    db: AsyncSession = Depends(get_db),
) -> RefreshTokenRepository:
    return RefreshTokenRepository(db)


def get_workspace_repository(db: AsyncSession = Depends(get_db)) -> WorkspaceRepository:
    return WorkspaceRepository(db)


def get_workspace_member_repository(
    db: AsyncSession = Depends(get_db),
) -> WorkspaceMemberRepository:
    return WorkspaceMemberRepository(db)


def get_project_repository(db: AsyncSession = Depends(get_db)) -> ProjectRepository:
    return ProjectRepository(db)


def get_task_repository(db: AsyncSession = Depends(get_db)) -> TaskRepository:
    return TaskRepository(db)


def get_access_control(
    ws_repo: WorkspaceRepository = Depends(get_workspace_repository),
    member_repo: WorkspaceMemberRepository = Depends(get_workspace_member_repository),
) -> AccessControl:
    return AccessControl(ws_repo, member_repo)


def get_auth_service(
    user_repo: UserRepository = Depends(get_user_repository),
    token_repo: RefreshTokenRepository = Depends(get_refresh_token_repository),
) -> AuthService:
    return AuthService(user_repo, token_repo)


def get_user_service(
    repo: UserRepository = Depends(get_user_repository),
    token_repo: RefreshTokenRepository = Depends(get_refresh_token_repository),
) -> UserService:
    return UserService(repo, token_repo)


def get_workspace_service(
    repo: WorkspaceRepository = Depends(get_workspace_repository),
    member_repo: WorkspaceMemberRepository = Depends(get_workspace_member_repository),
    user_repo: UserRepository = Depends(get_user_repository),
    access_control: AccessControl = Depends(get_access_control),
) -> WorkspaceService:
    return WorkspaceService(repo, member_repo, user_repo, access_control)


def get_project_service(
    repo: ProjectRepository = Depends(get_project_repository),
    workspace_repo: WorkspaceRepository = Depends(get_workspace_repository),
    access_control: AccessControl = Depends(get_access_control),
) -> ProjectService:
    return ProjectService(repo, workspace_repo, access_control)


def get_task_service(
    repo: TaskRepository = Depends(get_task_repository),
    project_repo: ProjectRepository = Depends(get_project_repository),
) -> TaskService:
    return TaskService(repo, project_repo)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    user_repo: UserRepository = Depends(get_user_repository),
) -> User:
    if credentials is None or not credentials.credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authorization token",
        )

    try:
        payload = decode_token(credentials.credentials)
    except jwt.PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired access token",
        )

    if payload.get("type") != "access" or not payload.get("sub"):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid access token",
        )

    try:
        user_id = int(payload["sub"])
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token subject",
        )

    user = await user_repo.get_by_id(user_id)
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive",
        )
    return user
