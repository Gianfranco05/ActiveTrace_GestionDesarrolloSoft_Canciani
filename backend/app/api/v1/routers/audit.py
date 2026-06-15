import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import (
    UserSession,
    get_db,
    require_permission_return_user,
)
from app.repositories.audit_repository import AuditLogRepository
from app.schemas.audit import AuditLogListResponse, AuditLogResponse

router = APIRouter(prefix="/api/v1/audit", tags=["audit"])


@router.get("", response_model=AuditLogListResponse)
async def list_audit_logs(
    accion: str | None = Query(None),
    actor_id: uuid.UUID | None = Query(None),
    fecha_desde: datetime | None = Query(None),
    fecha_hasta: datetime | None = Query(None),
    offset: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    current_user: UserSession = Depends(require_permission_return_user("auditoria:ver")),
    db: AsyncSession = Depends(get_db),
):
    repo = AuditLogRepository(db, current_user.tenant_id)
    items = await repo.list(
        accion=accion,
        actor_id=actor_id,
        fecha_desde=fecha_desde,
        fecha_hasta=fecha_hasta,
        offset=offset,
        limit=limit,
    )
    total = await repo.count(
        accion=accion,
        actor_id=actor_id,
        fecha_desde=fecha_desde,
        fecha_hasta=fecha_hasta,
    )
    return AuditLogListResponse(
        items=[AuditLogResponse.model_validate(e) for e in items],
        total=total,
        offset=offset,
        limit=limit,
    )


@router.get("/{id}", response_model=AuditLogResponse)
async def get_audit_log(
    id: uuid.UUID,
    current_user: UserSession = Depends(require_permission_return_user("auditoria:ver")),
    db: AsyncSession = Depends(get_db),
):
    repo = AuditLogRepository(db, current_user.tenant_id)
    entry = await repo.find_by_id(id)
    if entry is None:
        raise HTTPException(status_code=404, detail="Audit log entry not found")
    return AuditLogResponse.model_validate(entry)
