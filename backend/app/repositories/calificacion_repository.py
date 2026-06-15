from uuid import UUID

from sqlalchemy import func, select

from app.models.calificacion import Calificacion
from app.repositories.base import BaseRepository


class CalificacionRepository(BaseRepository[Calificacion]):
    def __init__(self, session, tenant_id):
        super().__init__(session, tenant_id, Calificacion)

    async def bulk_create(self, calificaciones: list[dict]) -> list[Calificacion]:
        entities = []
        for data in calificaciones:
            data["tenant_id"] = self._tenant_id
            c = Calificacion(**data)
            self._session.add(c)
            entities.append(c)
        await self._session.commit()
        for c in entities:
            await self._session.refresh(c)
        return entities

    async def get_by_materia_y_cohorte(
        self,
        materia_id: UUID,
        cohorte_id: UUID,
        cargado_por: UUID | None = None,
        offset: int = 0,
        limit: int = 100,
    ) -> tuple[list[Calificacion], int]:
        query = select(Calificacion).where(
            Calificacion.tenant_id == self._tenant_id,
            Calificacion.materia_id == materia_id,
            Calificacion.cohorte_id == cohorte_id,
            Calificacion.deleted_at.is_(None),
        )
        if cargado_por:
            query = query.where(Calificacion.cargado_por == cargado_por)

        count_query = select(func.count()).select_from(query.subquery())
        total = await self._session.scalar(count_query)

        query = query.order_by(Calificacion.created_at.desc()).offset(offset).limit(limit)
        result = await self._session.execute(query)
        items = list(result.scalars().all())
        return items, total

    async def get_by_entrada_padron(self, entrada_padron_id: UUID, actividad: str) -> Calificacion | None:
        query = select(Calificacion).where(
            Calificacion.tenant_id == self._tenant_id,
            Calificacion.entrada_padron_id == entrada_padron_id,
            Calificacion.actividad == actividad,
            Calificacion.deleted_at.is_(None),
        )
        result = await self._session.execute(query)
        return result.scalar_one_or_none()

    async def count_by_actividad(
        self,
        materia_id: UUID,
        cohorte_id: UUID,
        actividad: str,
    ) -> int:
        query = select(func.count()).select_from(Calificacion).where(
            Calificacion.tenant_id == self._tenant_id,
            Calificacion.materia_id == materia_id,
            Calificacion.cohorte_id == cohorte_id,
            Calificacion.actividad == actividad,
            Calificacion.deleted_at.is_(None),
        )
        result = await self._session.execute(query)
        return result.scalar_one()
