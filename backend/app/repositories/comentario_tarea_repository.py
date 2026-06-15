import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.comentario_tarea import ComentarioTarea


class ComentarioTareaRepository:
    def __init__(self, session: AsyncSession, tenant_id: uuid.UUID):
        self._session = session
        self._tenant_id = tenant_id

    async def create(self, comentario: ComentarioTarea) -> ComentarioTarea:
        self._session.add(comentario)
        await self._session.flush()
        await self._session.refresh(comentario, ["autor"])
        return comentario

    async def list_by_tarea(
        self, tarea_id: uuid.UUID, tenant_id: uuid.UUID,
    ) -> list[ComentarioTarea]:
        query = (
            select(ComentarioTarea)
            .options(selectinload(ComentarioTarea.autor))
            .where(
                ComentarioTarea.tarea_id == tarea_id,
                ComentarioTarea.tenant_id == tenant_id,
                ComentarioTarea.deleted_at.is_(None),
            )
            .order_by(ComentarioTarea.creado_at.asc())
        )
        result = await self._session.execute(query)
        return list(result.scalars().all())
