import uuid
from datetime import datetime

from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.audit_codes import AuditAction
from app.models.evaluacion import Evaluacion
from app.repositories.evaluacion_repository import EvaluacionRepository
from app.schemas.evaluaciones import (
    EvaluacionCreateRequest,
    EvaluacionDetailResponse,
    EvaluacionResponse,
    EvaluacionUpdateRequest,
    ReservaResponse,
)
from app.services.audit_service import AuditService


class EvaluacionService:
    def __init__(
        self,
        session: AsyncSession,
        tenant_id: uuid.UUID,
        audit_service: AuditService,
    ):
        self._session = session
        self._tenant_id = tenant_id
        self._repo = EvaluacionRepository(session, tenant_id)
        self._audit = audit_service

    async def crear(
        self, data: EvaluacionCreateRequest, actor_id: uuid.UUID,
    ) -> EvaluacionResponse:
        materias = await self._repo.get_materias_by_ids([data.materia_id])
        materia = materias.get(data.materia_id)
        if materia is None:
            raise HTTPException(status_code=404, detail="Materia no encontrada")

        cohortes = await self._repo.get_cohortes_by_ids([data.cohorte_id])
        cohorte = cohortes.get(data.cohorte_id)
        if cohorte is None:
            raise HTTPException(status_code=404, detail="Cohorte no encontrada")

        fechas = [d.fecha for d in data.cupos_por_dia]
        if len(fechas) != len(set(fechas)):
            raise HTTPException(status_code=422, detail="No puede haber fechas duplicadas en cupos_por_dia")

        cupos = [{"fecha": str(d.fecha), "cupo": d.cupo} for d in data.cupos_por_dia]

        evaluacion = Evaluacion(
            tenant_id=self._tenant_id,
            materia_id=data.materia_id,
            cohorte_id=data.cohorte_id,
            tipo=data.tipo,
            instancia=data.instancia,
            cupos_por_dia=cupos,
            alumnos_convocados=[],
            activa=True,
        )
        await self._repo.create(evaluacion)
        await self._session.commit()

        await self._audit.log(
            accion=AuditAction.COLOQUIO_CREAR,
            actor_id=actor_id,
            tenant_id=self._tenant_id,
            detalle={"evaluacion_id": str(evaluacion.id), "operacion": "crear"},
        )

        return EvaluacionResponse(
            id=evaluacion.id,
            materia_id=evaluacion.materia_id,
            materia_nombre=materia.nombre,
            cohorte_id=evaluacion.cohorte_id,
            cohorte_nombre=cohorte.nombre,
            tipo=evaluacion.tipo,
            instancia=evaluacion.instancia,
            cupos_por_dia=evaluacion.cupos_por_dia,
            activa=evaluacion.activa,
            total_convocados=0,
            total_reservas=0,
            total_resultados=0,
            cupos_libres=sum(d["cupo"] for d in cupos),
        )

    async def actualizar(
        self, evaluacion_id: uuid.UUID, data: EvaluacionUpdateRequest, actor_id: uuid.UUID,
    ) -> EvaluacionResponse:
        evaluacion = await self._repo.get(evaluacion_id)
        if evaluacion is None:
            raise HTTPException(status_code=404, detail="Evaluacion no encontrada")

        if data.instancia is not None:
            evaluacion.instancia = data.instancia
        if data.cupos_por_dia is not None:
            evaluacion.cupos_por_dia = [{"fecha": str(d.fecha), "cupo": d.cupo} for d in data.cupos_por_dia]
        if data.activa is not None:
            evaluacion.activa = data.activa

        await self._session.commit()
        await self._session.refresh(evaluacion)

        materias = await self._repo.get_materias_by_ids([evaluacion.materia_id])
        materia = materias.get(evaluacion.materia_id)
        cohortes = await self._repo.get_cohortes_by_ids([evaluacion.cohorte_id])
        cohorte = cohortes.get(evaluacion.cohorte_id)

        res_count = await self._repo.count_reservas_activas_by_evaluacion(evaluacion.id)
        res_filt_count = await self._repo.count_resultados_by_evaluacion(evaluacion.id)

        total_cupos = sum(d["cupo"] for d in (evaluacion.cupos_por_dia or []))
        cupos_libres = max(0, total_cupos - res_count)

        await self._audit.log(
            accion=AuditAction.COLOQUIO_CREAR,
            actor_id=actor_id,
            tenant_id=self._tenant_id,
            detalle={"evaluacion_id": str(evaluacion_id), "operacion": "actualizar"},
        )

        return EvaluacionResponse(
            id=evaluacion.id,
            materia_id=evaluacion.materia_id,
            materia_nombre=materia.nombre if materia else "",
            cohorte_id=evaluacion.cohorte_id,
            cohorte_nombre=cohorte.nombre if cohorte else "",
            tipo=evaluacion.tipo,
            instancia=evaluacion.instancia,
            cupos_por_dia=evaluacion.cupos_por_dia,
            activa=evaluacion.activa,
            total_convocados=len(evaluacion.alumnos_convocados or []),
            total_reservas=res_count,
            total_resultados=res_filt_count,
            cupos_libres=cupos_libres,
        )

    async def obtener(self, evaluacion_id: uuid.UUID) -> EvaluacionDetailResponse:
        evaluacion = await self._repo.get(evaluacion_id)
        if evaluacion is None:
            raise HTTPException(status_code=404, detail="Evaluacion no encontrada")
        return EvaluacionDetailResponse(
            id=evaluacion.id,
            materia_id=evaluacion.materia_id,
            cohorte_id=evaluacion.cohorte_id,
            tipo=evaluacion.tipo,
            instancia=evaluacion.instancia,
            cupos_por_dia=evaluacion.cupos_por_dia,
            activa=evaluacion.activa,
            alumnos_convocados=evaluacion.alumnos_convocados or [],
        )

    async def listar(self, filtros: dict) -> tuple[list[dict], int]:
        return await self._repo.list_evaluaciones_with_metrics(
            materia_id=filtros.get("materia_id"),
            cohorte_id=filtros.get("cohorte_id"),
            tipo=filtros.get("tipo"),
            activa=filtros.get("activa"),
            offset=filtros.get("offset", 0),
            limit=filtros.get("limit", 20),
        )

    async def reservar_turno(
        self,
        evaluacion_id: uuid.UUID,
        fecha_hora: datetime,
        actor_id: uuid.UUID,
        alumno_id: uuid.UUID,
    ) -> ReservaResponse:
        evaluacion = await self._repo.get(evaluacion_id)
        if evaluacion is None:
            raise HTTPException(status_code=404, detail="Evaluacion no encontrada")
        if not evaluacion.activa:
            raise HTTPException(status_code=400, detail="La evaluacion no esta activa")

        convocados_str = [str(uid) for uid in (evaluacion.alumnos_convocados or [])]
        if str(alumno_id) not in convocados_str:
            raise HTTPException(status_code=403, detail="Alumno no convocado")

        fecha = fecha_hora.date()
        dia_cupo = next(
            (d for d in evaluacion.cupos_por_dia if d.get("fecha") == str(fecha)),
            None,
        )
        if dia_cupo is None:
            raise HTTPException(status_code=400, detail="Fecha no disponible")

        activas = await self._repo.count_reservas_activas(evaluacion_id, fecha)
        if activas >= dia_cupo["cupo"]:
            raise HTTPException(status_code=409, detail="Cupo lleno")

        existente = await self._repo.get_reserva_activa(evaluacion_id, alumno_id)
        if existente:
            raise HTTPException(status_code=409, detail="Ya tiene una reserva activa")

        reserva = await self._repo.create_reserva({
            "evaluacion_id": evaluacion_id,
            "alumno_id": alumno_id,
            "fecha_hora": fecha_hora,
        })

        await self._audit.log(
            accion=AuditAction.COLOQUIO_RESERVAR,
            actor_id=actor_id,
            tenant_id=self._tenant_id,
            detalle={
                "reserva_id": str(reserva.id),
                "evaluacion_id": str(evaluacion_id),
                "alumno_id": str(alumno_id),
            },
        )

        return ReservaResponse(
            id=reserva.id,
            evaluacion_id=reserva.evaluacion_id,
            alumno_id=reserva.alumno_id,
            fecha_hora=reserva.fecha_hora,
            estado=reserva.estado,
        )

    async def cancelar_reserva(
        self, reserva_id: uuid.UUID, actor_id: uuid.UUID, alumno_id: uuid.UUID,
    ) -> ReservaResponse:
        reserva = await self._repo.get_reserva(reserva_id)
        if reserva is None:
            raise HTTPException(status_code=404, detail="Reserva no encontrada")
        if str(reserva.alumno_id) != str(alumno_id):
            raise HTTPException(status_code=403, detail="No puedes cancelar una reserva ajena")
        if reserva.estado != "Activa":
            raise HTTPException(status_code=409, detail="La reserva no esta activa")

        reserva.estado = "Cancelada"
        await self._session.commit()
        await self._session.refresh(reserva)

        await self._audit.log(
            accion=AuditAction.COLOQUIO_CANCELAR,
            actor_id=actor_id,
            tenant_id=self._tenant_id,
            detalle={
                "reserva_id": str(reserva_id),
                "evaluacion_id": str(reserva.evaluacion_id),
                "alumno_id": str(alumno_id),
            },
        )

        return ReservaResponse(
            id=reserva.id,
            evaluacion_id=reserva.evaluacion_id,
            alumno_id=reserva.alumno_id,
            fecha_hora=reserva.fecha_hora,
            estado=reserva.estado,
        )

    async def listar_mis_reservas(
        self, alumno_id: uuid.UUID, estado: str = "Activa",
    ) -> list[ReservaResponse]:
        reservas = await self._repo.list_reservas_by_alumno(alumno_id, estado)
        return [
            ReservaResponse(
                id=res.id,
                evaluacion_id=res.evaluacion_id,
                alumno_id=res.alumno_id,
                fecha_hora=res.fecha_hora,
                estado=res.estado,
            )
            for res in reservas
        ]

    async def agenda_reservas(self, filtros: dict) -> tuple[list[dict], int]:
        reservas, total = await self._repo.list_reservas_global(
            materia_id=filtros.get("materia_id"),
            evaluacion_id=filtros.get("evaluacion_id"),
            fecha_desde=filtros.get("fecha_desde"),
            fecha_hasta=filtros.get("fecha_hasta"),
            offset=filtros.get("offset", 0),
            limit=filtros.get("limit", 20),
        )
        if not reservas:
            return [], total

        ev_ids = list({r.evaluacion_id for r in reservas})
        alumno_ids = list({r.alumno_id for r in reservas})
        evaluaciones = await self._repo.get_evaluaciones_by_ids(ev_ids)
        materia_ids = list({ev.materia_id for ev in evaluaciones.values()})
        cohorte_ids = list({ev.cohorte_id for ev in evaluaciones.values()})
        materias = await self._repo.get_materias_by_ids(materia_ids)
        cohortes = await self._repo.get_cohortes_by_ids(cohorte_ids)
        usuarios = await self._repo.get_usuarios_by_ids(alumno_ids)

        items = []
        for r in reservas:
            ev = evaluaciones.get(r.evaluacion_id)
            usuario = usuarios.get(r.alumno_id)
            materia = materias.get(ev.materia_id) if ev else None
            cohorte = cohortes.get(ev.cohorte_id) if ev else None
            items.append({
                "id": r.id,
                "evaluacion_id": r.evaluacion_id,
                "materia_nombre": materia.nombre if materia else "",
                "cohorte_nombre": cohorte.nombre if cohorte else "",
                "instancia": ev.instancia if ev else "",
                "alumno_nombre": usuario.nombre if usuario else "",
                "alumno_apellidos": usuario.apellidos if usuario else "",
                "fecha_hora": r.fecha_hora,
                "estado": r.estado,
            })
        return items, total
