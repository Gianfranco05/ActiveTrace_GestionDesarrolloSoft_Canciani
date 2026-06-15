import uuid

from sqlalchemy import func, select

from app.models.programa_materia import ProgramaMateria
from app.repositories.base import BaseRepository


class ProgramaMateriaRepository(BaseRepository[ProgramaMateria]):
    def __init__(self, session, tenant_id: uuid.UUID) -> None:
        super().__init__(session, tenant_id, ProgramaMateria)

    async def get_by_id(self, id: uuid.UUID, tenant_id: uuid.UUID) -> ProgramaMateria | None:
        return await self.get(id)

    async def list_by_filters(
        self,
        tenant_id: uuid.UUID,
        *,
        materia_id: uuid.UUID | None = None,
        carrera_id: uuid.UUID | None = None,
        cohorte_id: uuid.UUID | None = None,
        offset: int = 0,
        limit: int = 20,
    ) -> tuple[list[ProgramaMateria], int]:
        query = select(ProgramaMateria).where(
            ProgramaMateria.tenant_id == tenant_id,
        )
        query = self._apply_soft_delete_filter(query)

        if materia_id is not None:
            query = query.where(ProgramaMateria.materia_id == materia_id)
        if carrera_id is not None:
            query = query.where(ProgramaMateria.carrera_id == carrera_id)
        if cohorte_id is not None:
            query = query.where(ProgramaMateria.cohorte_id == cohorte_id)

        count_query = select(func.count()).select_from(query.subquery())
        count_result = await self._session.execute(count_query)
        total = count_result.scalar_one()

        query = query.offset(offset).limit(limit)
        result = await self._session.execute(query)
        items = list(result.scalars().all())

        return items, total

    async def soft_delete(self, id: uuid.UUID, tenant_id: uuid.UUID) -> bool:
        return await super().soft_delete(id)
