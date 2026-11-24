from typing import Generic, List, Optional, Sequence, Tuple, Type, TypeVar

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.base import Base

ModelType = TypeVar("ModelType", bound=Base)


class BaseRepository(Generic[ModelType]):
    def __init__(self, model: Type[ModelType], db: AsyncSession):
        self.model = model
        self.db = db

    async def get_by_id(self, id: int) -> Optional[ModelType]:
        return await self.db.get(self.model, id)

    async def get_multi(
        self,
        page: int = 1,
        page_size: int = 10,
        filters: Optional[Sequence] = None,
        order_by=None,
    ) -> Tuple[List[ModelType], int]:
        stmt = select(self.model)
        count_stmt = select(func.count()).select_from(self.model)

        if filters:
            for condition in filters:
                stmt = stmt.where(condition)
                count_stmt = count_stmt.where(condition)

        if order_by is not None:
            stmt = stmt.order_by(order_by)

        offset = (page - 1) * page_size
        stmt = stmt.offset(offset).limit(page_size)

        total = (await self.db.scalar(count_stmt)) or 0
        result = await self.db.scalars(stmt)
        items = list(result.all())
        return items, total

    async def create(self, obj: ModelType) -> ModelType:
        self.db.add(obj)
        await self.db.commit()
        await self.db.refresh(obj)
        return obj

    async def update(self, db_obj: ModelType, update_data: dict) -> ModelType:
        for key, value in update_data.items():
            if hasattr(db_obj, key):
                setattr(db_obj, key, value)
        await self.db.commit()
        await self.db.refresh(db_obj)
        return db_obj

    async def delete(self, db_obj: ModelType) -> None:
        await self.db.delete(db_obj)
        await self.db.commit()
