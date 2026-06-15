import uuid
from datetime import date

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import UserSession, get_current_user, get_db, require_permission_return_user
from app.repositories.audit_repository import AuditLogRepository
from app.schemas.common import ListResponse
from app.schemas.evaluaciones import (
    ConsolidadoResponse,
    ConvocatoriaMetricasResponse,
    EvaluacionCreateRequest,
    EvaluacionDetailResponse,
    EvaluacionResponse,
    EvaluacionUpdateRequest,
    ImportarAlumnosRequest,
    PanelMetricasResponse,
    ReservaAgendaResponse,
    ReservaRequest,
    ReservaResponse,
    ResultadoRequest,
    ResultadoResponse,
)
from app.services.audit_service import AuditService
from app.services.evaluacion_admin_service import EvaluacionAdminService
from app.services.evaluacion_service import EvaluacionService
from app.services.resultado_evaluacion_service import ResultadoEvaluacionService

router = APIRouter(prefix="/api/coloquios", tags=["coloquios"])


def _build_audit_service(db: AsyncSession, tenant_id: uuid.UUID) -> AuditService:
    repo = AuditLogRepository(db, tenant_id)
    return AuditService(db, repo)


def _build_svc(db: AsyncSession, tenant_id: uuid.UUID) -> EvaluacionService:
    return EvaluacionService(db, tenant_id, _build_audit_service(db, tenant_id))


def _build_resultado_svc(db: AsyncSession, tenant_id: uuid.UUID) -> ResultadoEvaluacionService:
    return ResultadoEvaluacionService(db, tenant_id, _build_audit_service(db, tenant_id))


def _build_admin_svc(db: AsyncSession, tenant_id: uuid.UUID) -> EvaluacionAdminService:
    return EvaluacionAdminService(db, tenant_id)


@router.post("/", response_model=EvaluacionResponse, status_code=201)
async def crear_convocatoria(
    body: EvaluacionCreateRequest,
    current_user: UserSession = Depends(require_permission_return_user("coloquios:gestionar")),
    db: AsyncSession = Depends(get_db),
):
    svc = _build_svc(db, current_user.tenant_id)
    return await svc.crear(body, current_user.user_id)


@router.get("/", response_model=ListResponse[EvaluacionResponse])
async def listar_convocatorias(
    current_user: UserSession = Depends(require_permission_return_user("coloquios:gestionar")),
    db: AsyncSession = Depends(get_db),
    materia_id: uuid.UUID | None = Query(default=None),
    cohorte_id: uuid.UUID | None = Query(default=None),
    tipo: str | None = Query(default=None),
    activa: bool | None = Query(default=None),
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=20, ge=1, le=100),
):
    svc = _build_svc(db, current_user.tenant_id)
    filtros: dict = {"offset": offset, "limit": limit}
    if materia_id:
        filtros["materia_id"] = materia_id
    if cohorte_id:
        filtros["cohorte_id"] = cohorte_id
    if tipo:
        filtros["tipo"] = tipo
    if activa is not None:
        filtros["activa"] = activa
    items, total = await svc.listar(filtros)
    return ListResponse(
        items=[EvaluacionResponse(**i) for i in items],
        total=total,
        offset=offset,
        limit=limit,
    )


@router.get("/metricas", response_model=PanelMetricasResponse)
async def metricas_panel(
    current_user: UserSession = Depends(require_permission_return_user("coloquios:gestionar")),
    db: AsyncSession = Depends(get_db),
):
    svc = _build_admin_svc(db, current_user.tenant_id)
    return await svc.metricas_panel()


@router.get("/{evaluacion_id}", response_model=EvaluacionDetailResponse)
async def obtener_convocatoria(
    evaluacion_id: uuid.UUID,
    current_user: UserSession = Depends(require_permission_return_user("coloquios:gestionar")),
    db: AsyncSession = Depends(get_db),
):
    svc = _build_svc(db, current_user.tenant_id)
    return await svc.obtener(evaluacion_id)


@router.put("/{evaluacion_id}", response_model=EvaluacionResponse)
async def actualizar_convocatoria(
    evaluacion_id: uuid.UUID,
    body: EvaluacionUpdateRequest,
    current_user: UserSession = Depends(require_permission_return_user("coloquios:gestionar")),
    db: AsyncSession = Depends(get_db),
):
    svc = _build_svc(db, current_user.tenant_id)
    return await svc.actualizar(evaluacion_id, body, current_user.user_id)


@router.put("/{evaluacion_id}/convocados", response_model=EvaluacionDetailResponse)
async def importar_alumnos(
    evaluacion_id: uuid.UUID,
    body: ImportarAlumnosRequest,
    current_user: UserSession = Depends(require_permission_return_user("coloquios:gestionar")),
    db: AsyncSession = Depends(get_db),
):
    svc = _build_resultado_svc(db, current_user.tenant_id)
    return await svc.importar_alumnos(evaluacion_id, body, current_user.user_id)


@router.get("/{evaluacion_id}/metricas", response_model=ConvocatoriaMetricasResponse)
async def metricas_convocatoria(
    evaluacion_id: uuid.UUID,
    current_user: UserSession = Depends(require_permission_return_user("coloquios:gestionar")),
    db: AsyncSession = Depends(get_db),
):
    svc = _build_admin_svc(db, current_user.tenant_id)
    return await svc.metricas_convocatoria(evaluacion_id)


@router.post("/{evaluacion_id}/reservas", response_model=ReservaResponse, status_code=201)
async def reservar_turno(
    evaluacion_id: uuid.UUID,
    body: ReservaRequest,
    current_user: UserSession = Depends(require_permission_return_user("coloquios:reservar")),
    db: AsyncSession = Depends(get_db),
):
    svc = _build_svc(db, current_user.tenant_id)
    return await svc.reservar_turno(evaluacion_id, body.fecha_hora, current_user.user_id, current_user.user_id)


@router.patch("/reservas/{reserva_id}/cancelar", response_model=ReservaResponse)
async def cancelar_reserva(
    reserva_id: uuid.UUID,
    current_user: UserSession = Depends(require_permission_return_user("coloquios:reservar")),
    db: AsyncSession = Depends(get_db),
):
    svc = _build_svc(db, current_user.tenant_id)
    return await svc.cancelar_reserva(reserva_id, current_user.user_id, current_user.user_id)


@router.get("/mis-reservas", response_model=ListResponse[ReservaResponse])
async def mis_reservas(
    current_user: UserSession = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    estado: str = Query(default="Activa"),
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=20, ge=1, le=100),
):
    svc = _build_svc(db, current_user.tenant_id)
    reservas = await svc.listar_mis_reservas(current_user.user_id, estado)
    start = min(offset, len(reservas))
    end = min(start + limit, len(reservas))
    paginated = reservas[start:end]
    return ListResponse(
        items=paginated,
        total=len(reservas),
        offset=offset,
        limit=limit,
    )


@router.post("/{evaluacion_id}/resultados", response_model=ResultadoResponse, status_code=201)
async def registrar_resultado(
    evaluacion_id: uuid.UUID,
    body: ResultadoRequest,
    current_user: UserSession = Depends(require_permission_return_user("coloquios:gestionar")),
    db: AsyncSession = Depends(get_db),
):
    svc = _build_resultado_svc(db, current_user.tenant_id)
    return await svc.registrar_resultado(evaluacion_id, body, current_user.user_id)


@router.get("/{evaluacion_id}/resultados", response_model=ListResponse[ResultadoResponse])
async def listar_resultados(
    evaluacion_id: uuid.UUID,
    current_user: UserSession = Depends(require_permission_return_user("coloquios:gestionar")),
    db: AsyncSession = Depends(get_db),
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=20, ge=1, le=100),
):
    svc = _build_resultado_svc(db, current_user.tenant_id)
    items_data, total = await svc.listar_resultados(evaluacion_id, offset, limit)
    return ListResponse(
        items=[ResultadoResponse(**i) for i in items_data],
        total=total,
        offset=offset,
        limit=limit,
    )


@router.get("/admin/agenda", response_model=ListResponse[ReservaAgendaResponse])
async def agenda_reservas(
    current_user: UserSession = Depends(require_permission_return_user("coloquios:gestionar")),
    db: AsyncSession = Depends(get_db),
    materia_id: uuid.UUID | None = Query(default=None),
    evaluacion_id: uuid.UUID | None = Query(default=None),
    fecha_desde: date | None = Query(default=None),
    fecha_hasta: date | None = Query(default=None),
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=20, ge=1, le=100),
):
    svc = _build_svc(db, current_user.tenant_id)
    filtros = {"offset": offset, "limit": limit}
    if materia_id:
        filtros["materia_id"] = materia_id
    if evaluacion_id:
        filtros["evaluacion_id"] = evaluacion_id
    if fecha_desde:
        filtros["fecha_desde"] = fecha_desde
    if fecha_hasta:
        filtros["fecha_hasta"] = fecha_hasta
    items, total = await svc.agenda_reservas(filtros)
    return ListResponse(
        items=[ReservaAgendaResponse(**i) for i in items],
        total=total,
        offset=offset,
        limit=limit,
    )


@router.get("/admin/consolidado", response_model=ListResponse[ConsolidadoResponse])
async def consolidado(
    current_user: UserSession = Depends(require_permission_return_user("coloquios:gestionar")),
    db: AsyncSession = Depends(get_db),
    materia_id: uuid.UUID | None = Query(default=None),
    cohorte_id: uuid.UUID | None = Query(default=None),
    alumno_id: uuid.UUID | None = Query(default=None),
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=20, ge=1, le=100),
):
    svc = _build_resultado_svc(db, current_user.tenant_id)
    filtros = {"offset": offset, "limit": limit}
    if materia_id:
        filtros["materia_id"] = materia_id
    if cohorte_id:
        filtros["cohorte_id"] = cohorte_id
    if alumno_id:
        filtros["alumno_id"] = alumno_id
    items, total = await svc.consolidado(filtros)
    return ListResponse(
        items=[ConsolidadoResponse(**i) for i in items],
        total=total,
        offset=offset,
        limit=limit,
    )


@router.get("/admin/convocatorias", response_model=ListResponse[EvaluacionResponse])
async def admin_convocatorias(
    current_user: UserSession = Depends(require_permission_return_user("coloquios:gestionar")),
    db: AsyncSession = Depends(get_db),
    materia_id: uuid.UUID | None = Query(default=None),
    cohorte_id: uuid.UUID | None = Query(default=None),
    tipo: str | None = Query(default=None),
    incluir_inactivas: bool = Query(default=False),
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=20, ge=1, le=100),
):
    svc = _build_admin_svc(db, current_user.tenant_id)
    filtros: dict = {"offset": offset, "limit": limit, "incluir_inactivas": incluir_inactivas}
    if materia_id:
        filtros["materia_id"] = materia_id
    if cohorte_id:
        filtros["cohorte_id"] = cohorte_id
    if tipo:
        filtros["tipo"] = tipo
    items, total = await svc.admin_convocatorias(filtros)
    return ListResponse(
        items=[EvaluacionResponse(**i) for i in items],
        total=total,
        offset=offset,
        limit=limit,
    )
