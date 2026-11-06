from fastapi import Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.repositories.task_repository import TaskRepository
from app.services.task_service import TaskService


def get_task_repository(db: Session = Depends(get_db)) -> TaskRepository:
    return TaskRepository(db)


def get_task_service(repo: TaskRepository = Depends(get_task_repository)) -> TaskService:
    return TaskService(repo)
