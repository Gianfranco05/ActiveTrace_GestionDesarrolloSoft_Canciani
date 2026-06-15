import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import (
    UserSession,
    get_db,
    require_permission_return_user,
)
from app.repositories.audit_repository import AuditLogRepository
from app.schemas.perfil import PerfilResponse, PerfilUpdateRequest
from app.services.audit_service import AuditService

router = APIRouter(prefix="/api/perfil", tags=["perfil"])


def _build_audit_service(db: AsyncSession, tenant_id: uuid.UUID) -> AuditService:
    repo = AuditLogRepository(db, tenant_id)
    return AuditService(db, repo)


@router.get("", response_model=PerfilResponse)
async def get_perfil(
    current_user: UserSession = Depends(require_permission_return_user("perfil:editar")),
    db: AsyncSession = Depends(get_db),
):
    from app.services.perfil_service import PerfilService

    svc = PerfilService(db, current_user.tenant_id)
    try:
        return await svc.get_perfil(current_user.user_id, current_user.tenant_id)
    except HTTPException:
        raise


@router.put("", response_model=PerfilResponse)
async def update_perfil(
    body: PerfilUpdateRequest,
    current_user: UserSession = Depends(require_permission_return_user("perfil:editar")),
    db: AsyncSession = Depends(get_db),
):
    from app.services.perfil_service import PerfilService

    svc = PerfilService(db, current_user.tenant_id, _build_audit_service(db, current_user.tenant_id))
    try:
        return await svc.update_perfil(current_user.user_id, current_user.tenant_id, body)
    except HTTPException:
        raise
