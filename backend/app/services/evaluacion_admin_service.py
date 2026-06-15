import uuid

from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.evaluacion_repository import EvaluacionRepository
from app.schemas.evaluaciones import (
    ConvocatoriaMetricasResponse,
    PanelMetricasResponse,
)


class EvaluacionAdminService:
    def __init__(
        self,
        session: AsyncSession,
        tenant_id: uuid.UUID,
    ):
        self._session = session
        self._tenant_id = tenant_id
        self._repo = EvaluacionRepository(session, tenant_id)

    async def metricas_panel(self) -> PanelMetricasResponse:
        total_activas = await self._repo.count_evaluaciones_activas()
        evaluaciones = await self._repo.get_activas_with_convocados()
        total_convocados = sum(len(e.alumnos_convocados or []) for e in evaluaciones)
        total_reservas = await self._repo.count_reservas_activas_global()
        total_resultados = await self._repo.count_resultados_global()

        if total_resultados > 0:
            tasa = 1.0
        else:
            tasa = None

        return PanelMetricasResponse(
            total_convocatorias_activas=total_activas,
            total_convocados=total_convocados,
            total_reservas_activas=total_reservas,
            total_resultados=total_resultados,
            tasa_aprobacion=tasa,
        )

    async def metricas_convocatoria(
        self, evaluacion_id: uuid.UUID,
    ) -> ConvocatoriaMetricasResponse:
        evaluacion = await self._repo.get(evaluacion_id)
        if evaluacion is None:
            raise HTTPException(status_code=404, detail="Evaluacion no encontrada")

        total_reservas = await self._repo.count_reservas_activas_by_evaluacion(evaluacion_id)
        total_resultados = await self._repo.count_resultados_by_evaluacion(evaluacion_id)
        total_cupos = sum(d["cupo"] for d in (evaluacion.cupos_por_dia or []))

        return ConvocatoriaMetricasResponse(
            evaluacion_id=evaluacion_id,
            total_convocados=len(evaluacion.alumnos_convocados or []),
            total_reservas=total_reservas,
            total_resultados=total_resultados,
            cupos_libres=max(0, total_cupos - total_reservas),
        )

    async def admin_convocatorias(self, filtros: dict) -> tuple[list[dict], int]:
        return await self._repo.list_evaluaciones_with_metrics(
            materia_id=filtros.get("materia_id"),
            cohorte_id=filtros.get("cohorte_id"),
            tipo=filtros.get("tipo"),
            incluir_inactivas=filtros.get("incluir_inactivas", False),
            offset=filtros.get("offset", 0),
            limit=filtros.get("limit", 20),
        )
