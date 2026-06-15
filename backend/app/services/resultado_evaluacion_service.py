import uuid

from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.audit_codes import AuditAction
from app.repositories.evaluacion_repository import EvaluacionRepository
from app.schemas.evaluaciones import (
    EvaluacionDetailResponse,
    ImportarAlumnosRequest,
    ResultadoRequest,
    ResultadoResponse,
)
from app.services.audit_service import AuditService


class ResultadoEvaluacionService:
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

    async def importar_alumnos(
        self, evaluacion_id: uuid.UUID, data: ImportarAlumnosRequest, actor_id: uuid.UUID,
    ) -> EvaluacionDetailResponse:
        evaluacion = await self._repo.get(evaluacion_id)
        if evaluacion is None:
            raise HTTPException(status_code=404, detail="Evaluacion no encontrada")
        if not evaluacion.activa:
            raise HTTPException(status_code=400, detail="La evaluacion no esta activa")

        if data.modo == "manual":
            if not data.usuario_ids:
                raise HTTPException(status_code=422, detail="usuario_ids requerido en modo manual")
            usuarios_roles = await self._repo.get_usuarios_with_roles(data.usuario_ids)
            for uid in data.usuario_ids:
                usuario, roles = usuarios_roles.get(uid, (None, []))
                if usuario is None:
                    raise HTTPException(status_code=404, detail=f"Usuario {uid} no encontrado")
                if "ALUMNO" not in roles:
                    raise HTTPException(status_code=400, detail=f"Usuario {uid} no tiene rol ALUMNO")
            evaluacion.alumnos_convocados = [str(uid) for uid in data.usuario_ids]
        elif data.modo == "padron":
            if not data.materia_id or not data.cohorte_id:
                raise HTTPException(status_code=422, detail="materia_id y cohorte_id requeridos en modo padron")
            usuario_ids = await self._repo.get_alumnos_from_padron(data.materia_id, data.cohorte_id)
            if not usuario_ids:
                raise HTTPException(status_code=400, detail="No se encontraron alumnos en el padron")
            evaluacion.alumnos_convocados = [str(uid) for uid in usuario_ids]

        await self._session.commit()
        await self._session.refresh(evaluacion)

        await self._audit.log(
            accion=AuditAction.COLOQUIO_CREAR,
            actor_id=actor_id,
            tenant_id=self._tenant_id,
            detalle={
                "evaluacion_id": str(evaluacion_id),
                "operacion": "importar_alumnos",
                "modo": data.modo,
                "cantidad": len(evaluacion.alumnos_convocados),
            },
        )

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

    async def registrar_resultado(
        self, evaluacion_id: uuid.UUID, data: ResultadoRequest, actor_id: uuid.UUID,
    ) -> ResultadoResponse:
        evaluacion = await self._repo.get(evaluacion_id)
        if evaluacion is None:
            raise HTTPException(status_code=404, detail="Evaluacion no encontrada")

        usuario = await self._repo.get_usuario(data.alumno_id)
        if usuario is None:
            raise HTTPException(status_code=404, detail="Alumno no encontrado")

        resultado = await self._repo.upsert_resultado({
            "evaluacion_id": evaluacion_id,
            "alumno_id": data.alumno_id,
            "nota_final": data.nota_final,
        })

        await self._audit.log(
            accion=AuditAction.COLOQUIO_RESULTADO,
            actor_id=actor_id,
            tenant_id=self._tenant_id,
            detalle={
                "resultado_id": str(resultado.id),
                "evaluacion_id": str(evaluacion_id),
                "alumno_id": str(data.alumno_id),
            },
        )

        return ResultadoResponse(
            id=resultado.id,
            evaluacion_id=resultado.evaluacion_id,
            alumno_id=resultado.alumno_id,
            alumno_nombre=usuario.nombre,
            alumno_apellidos=usuario.apellidos,
            nota_final=resultado.nota_final,
        )

    async def listar_resultados(
        self, evaluacion_id: uuid.UUID, offset: int = 0, limit: int = 20,
    ) -> tuple[list[dict], int]:
        resultados = await self._repo.list_resultados(evaluacion_id)
        total = len(resultados)
        page = resultados[offset:offset + limit]
        if not page:
            return [], total
        alumno_ids = list({r.alumno_id for r in page})
        usuarios = await self._repo.get_usuarios_by_ids(alumno_ids)
        items = []
        for r in page:
            usuario = usuarios.get(r.alumno_id)
            items.append({
                "id": r.id,
                "evaluacion_id": r.evaluacion_id,
                "alumno_id": r.alumno_id,
                "alumno_nombre": usuario.nombre if usuario else "",
                "alumno_apellidos": usuario.apellidos if usuario else "",
                "nota_final": r.nota_final,
            })
        return items, total

    async def consolidado(self, filtros: dict) -> tuple[list[dict], int]:
        resultados, total = await self._repo.list_resultados_global(
            materia_id=filtros.get("materia_id"),
            cohorte_id=filtros.get("cohorte_id"),
            alumno_id=filtros.get("alumno_id"),
            offset=filtros.get("offset", 0),
            limit=filtros.get("limit", 20),
        )
        if not resultados:
            return [], total
        ev_ids = list({r.evaluacion_id for r in resultados})
        alumno_ids = list({r.alumno_id for r in resultados})
        evaluaciones = await self._repo.get_evaluaciones_by_ids(ev_ids)
        materia_ids = list({ev.materia_id for ev in evaluaciones.values()})
        materias = await self._repo.get_materias_by_ids(materia_ids)
        usuarios = await self._repo.get_usuarios_by_ids(alumno_ids)
        items = []
        for r in resultados:
            ev = evaluaciones.get(r.evaluacion_id)
            usuario = usuarios.get(r.alumno_id)
            materia = materias.get(ev.materia_id) if ev else None
            items.append({
                "alumno_id": r.alumno_id,
                "alumno_nombre": usuario.nombre if usuario else "",
                "alumno_apellidos": usuario.apellidos if usuario else "",
                "materia_nombre": materia.nombre if materia else "",
                "instancia": ev.instancia if ev else "",
                "nota_final": r.nota_final,
                "fecha_registro": r.created_at,
            })
        return items, total
