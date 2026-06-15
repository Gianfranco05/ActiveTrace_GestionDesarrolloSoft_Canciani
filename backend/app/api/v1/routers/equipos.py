"""Equipos router — team management endpoints."""

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import (
    UserSession,
    get_current_user,
    get_db,
    require_permission_return_user,
)
from app.repositories.audit_repository import AuditLogRepository
from app.schemas.asignaciones import (
    AsignacionMasivaRequest,
    AsignacionResponse,
    ClonarRequest,
    EquipoDetailResponse,
    EquipoResponse,
    MisMateriasResponse,
    UsuarioSearchResponse,
    VigenciaUpdateRequest,
)
from app.schemas.common import ListResponse
from app.services.audit_service import AuditService
from app.services.equipo_service import EquipoService

router = APIRouter(prefix="/api/equipos", tags=["equipos"])


def _get_service(db: AsyncSession, user: UserSession) -> EquipoService:
    audit_repo = AuditLogRepository(db, user.tenant_id)
    audit_svc = AuditService(db, audit_repo)
    return EquipoService(session=db, audit_service=audit_svc, tenant_id=user.tenant_id)


@router.get("/mis-materias", response_model=list[MisMateriasResponse])
async def mis_materias(
    current_user: UserSession = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Devuelve las materias vigentes asignadas al usuario autenticado.
    Si el usuario es ADMIN o COORDINADOR, devuelve todas las materias del tenant."""
    from sqlalchemy import select

    from app.models.materia import Materia

    if "ADMIN" in current_user.roles or "COORDINADOR" in current_user.roles:
        query = select(Materia).where(
            Materia.tenant_id == current_user.tenant_id,
            Materia.estado == "Activa",
            Materia.deleted_at.is_(None),
        )
        result = await db.execute(query)
        materias = result.scalars().all()
        return [
            MisMateriasResponse(id=m.id, nombre=m.nombre, comision="")
            for m in materias
        ]

    service = _get_service(db, current_user)
    return await service.listar_mis_materias(current_user.user_id)


@router.get("/mis-equipos", response_model=ListResponse[AsignacionResponse])
async def mis_equipos(
    current_user: UserSession = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    estado: str | None = Query(default="Vigente"),
    materia_id: uuid.UUID | None = Query(default=None),
    rol_id: uuid.UUID | None = Query(default=None),
    carrera_id: uuid.UUID | None = Query(default=None),
    cohorte_id: uuid.UUID | None = Query(default=None),
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=20, ge=1, le=100),
):
    service = _get_service(db, current_user)
    filtros = {
        "estado": estado,
        "materia_id": str(materia_id) if materia_id else None,
        "rol_id": str(rol_id) if rol_id else None,
        "carrera_id": str(carrera_id) if carrera_id else None,
        "cohorte_id": str(cohorte_id) if cohorte_id else None,
    }
    filtros = {k: v for k, v in filtros.items() if v is not None}
    items = await service.listar_mis_equipos(current_user.user_id, current_user.tenant_id, filtros)
    total = len(items)
    paginated = items[offset:offset + limit]
    return ListResponse(items=paginated, total=total, offset=offset, limit=limit)


@router.get("", response_model=ListResponse[EquipoResponse])
async def list_equipos(
    current_user: UserSession = Depends(require_permission_return_user("equipos:asignar")),
    db: AsyncSession = Depends(get_db),
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=20, ge=1, le=100),
):
    service = _get_service(db, current_user)
    items = await service.listar_equipos(current_user.tenant_id)
    total = len(items)
    paginated = items[offset:offset + limit]
    return ListResponse(items=paginated, total=total, offset=offset, limit=limit)


@router.get("/detail", response_model=EquipoDetailResponse)
async def get_equipo_detail(
    current_user: UserSession = Depends(require_permission_return_user("equipos:asignar")),
    db: AsyncSession = Depends(get_db),
    materia_id: uuid.UUID = Query(...),
    carrera_id: uuid.UUID = Query(...),
    cohorte_id: uuid.UUID = Query(...),
):
    service = _get_service(db, current_user)
    try:
        equipo = await service.obtener_equipo(materia_id, carrera_id, cohorte_id)
    except HTTPException:
        raise
    if not equipo.asignaciones:
        raise HTTPException(status_code=404, detail="Equipo not found")
    return equipo


@router.post("/masiva", response_model=ListResponse[AsignacionResponse], status_code=201)
async def asignacion_masiva(
    body: AsignacionMasivaRequest,
    current_user: UserSession = Depends(require_permission_return_user("equipos:asignar")),
    db: AsyncSession = Depends(get_db),
):
    service = _get_service(db, current_user)
    items = await service.asignacion_masiva(body, current_user.user_id)
    return ListResponse(items=items, total=len(items), offset=0, limit=len(items))


@router.post("/clonar", response_model=EquipoDetailResponse, status_code=201)
async def clonar_equipo(
    body: ClonarRequest,
    current_user: UserSession = Depends(require_permission_return_user("equipos:asignar")),
    db: AsyncSession = Depends(get_db),
):
    service = _get_service(db, current_user)
    return await service.clonar_equipo(body, current_user.user_id)


@router.patch("/vigencia", response_model=EquipoDetailResponse)
async def modificar_vigencia(
    body: VigenciaUpdateRequest,
    current_user: UserSession = Depends(require_permission_return_user("equipos:asignar")),
    db: AsyncSession = Depends(get_db),
    materia_id: uuid.UUID = Query(...),
    carrera_id: uuid.UUID = Query(...),
    cohorte_id: uuid.UUID = Query(...),
):
    service = _get_service(db, current_user)
    try:
        return await service.modificar_vigencia(materia_id, carrera_id, cohorte_id, body, current_user.user_id)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e)) from e


@router.get("/export")
async def export_equipo(
    current_user: UserSession = Depends(require_permission_return_user("equipos:asignar")),
    db: AsyncSession = Depends(get_db),
    materia_id: uuid.UUID = Query(...),
    carrera_id: uuid.UUID = Query(...),
    cohorte_id: uuid.UUID = Query(...),
):
    service = _get_service(db, current_user)
    csv_content = await service.exportar_equipo(materia_id, carrera_id, cohorte_id)
    return StreamingResponse(
        iter([csv_content]),
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": f"attachment; filename=equipo_{materia_id}_{carrera_id}_{cohorte_id}.csv"},
    )


@router.get("/usuarios/search", response_model=ListResponse[UsuarioSearchResponse])
async def search_usuarios(
    current_user: UserSession = Depends(require_permission_return_user("equipos:asignar")),
    db: AsyncSession = Depends(get_db),
    q: str = Query(..., min_length=1),
    limit: int = Query(default=20, ge=1, le=50),
):
    service = _get_service(db, current_user)
    items = await service.buscar_usuarios(q, current_user.tenant_id, limit)
    return ListResponse(items=items, total=len(items), offset=0, limit=limit)
