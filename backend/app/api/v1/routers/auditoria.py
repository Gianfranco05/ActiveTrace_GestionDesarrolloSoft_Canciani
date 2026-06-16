import uuid
from datetime import date, datetime

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import (
    UserSession,
    get_db,
    require_permission_return_user,
)
from app.repositories.audit_repository import AuditLogRepository
from app.schemas.auditoria import (
    AuditoriaLogListResponse,
    AuditoriaLogResponse,
)
from app.services.auditoria.metrics_service import MetricsService

router = APIRouter(prefix="/api/auditoria", tags=["auditoria"])

# TODO: when RBAC supports scope attributes, refactor is_global_scope
# to query permiso.scope instead of checking role names.
GLOBAL_SCOPE_ROLES = {"ADMIN", "FINANZAS"}


def _is_global_scope(current_user: UserSession) -> bool:
    return bool(set(current_user.roles) & GLOBAL_SCOPE_ROLES)


def _build_service(db: AsyncSession, current_user: UserSession) -> MetricsService:
    return MetricsService(
        session=db,
        tenant_id=current_user.tenant_id,
        user_id=current_user.user_id,
        is_global_scope=_is_global_scope(current_user),
    )


@router.get("/panel/acciones-por-dia")
async def panel_acciones_por_dia(
    fecha_desde: date | None = Query(None),
    fecha_hasta: date | None = Query(None),
    current_user: UserSession = Depends(require_permission_return_user("auditoria:ver")),
    db: AsyncSession = Depends(get_db),
):
    service = _build_service(db, current_user)
    return await service.acciones_por_dia(fecha_desde=fecha_desde, fecha_hasta=fecha_hasta)


@router.get("/panel/estado-comunicaciones")
async def panel_estado_comunicaciones(
    fecha_desde: date | None = Query(None),
    fecha_hasta: date | None = Query(None),
    materia_id: uuid.UUID | None = Query(None),
    current_user: UserSession = Depends(require_permission_return_user("auditoria:ver")),
    db: AsyncSession = Depends(get_db),
):
    service = _build_service(db, current_user)
    return await service.estado_comunicaciones_por_docente(
        fecha_desde=fecha_desde, fecha_hasta=fecha_hasta, materia_id=materia_id,
    )


@router.get("/panel/interacciones")
async def panel_interacciones(
    fecha_desde: date | None = Query(None),
    fecha_hasta: date | None = Query(None),
    usuario_id: uuid.UUID | None = Query(None),
    current_user: UserSession = Depends(require_permission_return_user("auditoria:ver")),
    db: AsyncSession = Depends(get_db),
):
    service = _build_service(db, current_user)
    return await service.interacciones_por_docente_materia(
        fecha_desde=fecha_desde, fecha_hasta=fecha_hasta, usuario_id=usuario_id,
    )


@router.get("/panel/ultimas-acciones")
async def panel_ultimas_acciones(
    limit: int = Query(200, ge=1, le=1000),
    fecha_desde: date | None = Query(None),
    fecha_hasta: date | None = Query(None),
    usuario_id: uuid.UUID | None = Query(None),
    materia_id: uuid.UUID | None = Query(None),
    current_user: UserSession = Depends(require_permission_return_user("auditoria:ver")),
    db: AsyncSession = Depends(get_db),
):
    service = _build_service(db, current_user)
    return await service.ultimas_acciones(
        limit=limit,
        fecha_desde=fecha_desde,
        fecha_hasta=fecha_hasta,
        usuario_id=usuario_id,
        materia_id=materia_id,
    )


@router.get("/log")
async def auditoria_log(
    accion: str | None = Query(None),
    fecha_desde: datetime | None = Query(None),
    fecha_hasta: datetime | None = Query(None),
    usuario_id: uuid.UUID | None = Query(None),
    materia_id: uuid.UUID | None = Query(None),
    ip: str | None = Query(None),
    offset: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    current_user: UserSession = Depends(require_permission_return_user("auditoria:ver")),
    db: AsyncSession = Depends(get_db),
):
    # TODO: when RBAC supports scope attributes, refactor is_global_scope
    # to query permiso.scope instead of checking role names.
    is_global = _is_global_scope(current_user)

    effective_usuario_id = usuario_id
    if not is_global:
        effective_usuario_id = current_user.user_id

    repo = AuditLogRepository(db, current_user.tenant_id)
    items = await repo.list_with_join(
        accion=accion,
        fecha_desde=fecha_desde,
        fecha_hasta=fecha_hasta,
        usuario_id=effective_usuario_id,
        materia_id=materia_id,
        ip=ip,
        offset=offset,
        limit=limit,
    )
    total = await repo.count_with_filters(
        accion=accion,
        fecha_desde=fecha_desde,
        fecha_hasta=fecha_hasta,
        usuario_id=effective_usuario_id,
        materia_id=materia_id,
        ip=ip,
    )
    return AuditoriaLogListResponse(
        items=[AuditoriaLogResponse(**item) for item in items],
        total=total,
        offset=offset,
        limit=limit,
    )
