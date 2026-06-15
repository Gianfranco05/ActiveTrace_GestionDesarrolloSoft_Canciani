from __future__ import annotations

import uuid
from datetime import UTC, date, datetime, timedelta

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.auth_user import AuthUser
from app.models.materia import Materia
from app.models.usuario import Usuario
from app.repositories.audit_repository import AuditLogRepository
from app.schemas.auditoria import (
    AccionesPorDiaResponse,
    AccionPorDia,
    EstadoComunicacionesResponse,
    EstadoPorDocente,
    InteraccionesResponse,
    InteraccionRow,
    UltimaAccionResponse,
    UltimasAccionesResponse,
)

DEFAULT_ULTIMAS_ACCIONES_LIMIT = 200
MAX_ULTIMAS_ACCIONES_LIMIT = 1000


class MetricsService:

    def __init__(
        self,
        session: AsyncSession,
        tenant_id: uuid.UUID,
        user_id: uuid.UUID,
        is_global_scope: bool,
    ) -> None:
        self._session = session
        self._tenant_id = tenant_id
        self._user_id = user_id
        self._is_global_scope = is_global_scope
        self._audit_repo = AuditLogRepository(session, tenant_id)

    async def acciones_por_dia(
        self,
        fecha_desde: date | None = None,
        fecha_hasta: date | None = None,
    ) -> AccionesPorDiaResponse:
        if fecha_desde is None:
            fecha_desde = date.today() - timedelta(days=30)
        if fecha_hasta is None:
            fecha_hasta = date.today()

        desde_dt = datetime.combine(fecha_desde, datetime.min.time(), tzinfo=UTC)
        hasta_dt = datetime.combine(fecha_hasta, datetime.max.time(), tzinfo=UTC).replace(microsecond=0)

        actor_id = None if self._is_global_scope else self._user_id

        rows = await self._audit_repo.count_by_day(
            fecha_desde=desde_dt,
            fecha_hasta=hasta_dt,
            actor_id=actor_id,
        )

        items = [AccionPorDia(dia=r["dia"], total_acciones=r["total_acciones"]) for r in rows]
        return AccionesPorDiaResponse(items=items, desde=fecha_desde, hasta=fecha_hasta)

    async def estado_comunicaciones_por_docente(
        self,
        fecha_desde: date | None = None,
        fecha_hasta: date | None = None,
        materia_id: uuid.UUID | None = None,
    ) -> EstadoComunicacionesResponse:
        if fecha_desde is None:
            fecha_desde = date.today() - timedelta(days=30)
        if fecha_hasta is None:
            fecha_hasta = date.today()

        # TODO: when RBAC supports scope attributes, refactor is_global_scope
        # to query permiso.scope instead of deriving from role names.
        try:
            mod = __import__("app.models.comunicacion", fromlist=["Comunicacion"])
            comunicacion_model = getattr(mod, "Comunicacion", None)
            if comunicacion_model is None:
                return EstadoComunicacionesResponse(items=[])
        except ImportError:
            return EstadoComunicacionesResponse(items=[])

        desde_dt = datetime.combine(fecha_desde, datetime.min.time(), tzinfo=UTC)
        hasta_dt = datetime.combine(fecha_hasta, datetime.max.time(), tzinfo=UTC).replace(microsecond=0)

        query = (
            select(
                comunicacion_model.enviado_por.label("usuario_id"),
                comunicacion_model.materia_id,
                comunicacion_model.estado,
                func.count().label("cantidad"),
            )
            .where(comunicacion_model.tenant_id == self._tenant_id)
            .where(comunicacion_model.created_at >= desde_dt)
            .where(comunicacion_model.created_at <= hasta_dt)
            .where(comunicacion_model.deleted_at.is_(None))
        )

        if materia_id is not None:
            query = query.where(comunicacion_model.materia_id == materia_id)

        if not self._is_global_scope:
            query = query.where(comunicacion_model.enviado_por == self._user_id)

        query = query.group_by(
            comunicacion_model.enviado_por,
            comunicacion_model.materia_id,
            comunicacion_model.estado,
        )

        result = await self._session.execute(query)
        raw_rows = result.all()

        if not raw_rows:
            return EstadoComunicacionesResponse(items=[])

        user_ids = {r.usuario_id for r in raw_rows if r.usuario_id is not None}
        materia_ids = {r.materia_id for r in raw_rows if r.materia_id is not None}

        user_names: dict[uuid.UUID, str] = {}
        if user_ids:
            user_query = (
                select(AuthUser.id, Usuario.nombre, Usuario.apellidos)
                .select_from(AuthUser)
                .outerjoin(Usuario, AuthUser.id == Usuario.id)
                .where(AuthUser.id.in_(user_ids))
            )
            user_result = await self._session.execute(user_query)
            for row in user_result.all():
                if row.nombre and row.apellidos:
                    user_names[row.id] = f"{row.nombre} {row.apellidos}"

        materia_names: dict[uuid.UUID, str] = {}
        if materia_ids:
            materia_query = select(Materia.id, Materia.nombre).where(
                Materia.id.in_(materia_ids),
                Materia.deleted_at.is_(None),
            )
            materia_result = await self._session.execute(materia_query)
            for row in materia_result.all():
                materia_names[row.id] = row.nombre

        grouped: dict[tuple, dict] = {}
        for r in raw_rows:
            key = (r.usuario_id, r.materia_id)
            if key not in grouped:
                grouped[key] = {
                    "usuario_id": r.usuario_id,
                    "usuario_nombre": user_names.get(r.usuario_id) if r.usuario_id else None,
                    "materia_id": r.materia_id,
                    "materia_nombre": materia_names.get(r.materia_id) if r.materia_id else None,
                    "pendiente": 0,
                    "enviando": 0,
                    "enviado": 0,
                    "error": 0,
                    "cancelado": 0,
                }
            estado_lower = r.estado.lower() if r.estado else ""
            if estado_lower == "pendiente":
                grouped[key]["pendiente"] += r.cantidad
            elif estado_lower == "enviando":
                grouped[key]["enviando"] += r.cantidad
            elif estado_lower == "enviado":
                grouped[key]["enviado"] += r.cantidad
            elif estado_lower == "error":
                grouped[key]["error"] += r.cantidad
            elif estado_lower == "cancelado":
                grouped[key]["cancelado"] += r.cantidad

        items = [EstadoPorDocente(**v) for v in grouped.values()]
        return EstadoComunicacionesResponse(items=items)

    async def interacciones_por_docente_materia(
        self,
        fecha_desde: date | None = None,
        fecha_hasta: date | None = None,
        usuario_id: uuid.UUID | None = None,
    ) -> InteraccionesResponse:
        if fecha_desde is None:
            fecha_desde = date.today() - timedelta(days=30)
        if fecha_hasta is None:
            fecha_hasta = date.today()

        desde_dt = datetime.combine(fecha_desde, datetime.min.time(), tzinfo=UTC)
        hasta_dt = datetime.combine(fecha_hasta, datetime.max.time(), tzinfo=UTC).replace(microsecond=0)

        actor_filter = None
        if not self._is_global_scope:
            actor_filter = self._user_id
        elif usuario_id is not None:
            actor_filter = usuario_id

        rows = await self._audit_repo.count_by_actor_materia_accion(
            fecha_desde=desde_dt,
            fecha_hasta=hasta_dt,
            actor_id=actor_filter,
        )

        if not rows:
            return InteraccionesResponse(items=[])

        user_ids = {r["actor_id"] for r in rows}
        materia_ids = {r["materia_id"] for r in rows if r["materia_id"] is not None}

        user_names: dict[uuid.UUID, str] = {}
        if user_ids:
            user_query = (
                select(AuthUser.id, Usuario.nombre, Usuario.apellidos)
                .select_from(AuthUser)
                .outerjoin(Usuario, AuthUser.id == Usuario.id)
                .where(AuthUser.id.in_(user_ids))
            )
            user_result = await self._session.execute(user_query)
            for row in user_result.all():
                if row.nombre and row.apellidos:
                    user_names[row.id] = f"{row.nombre} {row.apellidos}"

        materia_names: dict[uuid.UUID, str] = {}
        if materia_ids:
            materia_query = select(Materia.id, Materia.nombre).where(
                Materia.id.in_(materia_ids),
                Materia.deleted_at.is_(None),
            )
            materia_result = await self._session.execute(materia_query)
            for row in materia_result.all():
                materia_names[row.id] = row.nombre

        items = [
            InteraccionRow(
                usuario_id=r["actor_id"],
                usuario_nombre=user_names.get(r["actor_id"]),
                materia_id=r["materia_id"],
                materia_nombre=materia_names.get(r["materia_id"]) if r["materia_id"] else None,
                accion=r["accion"],
                cantidad=r["cantidad"],
            )
            for r in rows
        ]
        return InteraccionesResponse(items=items)

    async def ultimas_acciones(
        self,
        limit: int | None = None,
        fecha_desde: date | None = None,
        fecha_hasta: date | None = None,
        usuario_id: uuid.UUID | None = None,
        materia_id: uuid.UUID | None = None,
    ) -> UltimasAccionesResponse:
        effective_limit = min(
            limit if limit is not None else DEFAULT_ULTIMAS_ACCIONES_LIMIT,
            MAX_ULTIMAS_ACCIONES_LIMIT,
        )

        desde_dt = None
        hasta_dt = None
        if fecha_desde is not None:
            desde_dt = datetime.combine(fecha_desde, datetime.min.time(), tzinfo=UTC)
        if fecha_hasta is not None:
            hasta_dt = datetime.combine(fecha_hasta, datetime.max.time(), tzinfo=UTC).replace(microsecond=0)

        effective_usuario_id = usuario_id
        if not self._is_global_scope:
            effective_usuario_id = self._user_id

        rows = await self._audit_repo.list_with_join(
            fecha_desde=desde_dt,
            fecha_hasta=hasta_dt,
            usuario_id=effective_usuario_id,
            materia_id=materia_id,
            offset=0,
            limit=effective_limit,
        )

        items = [
            UltimaAccionResponse(
                id=r["id"],
                fecha_hora=r["fecha_hora"],
                actor_id=r["actor_id"],
                actor_nombre=r["actor_nombre"],
                materia_id=r["materia_id"],
                materia_nombre=r["materia_nombre"],
                accion=r["accion"],
                detalle=r["detalle"],
                filas_afectadas=r["filas_afectadas"],
                ip=r["ip"],
                user_agent=r["user_agent"],
            )
            for r in rows
        ]
        return UltimasAccionesResponse(items=items, max_registros=effective_limit)
