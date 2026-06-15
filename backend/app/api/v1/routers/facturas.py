"""Facturas router — CRUD endpoints for facturador billing."""

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import (
    UserSession,
    get_db,
    require_permission_return_user,
)
from app.schemas.liquidacion import (
    FacturaCreate,
    FacturaResponse,
)
from app.services.factura_service import FacturaService

router = APIRouter(prefix="/api/facturas", tags=["facturas"])


def _get_service(db: AsyncSession, tenant_id: uuid.UUID) -> FacturaService:
    return FacturaService(db, tenant_id)


@router.post("", response_model=FacturaResponse, status_code=201)
async def create_factura(
    body: FacturaCreate,
    current_user: UserSession = Depends(require_permission_return_user("liquidaciones:ver")),
    db: AsyncSession = Depends(get_db),
):
    svc = _get_service(db, current_user.tenant_id)
    return await svc.create(body)


@router.get("", response_model=list[FacturaResponse])
async def list_facturas(
    current_user: UserSession = Depends(require_permission_return_user("liquidaciones:ver")),
    db: AsyncSession = Depends(get_db),
    usuario_id: uuid.UUID | None = Query(default=None),
    periodo: str | None = Query(default=None),
    estado: str | None = Query(default=None),
    busqueda: str | None = Query(default=None),
):
    svc = _get_service(db, current_user.tenant_id)
    return await svc.list_all(
        usuario_id=usuario_id,
        periodo=periodo,
        estado=estado,
        busqueda=busqueda,
    )


@router.get("/{id}", response_model=FacturaResponse)
async def get_factura(
    id: uuid.UUID,
    current_user: UserSession = Depends(require_permission_return_user("liquidaciones:ver")),
    db: AsyncSession = Depends(get_db),
):
    svc = _get_service(db, current_user.tenant_id)
    factura = await svc.get_by_id(id)
    if factura is None:
        raise HTTPException(status_code=404, detail="Factura not found")
    return factura


@router.put("/{id}/abonar", response_model=FacturaResponse)
async def abonar_factura(
    id: uuid.UUID,
    current_user: UserSession = Depends(require_permission_return_user("liquidaciones:ver")),
    db: AsyncSession = Depends(get_db),
):
    svc = _get_service(db, current_user.tenant_id)
    return await svc.abonar(id)


@router.put("/{id}/reabrir", response_model=FacturaResponse)
async def reabrir_factura(
    id: uuid.UUID,
    current_user: UserSession = Depends(require_permission_return_user("liquidaciones:ver")),
    db: AsyncSession = Depends(get_db),
):
    svc = _get_service(db, current_user.tenant_id)
    return await svc.reabrir(id)


@router.delete("/{id}", status_code=200)
async def delete_factura(
    id: uuid.UUID,
    current_user: UserSession = Depends(require_permission_return_user("liquidaciones:ver")),
    db: AsyncSession = Depends(get_db),
):
    svc = _get_service(db, current_user.tenant_id)
    deleted = await svc.soft_delete(id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Factura not found")
    return {"detail": "Factura deleted"}
