from typing import Optional

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.refresh_token import RefreshToken
from app.repositories.base import BaseRepository


class RefreshTokenRepository(BaseRepository[RefreshToken]):
    def __init__(self, db: AsyncSession):
        super().__init__(RefreshToken, db)

    async def get_by_jti(self, jti: str) -> Optional[RefreshToken]:
        stmt = select(RefreshToken).where(RefreshToken.jti == jti)
        result = await self.db.scalars(stmt)
        return result.first()

    async def revoke(self, token_obj: RefreshToken) -> RefreshToken:
        return await self.update(token_obj, {"is_revoked": True})

    async def revoke_all_for_user(self, user_id: int) -> None:
        stmt = (
            update(RefreshToken)
            .where(RefreshToken.user_id == user_id, RefreshToken.is_revoked.is_(False))
            .values(is_revoked=True)
        )
        await self.db.execute(stmt)
        await self.db.commit()
