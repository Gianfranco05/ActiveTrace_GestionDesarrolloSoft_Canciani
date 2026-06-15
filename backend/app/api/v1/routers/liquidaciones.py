"""Liquidaciones router — calculation, view, close, history, export, salary grid."""

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import (
    UserSession,
    get_db,
    require_permission_return_user,
)
from app.repositories.salario_repository import (
    GrupoMateriaRepository,
    SalarioBaseRepository,
    SalarioPlusRepository,
)
from app.schemas.liquidacion import (
    CalcularLiquidacionRequest,
    GrupoMateriaCreate,
    GrupoMateriaResponse,
    LiquidacionKPIs,
    LiquidacionListResponse,
    LiquidacionResponse,
    SalarioBaseCreate,
    SalarioBaseResponse,
    SalarioBaseUpdate,
    SalarioPlusCreate,
    SalarioPlusResponse,
    SalarioPlusUpdate,
)
from app.services.liquidacion_service import LiquidacionService

router = APIRouter(prefix="/api/liquidaciones", tags=["liquidaciones"])


def _get_liquidacion_service(db: AsyncSession, tenant_id: uuid.UUID) -> LiquidacionService:
    return LiquidacionService(db, tenant_id)


# ── Liquidacion endpoints ─────────────────────────────────────────────────

@router.get("", response_model=list[LiquidacionResponse])
async def list_liquidaciones(
    current_user: UserSession = Depends(require_permission_return_user("liquidaciones:ver")),
    db: AsyncSession = Depends(get_db),
    cohorte_id: uuid.UUID | None = Query(default=None),
    periodo: str | None = Query(default=None),
    usuario_id: uuid.UUID | None = Query(default=None),
):
    svc = _get_liquidacion_service(db, current_user.tenant_id)
    if cohorte_id and periodo:
        view = await svc.get_liquidacion_view(cohorte_id, periodo)
        return view["liquidaciones"]
    if cohorte_id and not periodo:
        view = await svc.get_historial(cohorte_id)
        return view
    return []


@router.get("/kpi", response_model=LiquidacionKPIs)
async def get_liquidacion_kpi(
    current_user: UserSession = Depends(require_permission_return_user("liquidaciones:ver")),
    db: AsyncSession = Depends(get_db),
    cohorte_id: uuid.UUID | None = Query(default=None),
    periodo: str | None = Query(default=None),
):
    if not cohorte_id or not periodo:
        from decimal import Decimal
        return LiquidacionKPIs(
            total_general=Decimal("0"),
            total_sin_factura=Decimal("0"),
            total_nexo=Decimal("0"),
            total_facturantes=0,
            total_docentes=0,
        )
    svc = _get_liquidacion_service(db, current_user.tenant_id)
    view = await svc.get_liquidacion_view(cohorte_id, periodo)
    return view["kpis"]


@router.post("/calcular", response_model=LiquidacionListResponse)
async def calcular_liquidacion(
    body: CalcularLiquidacionRequest,
    current_user: UserSession = Depends(require_permission_return_user("liquidaciones:calcular")),
    db: AsyncSession = Depends(get_db),
):
    from app.services.liquidacion_service import LiquidacionCerradaError

    svc = _get_liquidacion_service(db, current_user.tenant_id)
    try:
        result = await svc.calcular_liquidacion(body.cohorte_id, body.periodo)
    except LiquidacionCerradaError as e:
        raise HTTPException(status_code=409, detail=str(e))
    view = await svc.get_liquidacion_view(body.cohorte_id, body.periodo)
    return LiquidacionListResponse(
        liquidaciones=view["liquidaciones"],
        kpis=view["kpis"],
        docentes_excluidos=result.get("docentes_excluidos", []),
    )


@router.post("/{cohorte_id}/{periodo}/cerrar", response_model=list[LiquidacionResponse])
async def cerrar_liquidacion(
    cohorte_id: uuid.UUID,
    periodo: str,
    current_user: UserSession = Depends(require_permission_return_user("liquidaciones:cerrar")),
    db: AsyncSession = Depends(get_db),
):
    from app.services.liquidacion_service import LiquidacionCerradaError, LiquidacionNotFoundError

    svc = _get_liquidacion_service(db, current_user.tenant_id)
    try:
        closed = await svc.cerrar_liquidacion(cohorte_id, periodo, current_user.user_id)
    except LiquidacionNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except LiquidacionCerradaError as e:
        raise HTTPException(status_code=409, detail=str(e))
    return closed


@router.get("/historial", response_model=list[LiquidacionResponse])
async def historial_liquidaciones(
    current_user: UserSession = Depends(require_permission_return_user("liquidaciones:ver")),
    db: AsyncSession = Depends(get_db),
    cohorte_id: uuid.UUID | None = Query(None),
):
    svc = _get_liquidacion_service(db, current_user.tenant_id)
    return await svc.get_historial(cohorte_id)


@router.get("/exportar")
async def exportar_liquidacion(
    current_user: UserSession = Depends(require_permission_return_user("liquidaciones:exportar")),
    db: AsyncSession = Depends(get_db),
    cohorte_id: uuid.UUID = Query(...),
    periodo: str = Query(...),
):
    svc = _get_liquidacion_service(db, current_user.tenant_id)
    csv_content = await svc.exportar_liquidacion(cohorte_id, periodo)
    return StreamingResponse(
        iter([csv_content]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=liquidacion_{cohorte_id}_{periodo}.csv"},
    )


# ── SalarioBase CRUD ──────────────────────────────────────────────────────

@router.get("/salarios/base", response_model=list[SalarioBaseResponse])
async def list_salarios_base(
    current_user: UserSession = Depends(require_permission_return_user("liquidaciones:ver")),
    db: AsyncSession = Depends(get_db),
):
    repo = SalarioBaseRepository(db, current_user.tenant_id)
    return await repo.list_all()


@router.post("/salarios/base", response_model=SalarioBaseResponse, status_code=201)
async def create_salario_base(
    body: SalarioBaseCreate,
    current_user: UserSession = Depends(require_permission_return_user("liquidaciones:configurar-salarios")),
    db: AsyncSession = Depends(get_db),
):
    repo = SalarioBaseRepository(db, current_user.tenant_id)
    return await repo.create_or_update(body.model_dump())


@router.put("/salarios/base/{id}", response_model=SalarioBaseResponse)
async def update_salario_base(
    id: uuid.UUID,
    body: SalarioBaseUpdate,
    current_user: UserSession = Depends(require_permission_return_user("liquidaciones:configurar-salarios")),
    db: AsyncSession = Depends(get_db),
):
    repo = SalarioBaseRepository(db, current_user.tenant_id)
    existing = await repo.get(id)
    if existing is None:
        raise HTTPException(status_code=404, detail="SalarioBase not found")
    update_data = body.model_dump(exclude_unset=True)
    updated = await repo.update(id, update_data)
    return updated


@router.delete("/salarios/base/{id}", status_code=200)
async def delete_salario_base(
    id: uuid.UUID,
    current_user: UserSession = Depends(require_permission_return_user("liquidaciones:configurar-salarios")),
    db: AsyncSession = Depends(get_db),
):
    repo = SalarioBaseRepository(db, current_user.tenant_id)
    deleted = await repo.soft_delete(id)
    if not deleted:
        raise HTTPException(status_code=404, detail="SalarioBase not found")
    return {"detail": "SalarioBase deleted"}


# ── SalarioPlus CRUD ──────────────────────────────────────────────────────

@router.get("/salarios/plus", response_model=list[SalarioPlusResponse])
async def list_salarios_plus(
    current_user: UserSession = Depends(require_permission_return_user("liquidaciones:ver")),
    db: AsyncSession = Depends(get_db),
):
    repo = SalarioPlusRepository(db, current_user.tenant_id)
    return await repo.list_all()


@router.post("/salarios/plus", response_model=SalarioPlusResponse, status_code=201)
async def create_salario_plus(
    body: SalarioPlusCreate,
    current_user: UserSession = Depends(require_permission_return_user("liquidaciones:configurar-salarios")),
    db: AsyncSession = Depends(get_db),
):
    repo = SalarioPlusRepository(db, current_user.tenant_id)
    return await repo.create_or_update(body.model_dump())


@router.put("/salarios/plus/{id}", response_model=SalarioPlusResponse)
async def update_salario_plus(
    id: uuid.UUID,
    body: SalarioPlusUpdate,
    current_user: UserSession = Depends(require_permission_return_user("liquidaciones:configurar-salarios")),
    db: AsyncSession = Depends(get_db),
):
    repo = SalarioPlusRepository(db, current_user.tenant_id)
    existing = await repo.get(id)
    if existing is None:
        raise HTTPException(status_code=404, detail="SalarioPlus not found")
    update_data = body.model_dump(exclude_unset=True)
    updated = await repo.update(id, update_data)
    return updated


@router.delete("/salarios/plus/{id}", status_code=200)
async def delete_salario_plus(
    id: uuid.UUID,
    current_user: UserSession = Depends(require_permission_return_user("liquidaciones:configurar-salarios")),
    db: AsyncSession = Depends(get_db),
):
    repo = SalarioPlusRepository(db, current_user.tenant_id)
    deleted = await repo.soft_delete(id)
    if not deleted:
        raise HTTPException(status_code=404, detail="SalarioPlus not found")
    return {"detail": "SalarioPlus deleted"}


# ── GrupoMateria CRUD ─────────────────────────────────────────────────────

@router.get("/salarios/grupos", response_model=list[GrupoMateriaResponse])
async def list_grupo_materia(
    current_user: UserSession = Depends(require_permission_return_user("liquidaciones:ver")),
    db: AsyncSession = Depends(get_db),
):
    repo = GrupoMateriaRepository(db, current_user.tenant_id)
    return await repo.list_all()


@router.post("/salarios/grupos", response_model=GrupoMateriaResponse, status_code=201)
async def create_grupo_materia(
    body: GrupoMateriaCreate,
    current_user: UserSession = Depends(require_permission_return_user("liquidaciones:configurar-salarios")),
    db: AsyncSession = Depends(get_db),
):
    repo = GrupoMateriaRepository(db, current_user.tenant_id)
    return await repo.create(body.model_dump())


@router.delete("/salarios/grupos/{id}", status_code=200)
async def delete_grupo_materia(
    id: uuid.UUID,
    current_user: UserSession = Depends(require_permission_return_user("liquidaciones:configurar-salarios")),
    db: AsyncSession = Depends(get_db),
):
    repo = GrupoMateriaRepository(db, current_user.tenant_id)
    deleted = await repo.soft_delete(id)
    if not deleted:
        raise HTTPException(status_code=404, detail="GrupoMateria not found")
    return {"detail": "GrupoMateria deleted"}
