from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import func, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.audit_log import AuditLog
from app.models.auth_user import AuthUser
from app.models.materia import Materia
from app.models.usuario import Usuario


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

    async def count_by_day(
        self,
        *,
        fecha_desde: datetime,
        fecha_hasta: datetime,
        actor_id: uuid.UUID | None = None,
    ) -> list[dict]:
        query = (
            select(
                func.date(AuditLog.fecha_hora).label("dia"),
                func.count().label("total_acciones"),
            )
            .where(AuditLog.tenant_id == self._tenant_id)
            .where(AuditLog.fecha_hora >= fecha_desde)
            .where(AuditLog.fecha_hora <= fecha_hasta)
        )

        if actor_id is not None:
            query = query.where(AuditLog.actor_id == actor_id)

        query = query.group_by(func.date(AuditLog.fecha_hora))
        query = query.order_by(text("dia ASC"))

        result = await self._session.execute(query)
        return [{"dia": row.dia, "total_acciones": row.total_acciones} for row in result.all()]

    async def count_by_actor_materia_accion(
        self,
        *,
        fecha_desde: datetime,
        fecha_hasta: datetime,
        actor_id: uuid.UUID | None = None,
    ) -> list[dict]:
        query = (
            select(
                AuditLog.actor_id,
                AuditLog.materia_id,
                AuditLog.accion,
                func.count().label("cantidad"),
            )
            .where(AuditLog.tenant_id == self._tenant_id)
            .where(AuditLog.fecha_hora >= fecha_desde)
            .where(AuditLog.fecha_hora <= fecha_hasta)
        )

        if actor_id is not None:
            query = query.where(AuditLog.actor_id == actor_id)

        query = query.group_by(
            AuditLog.actor_id,
            AuditLog.materia_id,
            AuditLog.accion,
        )
        query = query.order_by(text("cantidad DESC"))

        result = await self._session.execute(query)
        return [
            {
                "actor_id": row.actor_id,
                "materia_id": row.materia_id,
                "accion": row.accion,
                "cantidad": row.cantidad,
            }
            for row in result.all()
        ]

    async def list_with_join(
        self,
        *,
        accion: str | None = None,
        fecha_desde: datetime | None = None,
        fecha_hasta: datetime | None = None,
        usuario_id: uuid.UUID | None = None,
        materia_id: uuid.UUID | None = None,
        ip: str | None = None,
        offset: int = 0,
        limit: int = 50,
    ) -> list[dict]:
        query = (
            select(
                AuditLog.id,
                AuditLog.fecha_hora,
                AuditLog.actor_id,
                (Usuario.nombre + " " + Usuario.apellidos).label("actor_nombre"),
                AuditLog.materia_id,
                Materia.nombre.label("materia_nombre"),
                AuditLog.accion,
                AuditLog.detalle,
                AuditLog.filas_afectadas,
                AuditLog.ip,
                AuditLog.user_agent,
            )
            .select_from(AuditLog)
            .outerjoin(
                AuthUser,
                (AuditLog.actor_id == AuthUser.id) & (AuthUser.deleted_at.is_(None)),
            )
            .outerjoin(
                Usuario,
                (AuthUser.id == Usuario.id) & (Usuario.deleted_at.is_(None)),
            )
            .outerjoin(
                Materia,
                (AuditLog.materia_id == Materia.id) & (Materia.deleted_at.is_(None)),
            )
            .where(AuditLog.tenant_id == self._tenant_id)
        )

        if accion is not None:
            query = query.where(AuditLog.accion == accion)
        if fecha_desde is not None:
            query = query.where(AuditLog.fecha_hora >= fecha_desde)
        if fecha_hasta is not None:
            query = query.where(AuditLog.fecha_hora <= fecha_hasta)
        if usuario_id is not None:
            query = query.where(AuditLog.actor_id == usuario_id)
        if materia_id is not None:
            query = query.where(AuditLog.materia_id == materia_id)
        if ip is not None:
            query = query.where(AuditLog.ip.like(f"%{ip}%"))

        query = query.order_by(AuditLog.fecha_hora.desc())
        query = query.offset(offset).limit(limit)

        result = await self._session.execute(query)
        return [
            {
                "id": row.id,
                "fecha_hora": row.fecha_hora,
                "actor_id": row.actor_id,
                "actor_nombre": row.actor_nombre,
                "materia_id": row.materia_id,
                "materia_nombre": row.materia_nombre,
                "accion": row.accion,
                "detalle": row.detalle,
                "filas_afectadas": row.filas_afectadas,
                "ip": row.ip,
                "user_agent": row.user_agent,
            }
            for row in result.all()
        ]

    async def count_with_filters(
        self,
        *,
        accion: str | None = None,
        fecha_desde: datetime | None = None,
        fecha_hasta: datetime | None = None,
        usuario_id: uuid.UUID | None = None,
        materia_id: uuid.UUID | None = None,
        ip: str | None = None,
    ) -> int:
        query = select(func.count(AuditLog.id)).where(
            AuditLog.tenant_id == self._tenant_id,
        )

        if accion is not None:
            query = query.where(AuditLog.accion == accion)
        if fecha_desde is not None:
            query = query.where(AuditLog.fecha_hora >= fecha_desde)
        if fecha_hasta is not None:
            query = query.where(AuditLog.fecha_hora <= fecha_hasta)
        if usuario_id is not None:
            query = query.where(AuditLog.actor_id == usuario_id)
        if materia_id is not None:
            query = query.where(AuditLog.materia_id == materia_id)
        if ip is not None:
            query = query.where(AuditLog.ip.like(f"%{ip}%"))

        result = await self._session.execute(query)
        return result.scalar_one()

    async def find_by_id(self, id: uuid.UUID) -> AuditLog | None:
        query = select(AuditLog).where(
            AuditLog.id == id,
            AuditLog.tenant_id == self._tenant_id,
        )
        result = await self._session.execute(query)
        return result.scalar_one_or_none()
