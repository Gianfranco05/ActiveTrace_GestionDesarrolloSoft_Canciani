"""Analisis router — endpoints de análisis académico y monitoreo."""

import csv
import io
from datetime import date, datetime
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Request
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.audit_codes import AuditAction
from app.core.dependencies import UserSession, get_db, require_permission_return_user
from app.repositories.audit_repository import AuditLogRepository
from app.schemas.analisis import (
    AlumnoAtrasado,
    AtrasadosResponse,
    MonitorCoordinacionRow,
    MonitorGeneralRow,
    MonitorSeguimientoRow,
    NotaFinalRow,
    NotasFinalesResponse,
    RankingResponse,
    RankingRow,
    ReporteMateria,
)
from app.services.analisis.atrasados_service import AtrasadosService
from app.services.analisis.monitores_service import MonitoresService
from app.services.analisis.ranking_service import NotasFinalesService, RankingService
from app.services.analisis.reportes_service import ExportService, ReportesService
from app.services.audit_service import AuditService

router = APIRouter(prefix="/api/analisis", tags=["Analisis"])


def _audit_svc(db: AsyncSession, tenant_id: UUID) -> AuditService:
    return AuditService(db, AuditLogRepository(db, tenant_id))


@router.get("/atrasados", response_model=AtrasadosResponse)
async def get_atrasados(
    request: Request,
    materia_id: UUID | None = Query(None),
    cohorte_id: UUID | None = Query(None),
    min_faltantes: int | None = Query(None),
    max_porcentaje: int | None = Query(None),
    db: AsyncSession = Depends(get_db),
    session: UserSession = Depends(require_permission_return_user("atrasados:ver")),
):
    raw = await AtrasadosService(db, session.tenant_id).get_atrasados(
        materia_id=materia_id, cohorte_id=cohorte_id,
        min_faltantes=min_faltantes, max_porcentaje=max_porcentaje,
    )
    items = [AlumnoAtrasado.model_validate(r) for r in raw]
    await _audit_svc(db, session.tenant_id).log(
        accion=AuditAction.ANALISIS_ATRASADOS,
        actor_id=session.user_id,
        tenant_id=session.tenant_id,
        ip=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
    )
    return AtrasadosResponse(items=items, total=len(items))


@router.get("/ranking", response_model=RankingResponse)
async def get_ranking(
    request: Request,
    materia_id: UUID = Query(...),
    cohorte_id: UUID | None = Query(None),
    db: AsyncSession = Depends(get_db),
    session: UserSession = Depends(require_permission_return_user("atrasados:ver")),
):
    raw = await RankingService(db, session.tenant_id).get_ranking(materia_id, cohorte_id)
    items = [RankingRow.model_validate(r) for r in raw]
    total_aprobados = sum(1 for r in raw if r.get("porcentaje", 0) > 0)
    await _audit_svc(db, session.tenant_id).log(
        accion=AuditAction.ANALISIS_RANKING,
        actor_id=session.user_id,
        tenant_id=session.tenant_id,
        detalle={"materia_id": str(materia_id), "cohorte_id": str(cohorte_id) if cohorte_id else None},
        ip=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
    )
    return RankingResponse(items=items, total_aprobados=total_aprobados,
                           materia_id=materia_id, cohorte_id=cohorte_id)


@router.get("/reportes/materia/{materia_id}", response_model=ReporteMateria)
async def get_reporte(
    request: Request,
    materia_id: UUID,
    db: AsyncSession = Depends(get_db),
    session: UserSession = Depends(require_permission_return_user("atrasados:ver")),
):
    data = await ReportesService(db, session.tenant_id).get_reporte(materia_id)
    await _audit_svc(db, session.tenant_id).log(
        accion=AuditAction.ANALISIS_REPORTE,
        actor_id=session.user_id,
        tenant_id=session.tenant_id,
        detalle={"materia_id": str(materia_id)},
        ip=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
    )
    return ReporteMateria.model_validate(data)


@router.get("/notas-finales", response_model=NotasFinalesResponse)
async def get_notas_finales(
    request: Request,
    materia_id: UUID = Query(...),
    cohorte_id: UUID | None = Query(None),
    db: AsyncSession = Depends(get_db),
    session: UserSession = Depends(require_permission_return_user("atrasados:ver")),
):
    raw = await NotasFinalesService(db, session.tenant_id).get_notas(materia_id, cohorte_id)
    items = [NotaFinalRow.model_validate(r) for r in raw]
    await _audit_svc(db, session.tenant_id).log(
        accion=AuditAction.ANALISIS_NOTAS_FINALES,
        actor_id=session.user_id,
        tenant_id=session.tenant_id,
        detalle={"materia_id": str(materia_id), "cohorte_id": str(cohorte_id) if cohorte_id else None},
        ip=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
    )
    return NotasFinalesResponse(items=items, materia_id=materia_id, cohorte_id=cohorte_id)


@router.get("/export/tps-sin-corregir")
async def export_tps_sin_corregir(
    request: Request,
    materia_id: UUID = Query(...),
    cohorte_id: UUID | None = Query(None),
    db: AsyncSession = Depends(get_db),
    session: UserSession = Depends(require_permission_return_user("atrasados:ver")),
):
    rows = await ExportService(db, session.tenant_id).export_tps_sin_corregir(materia_id, cohorte_id)

    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(["Alumno", "Actividad", "Cátedra"])
    for r in rows:
        writer.writerow([r["alumno"], r["actividad"], r["catedra"]])
    buf.seek(0)

    await _audit_svc(db, session.tenant_id).log(
        accion=AuditAction.ANALISIS_EXPORT_TPS,
        actor_id=session.user_id,
        tenant_id=session.tenant_id,
        detalle={"materia_id": str(materia_id), "cohorte_id": str(cohorte_id), "filas": len(rows)},
        ip=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
    )
    return StreamingResponse(
        iter([buf.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=tps-sin-corregir-{date.today()}.csv"},
    )


@router.get("/monitor/general", response_model=list[MonitorGeneralRow])
async def get_monitor_general(
    request: Request,
    db: AsyncSession = Depends(get_db),
    session: UserSession = Depends(require_permission_return_user("atrasados:ver")),
    materia_id: UUID | None = Query(None),
    alumno: str | None = Query(None),
    correo: str | None = Query(None),
    comision: str | None = Query(None),
    regional: str | None = Query(None),
    actividad: str | None = Query(None),
    min_actividades: int | None = Query(None),
    fecha_desde: date | None = Query(None),
    fecha_hasta: date | None = Query(None),
):
    items = await MonitoresService(db, session.tenant_id).get_general()
    await _audit_svc(db, session.tenant_id).log(
        accion=AuditAction.ANALISIS_MONITOR,
        actor_id=session.user_id,
        tenant_id=session.tenant_id,
        detalle={"tipo": "general"},
        ip=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
    )
    return items


@router.get("/monitor/seguimiento", response_model=list[MonitorSeguimientoRow])
async def get_monitor_seguimiento(
    request: Request,
    materia_id: UUID | None = Query(None),
    docente_id: UUID | None = Query(None),
    regional: str | None = Query(None),
    fecha_desde: date | None = Query(None),
    fecha_hasta: date | None = Query(None),
    minimo_actividades: int | None = Query(None),
    db: AsyncSession = Depends(get_db),
    session: UserSession = Depends(require_permission_return_user("atrasados:ver")),
):
    items = await MonitoresService(db, session.tenant_id).get_seguimiento(
        materia_id=materia_id, docente_id=docente_id, regional=regional,
        fecha_desde=fecha_desde, fecha_hasta=fecha_hasta,
        minimo_actividades=minimo_actividades,
    )
    await _audit_svc(db, session.tenant_id).log(
        accion=AuditAction.ANALISIS_MONITOR,
        actor_id=session.user_id,
        tenant_id=session.tenant_id,
        detalle={"tipo": "seguimiento", "materia_id": str(materia_id)},
        ip=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
    )
    return items


@router.get("/monitor/coordinacion", response_model=list[MonitorCoordinacionRow])
async def get_monitor_coordinacion(
    request: Request,
    desde: datetime | None = Query(None),
    hasta: datetime | None = Query(None),
    materia_id: UUID | None = Query(None),
    db: AsyncSession = Depends(get_db),
    session: UserSession = Depends(require_permission_return_user("atrasados:ver")),
):
    items = await MonitoresService(db, session.tenant_id).get_coordinacion(
        desde=desde, hasta=hasta, materia_id=materia_id,
    )
    await _audit_svc(db, session.tenant_id).log(
        accion=AuditAction.ANALISIS_MONITOR,
        actor_id=session.user_id,
        tenant_id=session.tenant_id,
        detalle={"tipo": "coordinacion"},
        ip=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
    )
    return items
