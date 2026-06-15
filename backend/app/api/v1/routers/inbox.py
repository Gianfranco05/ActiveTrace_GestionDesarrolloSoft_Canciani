import uuid

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import (
    UserSession,
    get_db,
    require_permission_return_user,
)
from app.repositories.audit_repository import AuditLogRepository
from app.schemas.mensajes import (
    MensajeCreateRequest,
    MensajeReplyRequest,
    MensajeResponse,
    ThreadDetailResponse,
)
from app.services.audit_service import AuditService

router = APIRouter(prefix="/api/inbox", tags=["inbox"])


def _build_audit_service(db: AsyncSession, tenant_id: uuid.UUID) -> AuditService:
    repo = AuditLogRepository(db, tenant_id)
    return AuditService(db, repo)


@router.post("", response_model=MensajeResponse, status_code=201)
async def enviar_mensaje(
    body: MensajeCreateRequest,
    current_user: UserSession = Depends(require_permission_return_user("mensajeria:usar")),
    db: AsyncSession = Depends(get_db),
):
    from app.services.mensaje_service import MensajeService

    svc = MensajeService(db, current_user.tenant_id, _build_audit_service(db, current_user.tenant_id))
    try:
        return await svc.enviar_mensaje(current_user.user_id, current_user.tenant_id, body)
    except HTTPException:
        raise


@router.get("")
async def listar_inbox(
    current_user: UserSession = Depends(require_permission_return_user("mensajeria:usar")),
    db: AsyncSession = Depends(get_db),
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=20, ge=1, le=50),
):
    from app.services.mensaje_service import MensajeService

    svc = MensajeService(db, current_user.tenant_id)
    return await svc.listar_inbox(current_user.user_id, current_user.tenant_id, offset, limit)


@router.get("/{thread_id}", response_model=ThreadDetailResponse)
async def ver_hilo(
    thread_id: uuid.UUID,
    current_user: UserSession = Depends(require_permission_return_user("mensajeria:usar")),
    db: AsyncSession = Depends(get_db),
):
    from app.services.mensaje_service import MensajeService

    svc = MensajeService(db, current_user.tenant_id)
    try:
        return await svc.ver_hilo(thread_id, current_user.user_id, current_user.tenant_id)
    except HTTPException:
        raise


@router.post("/{thread_id}/reply", response_model=MensajeResponse, status_code=201)
async def responder_hilo(
    thread_id: uuid.UUID,
    body: MensajeReplyRequest,
    current_user: UserSession = Depends(require_permission_return_user("mensajeria:usar")),
    db: AsyncSession = Depends(get_db),
):
    from app.services.mensaje_service import MensajeService

    svc = MensajeService(db, current_user.tenant_id, _build_audit_service(db, current_user.tenant_id))
    try:
        return await svc.responder(thread_id, current_user.user_id, current_user.tenant_id, body)
    except HTTPException:
        raise
