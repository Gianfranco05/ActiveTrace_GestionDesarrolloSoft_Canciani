import uuid

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import (
    UserSession,
    get_current_user,
    get_db,
    require_permission_return_user,
)
from app.repositories.audit_repository import AuditLogRepository
from app.schemas.avisos import (
    AckResponse,
    AckStatsResponse,
    AcuseResponse,
    AvisoCreateRequest,
    AvisoDetailResponse,
    AvisoListResponse,
    AvisoResponse,
    AvisoUpdateRequest,
)
from app.services.audit_service import AuditService
from app.services.aviso_service import AvisoService

router = APIRouter(prefix="/api/avisos", tags=["Avisos"])


def _get_audit_service(db: AsyncSession, tenant_id: uuid.UUID) -> AuditService:
    return AuditService(db, AuditLogRepository(db, tenant_id))


@router.post("", response_model=AvisoResponse, status_code=201)
async def create_aviso(
    body: AvisoCreateRequest,
    current_user: UserSession = Depends(
        require_permission_return_user("avisos:publicar"),
    ),
    db: AsyncSession = Depends(get_db),
):
    audit_svc = _get_audit_service(db, current_user.tenant_id)
    svc = AvisoService(db, audit_svc, current_user.tenant_id)
    try:
        result = await svc.create(body, current_user.user_id)
    except HTTPException:
        raise
    return result


@router.put("/{aviso_id}", response_model=AvisoResponse)
async def update_aviso(
    aviso_id: uuid.UUID,
    body: AvisoUpdateRequest,
    current_user: UserSession = Depends(
        require_permission_return_user("avisos:publicar"),
    ),
    db: AsyncSession = Depends(get_db),
):
    audit_svc = _get_audit_service(db, current_user.tenant_id)
    svc = AvisoService(db, audit_svc, current_user.tenant_id)
    try:
        result = await svc.update(aviso_id, body, current_user.user_id)
    except HTTPException:
        raise
    return result


@router.delete("/{aviso_id}", status_code=204)
async def delete_aviso(
    aviso_id: uuid.UUID,
    current_user: UserSession = Depends(
        require_permission_return_user("avisos:publicar"),
    ),
    db: AsyncSession = Depends(get_db),
):
    audit_svc = _get_audit_service(db, current_user.tenant_id)
    svc = AvisoService(db, audit_svc, current_user.tenant_id)
    try:
        await svc.soft_delete(aviso_id, current_user.user_id)
    except HTTPException:
        raise


@router.get("/{aviso_id}", response_model=AvisoDetailResponse)
async def get_aviso(
    aviso_id: uuid.UUID,
    current_user: UserSession = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    audit_svc = _get_audit_service(db, current_user.tenant_id)
    svc = AvisoService(db, audit_svc, current_user.tenant_id)
    try:
        result = await svc.get_by_id(aviso_id, current_user.user_id)
    except HTTPException:
        raise
    return result


@router.get("", response_model=AvisoListResponse)
async def list_avisos(
    offset: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    activo: bool | None = Query(None),
    alcance: str | None = Query(None),
    busqueda: str | None = Query(None),
    admin: bool = Query(False),
    current_user: UserSession = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    audit_svc = _get_audit_service(db, current_user.tenant_id)
    svc = AvisoService(db, audit_svc, current_user.tenant_id)
    try:
        result = await svc.list_visibles(
            current_user.user_id, offset, limit,
            activo=activo, alcance=alcance, busqueda=busqueda,
            admin=admin,
        )
    except HTTPException:
        raise
    return result


@router.post("/{aviso_id}/ack", response_model=AckResponse)
async def acknowledge_aviso(
    aviso_id: uuid.UUID,
    current_user: UserSession = Depends(
        require_permission_return_user("aviso:confirmar"),
    ),
    db: AsyncSession = Depends(get_db),
    response_model=None,
):
    audit_svc = _get_audit_service(db, current_user.tenant_id)
    svc = AvisoService(db, audit_svc, current_user.tenant_id)
    try:
        ack_response, status = await svc.acknowledge(
            aviso_id, current_user.user_id, current_user.user_id,
        )
    except HTTPException:
        raise
    # Manually set status code
    from starlette.responses import JSONResponse
    return JSONResponse(
        content=ack_response.model_dump(mode="json"),
        status_code=status,
    )


@router.get("/{aviso_id}/ack/stats", response_model=AckStatsResponse)
async def get_aviso_stats(
    aviso_id: uuid.UUID,
    current_user: UserSession = Depends(
        require_permission_return_user("avisos:publicar"),
    ),
    db: AsyncSession = Depends(get_db),
):
    audit_svc = _get_audit_service(db, current_user.tenant_id)
    svc = AvisoService(db, audit_svc, current_user.tenant_id)
    try:
        result = await svc.get_stats(aviso_id)
    except HTTPException:
        raise
    return result


@router.get("/{aviso_id}/acuses", response_model=list[AcuseResponse])
async def get_acuses(
    aviso_id: uuid.UUID,
    current_user: UserSession = Depends(
        require_permission_return_user("avisos:publicar"),
    ),
    db: AsyncSession = Depends(get_db),
):
    audit_svc = _get_audit_service(db, current_user.tenant_id)
    svc = AvisoService(db, audit_svc, current_user.tenant_id)
    try:
        result = await svc.get_acuses(aviso_id)
    except HTTPException:
        raise
    return result
