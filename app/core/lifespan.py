from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.core.database import engine
from app.models.base import Base


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Khoi tao database tables khi start app
    Base.metadata.create_all(bind=engine)
    yield
    # Dong connection khi tat app
    engine.dispose()
