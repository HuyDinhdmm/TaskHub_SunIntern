from typing import AsyncGenerator
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from app.core.database import get_db
from app.main import app
from app.models import Base

TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

engine = create_async_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


@pytest_asyncio.fixture(scope="function")
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with TestingSessionLocal() as session:
        yield session

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture(scope="function")
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()


@pytest_asyncio.fixture(scope="function")
async def sample_project(client: AsyncClient) -> dict:
    user_resp = await client.post(
        "/api/v1/users",
        json={
            "email": "intern@taskhub.local",
            "full_name": "Intern User",
            "password": "password123",
        },
    )
    user = user_resp.json()

    ws_resp = await client.post(
        "/api/v1/workspaces",
        json={"name": "Sun Intern Workspace", "owner_id": user["id"]},
    )
    workspace = ws_resp.json()

    proj_resp = await client.post(
        "/api/v1/projects",
        json={
            "workspace_id": workspace["id"],
            "name": "TaskHub Backend",
            "description": "FastAPI training project",
        },
    )
    project = proj_resp.json()
    return {"user": user, "workspace": workspace, "project": project}
