import copy
import uuid
from datetime import UTC, datetime
from typing import Self

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.base import BaseModelMixin


class BaseRepository[T: BaseModelMixin]:
    def __init__(
        self,
        session: AsyncSession,
        tenant_id: uuid.UUID,
        model_class: type[T],
    ) -> None:
        self._session = session
        self._tenant_id = tenant_id
        self._model_class = model_class
        self._include_deleted = False
        self._only_deleted = False

    async def list(self, **filters) -> list[T]:
        query = select(self._model_class).where(
            self._model_class.tenant_id == self._tenant_id,
        )
        query = self._apply_soft_delete_filter(query)
        for field, value in filters.items():
            query = query.where(
                getattr(self._model_class, field) == value,
            )
        result = await self._session.execute(query)
        return list(result.scalars().all())

    async def get(self, id: uuid.UUID) -> T | None:
        query = select(self._model_class).where(
            self._model_class.id == id,
            self._model_class.tenant_id == self._tenant_id,
        )
        query = self._apply_soft_delete_filter(query)
        result = await self._session.execute(query)
        return result.scalar_one_or_none()

    async def create(self, data: dict) -> T:
        # copy only columns present on the model to avoid passing extra keys (eg email/password)
        cols = {c.key for c in self._model_class.__table__.columns}
        filtered = {k: v for k, v in dict(data).items() if k in cols}
        filtered["tenant_id"] = self._tenant_id
        entity = self._model_class(**filtered)
        self._session.add(entity)
        await self._session.commit()
        await self._session.refresh(entity)
        return entity

    async def update(self, id: uuid.UUID, data: dict) -> T | None:
        entity = await self.get(id)
        if entity is None:
            return None
        for key, value in data.items():
            setattr(entity, key, value)
        await self._session.commit()
        await self._session.refresh(entity)
        return entity

    async def soft_delete(self, id: uuid.UUID) -> bool:
        entity = await self.get(id)
        if entity is None:
            return False
        entity.deleted_at = datetime.now(UTC)
        await self._session.commit()
        return True

    def with_deleted(self) -> Self:
        new = copy.copy(self)
        new._include_deleted = True
        new._only_deleted = False
        return new

    def only_deleted(self) -> Self:
        new = copy.copy(self)
        new._include_deleted = True
        new._only_deleted = True
        return new

    def _apply_soft_delete_filter(self, query):
        if self._only_deleted:
            query = query.where(self._model_class.deleted_at.isnot(None))
        elif not self._include_deleted:
            query = query.where(self._model_class.deleted_at.is_(None))
        return query
