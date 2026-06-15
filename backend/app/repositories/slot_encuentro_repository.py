from datetime import UTC
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.slot_encuentro import SlotEncuentro


class SlotEncuentroRepository:
    def __init__(self, session: AsyncSession, tenant_id: UUID):
        self._session = session
        self._tenant_id = tenant_id

    async def create(self, slot: SlotEncuentro) -> SlotEncuentro:
        self._session.add(slot)
        await self._session.flush()
        return slot

    async def get_by_id(self, slot_id: UUID, tenant_id: UUID) -> SlotEncuentro | None:
        query = select(SlotEncuentro).where(
            SlotEncuentro.id == slot_id,
            SlotEncuentro.tenant_id == tenant_id,
            SlotEncuentro.deleted_at.is_(None),
        )
        result = await self._session.execute(query)
        return result.scalar_one_or_none()

    async def list_by_materia(
        self,
        materia_id: UUID,
        tenant_id: UUID,
        asignacion_id: UUID | None = None,
        offset: int = 0,
        limit: int = 20,
    ) -> tuple[list[SlotEncuentro], int]:
        base = select(SlotEncuentro).where(
            SlotEncuentro.materia_id == materia_id,
            SlotEncuentro.tenant_id == tenant_id,
            SlotEncuentro.deleted_at.is_(None),
        )
        if asignacion_id:
            base = base.where(SlotEncuentro.asignacion_id == asignacion_id)

        count_q = select(func.count()).select_from(base.subquery())
        total = (await self._session.execute(count_q)).scalar_one()

        items_q = base.offset(offset).limit(limit).order_by(SlotEncuentro.created_at.desc())
        result = await self._session.execute(items_q)
        return list(result.scalars().all()), total

    async def list_by_asignacion(
        self, asignacion_id: UUID, tenant_id: UUID
    ) -> list[SlotEncuentro]:
        query = select(SlotEncuentro).where(
            SlotEncuentro.asignacion_id == asignacion_id,
            SlotEncuentro.tenant_id == tenant_id,
            SlotEncuentro.deleted_at.is_(None),
        ).order_by(SlotEncuentro.created_at.desc())
        result = await self._session.execute(query)
        return list(result.scalars().all())

    async def soft_delete(self, slot_id: UUID, tenant_id: UUID) -> bool:
        from datetime import datetime

        query = select(SlotEncuentro).where(
            SlotEncuentro.id == slot_id,
            SlotEncuentro.tenant_id == tenant_id,
            SlotEncuentro.deleted_at.is_(None),
        )
        result = await self._session.execute(query)
        slot = result.scalar_one_or_none()
        if slot is None:
            return False
        slot.deleted_at = datetime.now(UTC)
        return True
