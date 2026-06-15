from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.guardia import Guardia


class GuardiaRepository:
    def __init__(self, session: AsyncSession, tenant_id: UUID):
        self._session = session
        self._tenant_id = tenant_id

    async def create(self, guardia: Guardia) -> Guardia:
        self._session.add(guardia)
        await self._session.flush()
        return guardia

    async def get_by_id(self, guardia_id: UUID, tenant_id: UUID) -> Guardia | None:
        query = select(Guardia).where(
            Guardia.id == guardia_id,
            Guardia.tenant_id == tenant_id,
            Guardia.deleted_at.is_(None),
        )
        result = await self._session.execute(query)
        return result.scalar_one_or_none()

    async def update(
        self, guardia_id: UUID, tenant_id: UUID, **kwargs
    ) -> Guardia | None:
        guardia = await self.get_by_id(guardia_id, tenant_id)
        if guardia is None:
            return None
        for key, value in kwargs.items():
            if value is not None:
                setattr(guardia, key, value)
        return guardia

    async def list_by_filters(
        self,
        tenant_id: UUID,
        materia_id: UUID | None = None,
        carrera_id: UUID | None = None,
        cohorte_id: UUID | None = None,
        dia: str | None = None,
        estado: str | None = None,
        asignacion_id: UUID | None = None,
        offset: int = 0,
        limit: int = 20,
    ) -> tuple[list[Guardia], int]:
        base = select(Guardia).where(
            Guardia.tenant_id == tenant_id,
            Guardia.deleted_at.is_(None),
        )
        if materia_id:
            base = base.where(Guardia.materia_id == materia_id)
        if carrera_id:
            base = base.where(Guardia.carrera_id == carrera_id)
        if cohorte_id:
            base = base.where(Guardia.cohorte_id == cohorte_id)
        if dia:
            base = base.where(Guardia.dia == dia)
        if estado:
            base = base.where(Guardia.estado == estado)
        if asignacion_id:
            base = base.where(Guardia.asignacion_id == asignacion_id)

        count_q = select(func.count()).select_from(base.subquery())
        total = (await self._session.execute(count_q)).scalar_one()

        items_q = base.offset(offset).limit(limit).order_by(Guardia.creada_at.desc())
        result = await self._session.execute(items_q)
        return list(result.scalars().all()), total

    async def list_for_export(
        self,
        tenant_id: UUID,
        materia_id: UUID | None = None,
        carrera_id: UUID | None = None,
        cohorte_id: UUID | None = None,
        dia: str | None = None,
        estado: str | None = None,
        asignacion_id: UUID | None = None,
    ) -> list[Guardia]:
        query = select(Guardia).where(
            Guardia.tenant_id == tenant_id,
            Guardia.deleted_at.is_(None),
        )
        if materia_id:
            query = query.where(Guardia.materia_id == materia_id)
        if carrera_id:
            query = query.where(Guardia.carrera_id == carrera_id)
        if cohorte_id:
            query = query.where(Guardia.cohorte_id == cohorte_id)
        if dia:
            query = query.where(Guardia.dia == dia)
        if estado:
            query = query.where(Guardia.estado == estado)
        if asignacion_id:
            query = query.where(Guardia.asignacion_id == asignacion_id)

        query = query.order_by(Guardia.creada_at.desc())
        result = await self._session.execute(query)
        return list(result.scalars().all())
