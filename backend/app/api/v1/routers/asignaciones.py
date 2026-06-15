"""Asignacion router — role-context assignment CRUD."""

import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import (
    UserSession,
    get_db,
    require_permission_return_user,
)
from app.repositories.asignacion_repository import AsignacionRepository
from app.schemas.asignaciones import (
    AsignacionCreate,
    AsignacionResponse,
    AsignacionUpdate,
)
from app.schemas.common import ListResponse
from app.services.asignacion_service import AsignacionService

router = APIRouter(prefix="/api/v1/asignaciones", tags=["asignaciones"])


@router.get("", response_model=ListResponse[AsignacionResponse])
async def list_asignaciones(
    current_user: UserSession = Depends(require_permission_return_user("usuarios:gestionar")),
    db: AsyncSession = Depends(get_db),
    offset: int = 0,
    limit: int = 100,
    usuario_id: uuid.UUID | None = None,
    rol_id: uuid.UUID | None = None,
):
    repo = AsignacionRepository(db, current_user.tenant_id)
    service = AsignacionService(repo)
    items = await service.list()
    if usuario_id:
        items = [i for i in items if i.usuario_id == usuario_id]
    if rol_id:
        items = [i for i in items if i.rol_id == rol_id]

    # Batch-load rol names to avoid MissingGreenlet on lazy-load
    from app.models.rol import Rol
    rol_ids = {a.rol_id for a in items}
    rol_map: dict[uuid.UUID, str] = {}
    if rol_ids:
        rol_query = select(Rol).where(Rol.id.in_(rol_ids))
        rol_result = await db.execute(rol_query)
        rol_map = {r.id: r.nombre for r in rol_result.scalars().all()}

    response_items = []
    for a in items:
        response_items.append(
            AsignacionResponse(
                id=a.id,
                tenant_id=a.tenant_id,
                usuario_id=a.usuario_id,
                rol_id=a.rol_id,
                rol_nombre=rol_map.get(a.rol_id, ""),
                materia_id=a.materia_id,
                carrera_id=a.carrera_id,
                cohorte_id=a.cohorte_id,
                comisiones=a.comisiones,
                responsable_id=a.responsable_id,
                vig_desde=a.vig_desde,
                vig_hasta=a.vig_hasta,
                estado_vigencia=a.estado_vigencia,
                created_at=a.created_at,
                updated_at=a.updated_at,
            )
        )

    return ListResponse(
        items=response_items,
        total=len(items),
        offset=offset,
        limit=limit,
    )


@router.post("", response_model=AsignacionResponse, status_code=201)
async def create_asignacion(
    body: AsignacionCreate,
    current_user: UserSession = Depends(require_permission_return_user("usuarios:gestionar")),
    db: AsyncSession = Depends(get_db),
):
    repo = AsignacionRepository(db, current_user.tenant_id)
    service = AsignacionService(repo)
    entity = await service.create(body)
    return entity


@router.get("/{id}", response_model=AsignacionResponse)
async def get_asignacion(
    id: uuid.UUID,
    current_user: UserSession = Depends(require_permission_return_user("usuarios:gestionar")),
    db: AsyncSession = Depends(get_db),
):
    repo = AsignacionRepository(db, current_user.tenant_id)
    service = AsignacionService(repo)
    entity = await service.get(id)
    if entity is None:
        raise HTTPException(status_code=404, detail="Asignacion not found")
    return entity


@router.put("/{id}", response_model=AsignacionResponse)
async def update_asignacion(
    id: uuid.UUID,
    body: AsignacionUpdate,
    current_user: UserSession = Depends(require_permission_return_user("usuarios:gestionar")),
    db: AsyncSession = Depends(get_db),
):
    repo = AsignacionRepository(db, current_user.tenant_id)
    service = AsignacionService(repo)
    data = body.model_dump(exclude_none=True)
    if not data:
        raise HTTPException(status_code=400, detail="No fields to update")
    entity = await service.update(id, body)
    if entity is None:
        raise HTTPException(status_code=404, detail="Asignacion not found")
    return entity


@router.delete("/{id}", status_code=204)
async def delete_asignacion(
    id: uuid.UUID,
    current_user: UserSession = Depends(require_permission_return_user("usuarios:gestionar")),
    db: AsyncSession = Depends(get_db),
):
    repo = AsignacionRepository(db, current_user.tenant_id)
    service = AsignacionService(repo)
    deleted = await service.soft_delete(id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Asignacion not found")
