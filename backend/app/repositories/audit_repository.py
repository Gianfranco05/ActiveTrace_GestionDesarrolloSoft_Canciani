import uuid
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.audit_log import AuditLog


class AuditLogRepository:

    def __init__(self, session: AsyncSession, tenant_id: uuid.UUID) -> None:
        self._session = session
        self._tenant_id = tenant_id

    async def create(self, audit_log: AuditLog) -> AuditLog:
        self._session.add(audit_log)
        await self._session.commit()
        await self._session.refresh(audit_log)
        return audit_log

    async def list(
        self,
        *,
        accion: str | None = None,
        actor_id: uuid.UUID | None = None,
        fecha_desde: datetime | None = None,
        fecha_hasta: datetime | None = None,
        materia_id: uuid.UUID | None = None,
        impersonado_id: uuid.UUID | None = None,
        offset: int = 0,
        limit: int = 50,
    ) -> list[AuditLog]:
        query = select(AuditLog).where(AuditLog.tenant_id == self._tenant_id)

        if accion is not None:
            query = query.where(AuditLog.accion == accion)
        if actor_id is not None:
            query = query.where(AuditLog.actor_id == actor_id)
        if fecha_desde is not None:
            query = query.where(AuditLog.fecha_hora >= fecha_desde)
        if fecha_hasta is not None:
            query = query.where(AuditLog.fecha_hora <= fecha_hasta)
        if materia_id is not None:
            query = query.where(AuditLog.materia_id == materia_id)
        if impersonado_id is not None:
            query = query.where(AuditLog.impersonado_id == impersonado_id)

        query = query.order_by(AuditLog.fecha_hora.desc())
        query = query.offset(offset).limit(limit)
        result = await self._session.execute(query)
        return list(result.scalars().all())

    async def count(
        self,
        *,
        accion: str | None = None,
        actor_id: uuid.UUID | None = None,
        fecha_desde: datetime | None = None,
        fecha_hasta: datetime | None = None,
        materia_id: uuid.UUID | None = None,
        impersonado_id: uuid.UUID | None = None,
    ) -> int:
        from sqlalchemy import func

        query = select(func.count(AuditLog.id)).where(
            AuditLog.tenant_id == self._tenant_id,
        )

        if accion is not None:
            query = query.where(AuditLog.accion == accion)
        if actor_id is not None:
            query = query.where(AuditLog.actor_id == actor_id)
        if fecha_desde is not None:
            query = query.where(AuditLog.fecha_hora >= fecha_desde)
        if fecha_hasta is not None:
            query = query.where(AuditLog.fecha_hora <= fecha_hasta)
        if materia_id is not None:
            query = query.where(AuditLog.materia_id == materia_id)
        if impersonado_id is not None:
            query = query.where(AuditLog.impersonado_id == impersonado_id)

        result = await self._session.execute(query)
        return result.scalar_one()

    async def find_by_id(self, id: uuid.UUID) -> AuditLog | None:
        query = select(AuditLog).where(
            AuditLog.id == id,
            AuditLog.tenant_id == self._tenant_id,
        )
        result = await self._session.execute(query)
        return result.scalar_one_or_none()
