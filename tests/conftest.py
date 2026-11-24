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
    # Dang ky va login de lay token
    await client.post(
        "/api/v1/auth/register",
        json={
            "email": "intern_setup@example.com",
            "full_name": "Intern Setup",
            "password": "password123",
        },
    )
    login_resp = await client.post(
        "/api/v1/auth/login",
        json={"email": "intern_setup@example.com", "password": "password123"},
    )
    token = login_resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    user_info = (await client.get("/api/v1/users/me", headers=headers)).json()

    ws_resp = await client.post(
        "/api/v1/workspaces",
        json={"name": "Sun Intern Workspace"},
        headers=headers,
    )
    workspace = ws_resp.json()

    proj_resp = await client.post(
        f"/api/v1/workspaces/{workspace['id']}/projects",
        json={
            "name": "TaskHub Backend",
            "description": "FastAPI training project",
        },
        headers=headers,
    )
    project = proj_resp.json()
    return {"user": user_info, "workspace": workspace, "project": project, "token": token, "headers": headers}
