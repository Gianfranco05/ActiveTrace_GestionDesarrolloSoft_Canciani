from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.instancia_encuentro import InstanciaEncuentro


class InstanciaEncuentroRepository:
    def __init__(self, session: AsyncSession, tenant_id: UUID):
        self._session = session
        self._tenant_id = tenant_id

    async def create(self, instancia: InstanciaEncuentro) -> InstanciaEncuentro:
        self._session.add(instancia)
        await self._session.flush()
        return instancia

    async def bulk_create(self, instancias: list[InstanciaEncuentro]) -> list[InstanciaEncuentro]:
        for i in instancias:
            self._session.add(i)
        await self._session.flush()
        return instancias

    async def get_by_id(
        self, instancia_id: UUID, tenant_id: UUID
    ) -> InstanciaEncuentro | None:
        query = select(InstanciaEncuentro).where(
            InstanciaEncuentro.id == instancia_id,
            InstanciaEncuentro.tenant_id == tenant_id,
            InstanciaEncuentro.deleted_at.is_(None),
        )
        result = await self._session.execute(query)
        return result.scalar_one_or_none()

    async def update(
        self, instancia_id: UUID, tenant_id: UUID, **kwargs
    ) -> InstanciaEncuentro | None:
        instancia = await self.get_by_id(instancia_id, tenant_id)
        if instancia is None:
            return None
        for key, value in kwargs.items():
            if value is not None:
                setattr(instancia, key, value)
        return instancia

    async def list_by_slot(
        self, slot_id: UUID, tenant_id: UUID
    ) -> list[InstanciaEncuentro]:
        query = select(InstanciaEncuentro).where(
            InstanciaEncuentro.slot_id == slot_id,
            InstanciaEncuentro.tenant_id == tenant_id,
            InstanciaEncuentro.deleted_at.is_(None),
        ).order_by(InstanciaEncuentro.fecha)
        result = await self._session.execute(query)
        return list(result.scalars().all())

    async def list_by_filters(
        self,
        tenant_id: UUID,
        materia_id: UUID | None = None,
        slot_id: UUID | None = None,
        estado: str | None = None,
        asignacion_id: UUID | None = None,
        offset: int = 0,
        limit: int = 20,
    ) -> tuple[list[InstanciaEncuentro], int]:
        base = select(InstanciaEncuentro).where(
            InstanciaEncuentro.tenant_id == tenant_id,
            InstanciaEncuentro.deleted_at.is_(None),
        )
        if materia_id:
            base = base.where(InstanciaEncuentro.materia_id == materia_id)
        if slot_id:
            base = base.where(InstanciaEncuentro.slot_id == slot_id)
        if estado:
            base = base.where(InstanciaEncuentro.estado == estado)
        if asignacion_id:
            base = base.where(InstanciaEncuentro.asignacion_id == asignacion_id)

        count_q = select(func.count()).select_from(base.subquery())
        total = (await self._session.execute(count_q)).scalar_one()

        items_q = base.offset(offset).limit(limit).order_by(InstanciaEncuentro.fecha)
        result = await self._session.execute(items_q)
        return list(result.scalars().all()), total

    async def list_by_asignacion(
        self, asignacion_id: UUID, tenant_id: UUID
    ) -> list[InstanciaEncuentro]:
        query = select(InstanciaEncuentro).where(
            InstanciaEncuentro.asignacion_id == asignacion_id,
            InstanciaEncuentro.tenant_id == tenant_id,
            InstanciaEncuentro.deleted_at.is_(None),
        ).order_by(InstanciaEncuentro.fecha)
        result = await self._session.execute(query)
        return list(result.scalars().all())
