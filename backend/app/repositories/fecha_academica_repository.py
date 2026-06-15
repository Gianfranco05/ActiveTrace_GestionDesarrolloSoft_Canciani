import uuid
from datetime import date

from sqlalchemy import func, select

from app.models.fecha_academica import FechaAcademica
from app.repositories.base import BaseRepository


class FechaAcademicaRepository(BaseRepository[FechaAcademica]):
    def __init__(self, session, tenant_id: uuid.UUID) -> None:
        super().__init__(session, tenant_id, FechaAcademica)

    async def get_by_id(self, id: uuid.UUID, tenant_id: uuid.UUID) -> FechaAcademica | None:
        return await self.get(id)

    async def list_by_filters(
        self,
        tenant_id: uuid.UUID,
        *,
        materia_id: uuid.UUID | None = None,
        cohorte_id: uuid.UUID | None = None,
        tipo: str | None = None,
        periodo: str | None = None,
        offset: int = 0,
        limit: int = 20,
    ) -> tuple[list[FechaAcademica], int]:
        query = select(FechaAcademica).where(
            FechaAcademica.tenant_id == tenant_id,
        )
        query = self._apply_soft_delete_filter(query)

        if materia_id is not None:
            query = query.where(FechaAcademica.materia_id == materia_id)
        if cohorte_id is not None:
            query = query.where(FechaAcademica.cohorte_id == cohorte_id)
        if tipo is not None:
            query = query.where(FechaAcademica.tipo == tipo)
        if periodo is not None:
            query = query.where(FechaAcademica.periodo == periodo)

        count_query = select(func.count()).select_from(query.subquery())
        count_result = await self._session.execute(count_query)
        total = count_result.scalar_one()

        query = query.order_by(FechaAcademica.fecha.asc()).offset(offset).limit(limit)
        result = await self._session.execute(query)
        items = list(result.scalars().all())

        return items, total

    async def get_calendario(
        self,
        tenant_id: uuid.UUID,
        *,
        materia_id: uuid.UUID | None = None,
        cohorte_id: uuid.UUID | None = None,
        periodo: str | None = None,
        fecha_desde: date | None = None,
        fecha_hasta: date | None = None,
    ) -> list[FechaAcademica]:
        query = select(FechaAcademica).where(
            FechaAcademica.tenant_id == tenant_id,
        )
        query = self._apply_soft_delete_filter(query)

        if materia_id is not None:
            query = query.where(FechaAcademica.materia_id == materia_id)
        if cohorte_id is not None:
            query = query.where(FechaAcademica.cohorte_id == cohorte_id)
        if periodo is not None:
            query = query.where(FechaAcademica.periodo == periodo)
        if fecha_desde is not None:
            query = query.where(FechaAcademica.fecha >= fecha_desde)
        if fecha_hasta is not None:
            query = query.where(FechaAcademica.fecha <= fecha_hasta)

        query = query.order_by(FechaAcademica.fecha.asc())
        result = await self._session.execute(query)
        return list(result.scalars().all())

    async def update(
        self, id: uuid.UUID, tenant_id: uuid.UUID, **fields,
    ) -> FechaAcademica | None:
        return await super().update(id, fields)

    async def soft_delete(self, id: uuid.UUID, tenant_id: uuid.UUID) -> bool:
        return await super().soft_delete(id)
