from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.core.database import engine


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: database schema duoc quan ly bang Alembic migration
    yield
    # Shutdown: giai phong connection pool
    await engine.dispose()
