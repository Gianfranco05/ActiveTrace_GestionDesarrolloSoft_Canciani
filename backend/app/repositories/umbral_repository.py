from uuid import UUID

from sqlalchemy import select

from app.models.calificacion import UmbralMateria
from app.repositories.base import BaseRepository


class UmbralRepository(BaseRepository[UmbralMateria]):
    def __init__(self, session, tenant_id):
        super().__init__(session, tenant_id, UmbralMateria)

    async def get_by_materia(self, materia_id: UUID) -> UmbralMateria | None:
        query = select(UmbralMateria).where(
            UmbralMateria.tenant_id == self._tenant_id,
            UmbralMateria.materia_id == materia_id,
            UmbralMateria.deleted_at.is_(None),
        )
        result = await self._session.execute(query)
        return result.scalar_one_or_none()

    async def upsert(self, materia_id: UUID, data: dict) -> UmbralMateria:
        existing = await self.get_by_materia(materia_id)
        if existing:
            for key, value in data.items():
                setattr(existing, key, value)
            await self._session.commit()
            await self._session.refresh(existing)
            return existing
        data["materia_id"] = materia_id
        return await self.create(data)
