import uuid
from datetime import date

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import (
    UserSession,
    get_db,
    require_permission_return_user,
)
from app.repositories.fecha_academica_repository import FechaAcademicaRepository
from app.schemas.fechas_academicas import (
    FechaAcademicaCreateRequest,
    FechaAcademicaResponse,
    FechaAcademicaUpdateRequest,
    FechasLmsHtmlResponse,
)
from app.services.fecha_academica_service import FechaAcademicaService

router = APIRouter(prefix="/api/fechas-academicas", tags=["fechas-academicas"])


@router.get("")
async def list_fechas(
    current_user: UserSession = Depends(require_permission_return_user("estructura:gestionar")),
    db: AsyncSession = Depends(get_db),
    materia_id: uuid.UUID | None = None,
    cohorte_id: uuid.UUID | None = None,
    tipo: str | None = None,
    periodo: str | None = None,
    offset: int = 0,
    limit: int = 20,
):
    repo = FechaAcademicaRepository(db, current_user.tenant_id)
    svc = FechaAcademicaService(db, repo)
    items, total = await svc.listar(
        materia_id=materia_id,
        cohorte_id=cohorte_id,
        tipo=tipo,
        periodo=periodo,
        offset=offset,
        limit=limit,
        tenant_id=current_user.tenant_id,
    )
    return {"items": [FechaAcademicaResponse.model_validate(i) for i in items], "total": total, "offset": offset, "limit": limit}


@router.get("/calendario")
async def calendario_fechas(
    current_user: UserSession = Depends(require_permission_return_user("estructura:gestionar")),
    db: AsyncSession = Depends(get_db),
    materia_id: uuid.UUID | None = None,
    cohorte_id: uuid.UUID | None = None,
    periodo: str | None = None,
    fecha_desde: date | None = None,
    fecha_hasta: date | None = None,
):
    repo = FechaAcademicaRepository(db, current_user.tenant_id)
    svc = FechaAcademicaService(db, repo)
    items = await svc.calendario(
        tenant_id=current_user.tenant_id,
        materia_id=materia_id,
        cohorte_id=cohorte_id,
        periodo=periodo,
        fecha_desde=fecha_desde,
        fecha_hasta=fecha_hasta,
    )
    return {"items": items, "total": len(items)}


@router.post("", response_model=FechaAcademicaResponse, status_code=201)
async def create_fecha(
    body: FechaAcademicaCreateRequest,
    current_user: UserSession = Depends(require_permission_return_user("estructura:gestionar")),
    db: AsyncSession = Depends(get_db),
):
    repo = FechaAcademicaRepository(db, current_user.tenant_id)
    svc = FechaAcademicaService(db, repo)
    return await svc.crear(body, current_user.tenant_id, current_user.user_id)


@router.patch("/{id}", response_model=FechaAcademicaResponse)
async def update_fecha(
    id: uuid.UUID,
    body: FechaAcademicaUpdateRequest,
    current_user: UserSession = Depends(require_permission_return_user("estructura:gestionar")),
    db: AsyncSession = Depends(get_db),
):
    repo = FechaAcademicaRepository(db, current_user.tenant_id)
    svc = FechaAcademicaService(db, repo)
    return await svc.actualizar(id, body, current_user.tenant_id, current_user.user_id)


@router.delete("/{id}", status_code=204)
async def delete_fecha(
    id: uuid.UUID,
    current_user: UserSession = Depends(require_permission_return_user("estructura:gestionar")),
    db: AsyncSession = Depends(get_db),
):
    repo = FechaAcademicaRepository(db, current_user.tenant_id)
    svc = FechaAcademicaService(db, repo)
    await svc.eliminar(id, current_user.tenant_id, current_user.user_id)


@router.get("/lms/html", response_model=FechasLmsHtmlResponse)
async def lms_html(
    current_user: UserSession = Depends(require_permission_return_user("estructura:gestionar")),
    db: AsyncSession = Depends(get_db),
    materia_id: uuid.UUID | None = None,
    cohorte_id: uuid.UUID | None = None,
):
    if materia_id is None or cohorte_id is None:
        raise HTTPException(status_code=422, detail="materia_id and cohorte_id are required")

    repo = FechaAcademicaRepository(db, current_user.tenant_id)
    svc = FechaAcademicaService(db, repo)
    html = await svc.generar_html_lms(materia_id, cohorte_id, current_user.tenant_id)
    return FechasLmsHtmlResponse(html=html)
