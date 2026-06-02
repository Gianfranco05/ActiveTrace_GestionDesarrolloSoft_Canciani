import uuid

from sqlalchemy import select, update

from app.models.auth_user import AuthUser, RefreshToken, ResetToken
from app.repositories.base import BaseRepository


class AuthRepository(BaseRepository[AuthUser]):
    def __init__(self, session, tenant_id: uuid.UUID):
        super().__init__(session, tenant_id, AuthUser)

    async def find_by_email(self, email: str) -> AuthUser | None:
        query = select(AuthUser).where(
            AuthUser.tenant_id == self._tenant_id,
            AuthUser.email == email,
            AuthUser.deleted_at.is_(None),
        )
        result = await self._session.execute(query)
        return result.scalar_one_or_none()

    async def find_by_email_across_tenants(self, email: str) -> AuthUser | None:
        query = select(AuthUser).where(
            AuthUser.email == email,
            AuthUser.deleted_at.is_(None),
        )
        result = await self._session.execute(query)
        return result.scalar_one_or_none()


class RefreshTokenRepository(BaseRepository[RefreshToken]):
    def __init__(self, session, tenant_id: uuid.UUID):
        super().__init__(session, tenant_id, RefreshToken)

    async def find_by_hash(self, token_hash: str) -> RefreshToken | None:
        query = select(RefreshToken).where(
            RefreshToken.token_hash == token_hash,
        )
        result = await self._session.execute(query)
        return result.scalar_one_or_none()

    async def invalidate_all_for_user(self, user_id: uuid.UUID) -> None:
        stmt = (
            update(RefreshToken)
            .where(
                RefreshToken.user_id == user_id,
                RefreshToken.is_used == False,  # noqa: E712
            )
            .values(is_used=True)
        )
        await self._session.execute(stmt)
        await self._session.commit()


class ResetTokenRepository(BaseRepository[ResetToken]):
    def __init__(self, session, tenant_id: uuid.UUID):
        super().__init__(session, tenant_id, ResetToken)

    async def find_by_hash(self, token_hash: str) -> ResetToken | None:
        query = select(ResetToken).where(
            ResetToken.token_hash == token_hash,
        )
        result = await self._session.execute(query)
        return result.scalar_one_or_none()

    async def mark_used(self, token_id: uuid.UUID) -> None:
        stmt = update(ResetToken).where(
            ResetToken.id == token_id,
        ).values(is_used=True)
        await self._session.execute(stmt)
        await self._session.commit()
