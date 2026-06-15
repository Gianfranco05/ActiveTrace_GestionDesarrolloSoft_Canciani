import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.comentario_tarea import ComentarioTarea
from app.models.tarea import Tarea


class TareaRepository:
    def __init__(self, session: AsyncSession, tenant_id: uuid.UUID):
        self._session = session
        self._tenant_id = tenant_id

    async def create(self, tarea: Tarea) -> Tarea:
        self._session.add(tarea)
        await self._session.flush()
        return tarea

    async def get_by_id(
        self, tarea_id: uuid.UUID, tenant_id: uuid.UUID,
    ) -> Tarea | None:
        query = (
            select(Tarea)
            .options(
                selectinload(Tarea.asignado_a_usuario),
                selectinload(Tarea.asignado_por_usuario),
                selectinload(Tarea.materia),
                selectinload(Tarea.comentarios).selectinload(ComentarioTarea.autor),
            )
            .where(
                Tarea.id == tarea_id,
                Tarea.tenant_id == tenant_id,
                Tarea.deleted_at.is_(None),
            )
        )
        result = await self._session.execute(
            query.execution_options(populate_existing=True),
        )
        return result.scalar_one_or_none()

    async def update(
        self, tarea_id: uuid.UUID, tenant_id: uuid.UUID, **kwargs,
    ) -> Tarea | None:
        tarea = await self.get_by_id(tarea_id, tenant_id)
        if tarea is None:
            return None
        for key, value in kwargs.items():
            if value is not None:
                setattr(tarea, key, value)
        return tarea

    async def get_for_update(
        self, tarea_id: uuid.UUID, tenant_id: uuid.UUID,
    ) -> Tarea | None:
        query = (
            select(Tarea)
            .options(
                selectinload(Tarea.asignado_a_usuario),
                selectinload(Tarea.asignado_por_usuario),
                selectinload(Tarea.materia),
            )
            .where(
                Tarea.id == tarea_id,
                Tarea.tenant_id == tenant_id,
                Tarea.deleted_at.is_(None),
            )
            .with_for_update()
        )
        result = await self._session.execute(query)
        return result.scalar_one_or_none()

    async def list_by_filters(
        self,
        tenant_id: uuid.UUID,
        asignado_a: uuid.UUID | None = None,
        asignado_por: uuid.UUID | None = None,
        materia_id: uuid.UUID | None = None,
        estado: str | None = None,
        contexto_id: uuid.UUID | None = None,
        q: str | None = None,
        offset: int = 0,
        limit: int = 20,
    ) -> tuple[list[Tarea], int]:

        base = (
            select(Tarea)
            .options(
                selectinload(Tarea.asignado_a_usuario),
                selectinload(Tarea.asignado_por_usuario),
                selectinload(Tarea.materia),
            )
            .where(
                Tarea.tenant_id == tenant_id,
                Tarea.deleted_at.is_(None),
            )
        )
        if asignado_a:
            base = base.where(Tarea.asignado_a == asignado_a)
        if asignado_por:
            base = base.where(Tarea.asignado_por == asignado_por)
        if materia_id:
            base = base.where(Tarea.materia_id == materia_id)
        if estado:
            base = base.where(Tarea.estado == estado)
        if contexto_id:
            base = base.where(Tarea.contexto_id == contexto_id)
        if q:
            base = base.where(Tarea.descripcion.ilike(f"%{q}%"))

        count_q = select(func.count()).select_from(base.subquery())
        total = (await self._session.execute(count_q)).scalar_one()

        items_q = base.offset(offset).limit(limit).order_by(Tarea.created_at.desc())
        result = await self._session.execute(items_q)
        return list(result.scalars().all()), total
