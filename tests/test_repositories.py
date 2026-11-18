import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from app.models import (
    Comment,
    Label,
    Project,
    Task,
    User,
    Workspace,
    WorkspaceMember,
    WorkspaceRole,
)
from app.repositories import (
    ProjectRepository,
    TaskRepository,
    UserRepository,
    WorkspaceRepository,
)


@pytest.mark.asyncio
async def test_models_relationships_and_repositories(db_session: AsyncSession):
    user_repo = UserRepository(db_session)
    ws_repo = WorkspaceRepository(db_session)
    project_repo = ProjectRepository(db_session)
    task_repo = TaskRepository(db_session)

    # 1. Tao User
    user = await user_repo.create(
        User(
            email="dev@taskhub.local",
            full_name="Dev Intern",
            hashed_password="hashed_value",
        )
    )
    assert user.id is not None

    # 2. Tao Workspace va WorkspaceMember
    workspace = await ws_repo.create(Workspace(name="Backend Team", owner_id=user.id))
    member = WorkspaceMember(
        workspace_id=workspace.id,
        user_id=user.id,
        role=WorkspaceRole.OWNER,
    )
    db_session.add(member)
    await db_session.commit()

    # 3. Tao Project
    project = await project_repo.create(
        Project(workspace_id=workspace.id, name="TaskHub Core")
    )

    # 4. Tao Label & Task & Comment
    label = Label(project_id=project.id, name="backend", color="#10B981")
    db_session.add(label)
    await db_session.commit()
    await db_session.refresh(label)

    task = await task_repo.create(
        Task(
            project_id=project.id,
            assignee_id=user.id,
            created_by=user.id,
            title="Implement Alembic",
        )
    )
    task_id = task.id
    task_detail = await task_repo.get_detail(task_id)
    assert task_detail is not None
    task_detail.labels.append(label)

    comment = Comment(task_id=task_id, author_id=user.id, content="Done migration!")
    db_session.add(comment)
    await db_session.commit()

    # Clear cache trong session de dam bao query truc tiep tu DB
    db_session.expire_all()

    # Kiem tra load lai relationships (labels + comments)
    loaded = await task_repo.get_detail(task_id)
    assert loaded is not None
    assert len(loaded.labels) == 1
    assert loaded.labels[0].name == "backend"
    assert len(loaded.comments) == 1
    assert loaded.comments[0].content == "Done migration!"
