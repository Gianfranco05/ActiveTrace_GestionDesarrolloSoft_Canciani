"""EquipoService — team/equipo business logic over Asignacion model."""

import csv
import io
import uuid
from datetime import date

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.audit_codes import AuditAction
from app.core.tenant_aware import get_tenant_scoped
from app.models.asignacion import Asignacion
from app.models.carrera import Carrera
from app.models.cohorte import Cohorte
from app.models.materia import Materia
from app.models.usuario import Usuario
from app.repositories.asignacion_repository import AsignacionRepository
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
from app.services.audit_service import AuditService


def _as_date(val):
    """Normalize a date/datetime value to date (DB may return datetime for Date columns)."""
    if val is None:
        return None
    return val.date() if hasattr(val, 'date') else val


def _asignacion_response(a: Asignacion) -> AsignacionResponse:
    """Build AsignacionResponse with rol_nombre resolved from eager-loaded relationship."""
    return AsignacionResponse(
        id=a.id,
        tenant_id=a.tenant_id,
        usuario_id=a.usuario_id,
        rol_id=a.rol_id,
        rol_nombre=a.rol.nombre if a.rol else str(a.rol_id),
        materia_id=a.materia_id,
        carrera_id=a.carrera_id,
        cohorte_id=a.cohorte_id,
        comisiones=a.comisiones,
        responsable_id=a.responsable_id,
        vig_desde=_as_date(a.vig_desde),
        vig_hasta=_as_date(a.vig_hasta) if a.vig_hasta else None,
        estado_vigencia=a.estado_vigencia,
        created_at=a.created_at,
        updated_at=a.updated_at,
    )


class EquipoService:
    def __init__(
        self,
        session: AsyncSession,
        audit_service: AuditService,
        tenant_id: uuid.UUID,
    ):
        self._session = session
        self._repo = AsignacionRepository(session, tenant_id)
        self._audit = audit_service
        self._tenant_id = tenant_id

    async def listar_mis_equipos(
        self, usuario_id: uuid.UUID, tenant_id: uuid.UUID, filtros: dict
    ) -> list[AsignacionResponse]:
        all_asignaciones = await self._repo.get_by_usuario(usuario_id)

        estado = filtros.get("estado", "Vigente")

        if estado == "Vigente":
            today = date.today()
            filtered = [
                a for a in all_asignaciones
                if _as_date(a.vig_desde) <= today
                and a.deleted_at is None
                and (_as_date(a.vig_hasta) is None or _as_date(a.vig_hasta) >= today)
            ]
        elif estado == "Vencida":
            today = date.today()
            filtered = [
                a for a in all_asignaciones
                if a.vig_hasta is not None and _as_date(a.vig_hasta) < today
                and a.deleted_at is None
            ]
        elif estado == "Futuro":
            today = date.today()
            filtered = [
                a for a in all_asignaciones
                if _as_date(a.vig_desde) > today
                and a.deleted_at is None
            ]
        else:
            filtered = [a for a in all_asignaciones if a.deleted_at is None]

        if filtros.get("materia_id"):
            filtered = [a for a in filtered if str(a.materia_id) == str(filtros["materia_id"])]
        if filtros.get("rol_id"):
            filtered = [a for a in filtered if str(a.rol_id) == str(filtros["rol_id"])]
        if filtros.get("carrera_id"):
            filtered = [a for a in filtered if str(a.carrera_id) == str(filtros["carrera_id"])]
        if filtros.get("cohorte_id"):
            filtered = [a for a in filtered if str(a.cohorte_id) == str(filtros["cohorte_id"])]

        return [_asignacion_response(a) for a in filtered]

    async def listar_mis_materias(
        self, usuario_id: uuid.UUID
    ) -> list[MisMateriasResponse]:
        all_asignaciones = await self._repo.get_by_usuario(usuario_id)

        today = date.today()
        vigentes = [
            a for a in all_asignaciones
            if a.deleted_at is None
            and a.materia_id is not None
            and _as_date(a.vig_desde) <= today
            and (a.vig_hasta is None or _as_date(a.vig_hasta) >= today)
        ]

        seen: dict[uuid.UUID, Asignacion] = {}
        for a in vigentes:
            if a.materia_id not in seen:
                seen[a.materia_id] = a

        result: list[MisMateriasResponse] = []
        for mid, a in seen.items():
            nombre = await self._resolve_nombre_materia(mid)
            result.append(MisMateriasResponse(
                id=mid,
                nombre=nombre or "",
                comision=a.comisiones,
            ))

        return result

    async def listar_equipos(self, tenant_id: uuid.UUID) -> list[EquipoResponse]:
        groups = await self._repo.get_equipos_agrupados(tenant_id)
        items = []
        for g in groups:
            nombre_materia = await self._resolve_nombre_materia(g.materia_id) or ""
            nombre_carrera = await self._resolve_nombre_carrera(g.carrera_id) or ""
            nombre_cohorte = await self._resolve_nombre_cohorte(g.cohorte_id) or ""
            items.append(EquipoResponse(
                materia_id=g.materia_id,
                carrera_id=g.carrera_id,
                cohorte_id=g.cohorte_id,
                materia_nombre=nombre_materia,
                carrera_nombre=nombre_carrera,
                cohorte_nombre=nombre_cohorte,
                total_asignaciones=g.count,
            ))
        return items

    async def obtener_equipo(
        self, materia_id: uuid.UUID, carrera_id: uuid.UUID, cohorte_id: uuid.UUID
    ) -> EquipoDetailResponse:
        asignaciones = await self._repo.get_equipo(materia_id, carrera_id, cohorte_id)
        return EquipoDetailResponse(
            materia_id=materia_id,
            carrera_id=carrera_id,
            cohorte_id=cohorte_id,
            asignaciones=[_asignacion_response(a) for a in asignaciones],
        )

    async def asignacion_masiva(
        self, request: AsignacionMasivaRequest, actor_id: uuid.UUID
    ) -> list[AsignacionResponse]:
        for uid in request.usuario_ids:
            user = await get_tenant_scoped(self._session, Usuario, uid, self._tenant_id)
            if user is None:
                from fastapi import HTTPException
                raise HTTPException(status_code=404, detail=f"Usuario {uid} not found")

        new_asignaciones = []
        for uid in request.usuario_ids:
            a = Asignacion(
                tenant_id=self._tenant_id,
                usuario_id=uid,
                rol_id=request.rol_id,
                materia_id=request.materia_id,
                carrera_id=request.carrera_id,
                cohorte_id=request.cohorte_id,
                comisiones=request.comisiones,
                vig_desde=request.vig_desde,
                vig_hasta=request.vig_hasta,
            )
            new_asignaciones.append(a)

        try:
            created = await self._repo.bulk_create(new_asignaciones)
        except Exception:
            await self._session.rollback()
            from fastapi import HTTPException
            raise HTTPException(status_code=409, detail="Unique constraint violation or duplicate assignment") from None

        await self._audit.log(
            accion=AuditAction.ASIGNACION_MODIFICAR,
            actor_id=actor_id,
            tenant_id=self._tenant_id,
            detalle={
                "operacion": "masiva",
                "materia_id": str(request.materia_id),
                "carrera_id": str(request.carrera_id),
                "cohorte_id": str(request.cohorte_id),
                "filas_afectadas": len(created),
            },
            filas_afectadas=len(created),
        )

        return [_asignacion_response(a) for a in created]

    async def clonar_equipo(
        self, request: ClonarRequest, actor_id: uuid.UUID
    ) -> EquipoDetailResponse:
        origen = await self._repo.get_equipo(
            request.origen_materia_id,
            request.origen_carrera_id,
            request.origen_cohorte_id,
        )

        today = date.today()
        vigentes = [
            a for a in origen
            if a.deleted_at is None
            and _as_date(a.vig_desde) <= today
            and (a.vig_hasta is None or _as_date(a.vig_hasta) >= today)
        ]

        if not vigentes:
            from fastapi import HTTPException
            raise HTTPException(status_code=404, detail="Source equipo has no active assignments")

        old_to_new: dict[uuid.UUID, uuid.UUID] = {}
        new_asignaciones: list[Asignacion] = []

        for a in vigentes:
            new_a = Asignacion(
                tenant_id=self._tenant_id,
                usuario_id=a.usuario_id,
                rol_id=a.rol_id,
                materia_id=request.destino_materia_id,
                carrera_id=request.destino_carrera_id,
                cohorte_id=request.destino_cohorte_id,
                comisiones=a.comisiones,
                vig_desde=request.nueva_vig_desde,
                vig_hasta=request.nueva_vig_hasta,
            )
            new_asignaciones.append(new_a)
            old_to_new[a.id] = None  # placeholder

        try:
            created = await self._repo.bulk_create(new_asignaciones)
        except Exception:
            await self._session.rollback()
            from fastapi import HTTPException
            raise HTTPException(status_code=409, detail="Unique constraint violation in destination") from None

        for orig, new in zip(vigentes, created, strict=True):
            old_to_new[orig.id] = new.id

        for orig, new in zip(vigentes, created, strict=True):
            if orig.responsable_id and orig.responsable_id in old_to_new:
                new.responsable_id = old_to_new[orig.responsable_id]
                self._session.add(new)

        if any(orig.responsable_id and orig.responsable_id in old_to_new for orig in vigentes):
            await self._session.commit()
            for a in created:
                await self._session.refresh(a)

        await self._audit.log(
            accion=AuditAction.ASIGNACION_MODIFICAR,
            actor_id=actor_id,
            tenant_id=self._tenant_id,
            detalle={
                "operacion": "clonar",
                "materia_id": str(request.destino_materia_id),
                "carrera_id": str(request.destino_carrera_id),
                "cohorte_id": str(request.destino_cohorte_id),
                "filas_afectadas": len(created),
            },
            filas_afectadas=len(created),
        )

        return EquipoDetailResponse(
            materia_id=request.destino_materia_id,
            carrera_id=request.destino_carrera_id,
            cohorte_id=request.destino_cohorte_id,
            asignaciones=[_asignacion_response(a) for a in created],
        )

    async def modificar_vigencia(
        self,
        materia_id: uuid.UUID,
        carrera_id: uuid.UUID,
        cohorte_id: uuid.UUID,
        request: VigenciaUpdateRequest,
        actor_id: uuid.UUID,
    ) -> EquipoDetailResponse:
        if request.vig_hasta and request.vig_desde > request.vig_hasta:
            raise ValueError("vig_desde must be before vig_hasta")

        existing = await self._repo.get_equipo(materia_id, carrera_id, cohorte_id)
        if not existing:
            from fastapi import HTTPException
            raise HTTPException(status_code=404, detail="Equipo not found")

        updated_count = await self._repo.update_vigencia_batch(
            (materia_id, carrera_id, cohorte_id),
            request.vig_desde,
            request.vig_hasta,
        )

        await self._audit.log(
            accion=AuditAction.ASIGNACION_MODIFICAR,
            actor_id=actor_id,
            tenant_id=self._tenant_id,
            detalle={
                "operacion": "vigencia",
                "materia_id": str(materia_id),
                "carrera_id": str(carrera_id),
                "cohorte_id": str(cohorte_id),
                "filas_afectadas": updated_count,
            },
            filas_afectadas=updated_count,
        )

        updated = await self._repo.get_equipo(materia_id, carrera_id, cohorte_id)
        return EquipoDetailResponse(
            materia_id=materia_id,
            carrera_id=carrera_id,
            cohorte_id=cohorte_id,
            asignaciones=[_asignacion_response(a) for a in updated],
        )

    async def exportar_equipo(
        self, materia_id: uuid.UUID, carrera_id: uuid.UUID, cohorte_id: uuid.UUID
    ) -> str:
        rows = await self._repo.get_equipo_with_relations(materia_id, carrera_id, cohorte_id)
        if not rows:
            from fastapi import HTTPException
            raise HTTPException(status_code=404, detail="Equipo not found")

        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow([
            "usuario_id", "nombre", "apellidos", "rol",
            "materia", "carrera", "cohorte", "comisiones",
            "vig_desde", "vig_hasta", "estado_vigencia",
        ])

        for r in rows:
            a = r["asignacion"]
            usr = r["usuario"]
            rol = r["rol"]
            mat = r["materia"]
            car = r["carrera"]
            coh = r["cohorte"]
            writer.writerow([
                str(a.usuario_id),
                usr.nombre if usr else "",
                usr.apellidos if usr else "",
                rol.nombre if rol else "",
                mat.nombre if mat else "",
                car.nombre if car else "",
                coh.nombre if coh else "",
                a.comisiones or "",
                a.vig_desde.isoformat(),
                a.vig_hasta.isoformat() if a.vig_hasta else "",
                a.estado_vigencia,
            ])

        return output.getvalue()

    async def buscar_usuarios(
        self, query: str, tenant_id: uuid.UUID, limit: int = 20
    ) -> list[UsuarioSearchResponse]:
        users = await self._repo.search_usuarios(query, tenant_id, limit)
        return [UsuarioSearchResponse.model_validate(u) for u in users]

    async def _resolve_nombre_materia(self, materia_id) -> str | None:
        m = await get_tenant_scoped(self._session, Materia, materia_id, self._tenant_id)
        return m.nombre if m else None

    async def _resolve_nombre_carrera(self, carrera_id) -> str | None:
        c = await get_tenant_scoped(self._session, Carrera, carrera_id, self._tenant_id)
        return c.nombre if c else None

    async def _resolve_nombre_cohorte(self, cohorte_id) -> str | None:
        c = await get_tenant_scoped(self._session, Cohorte, cohorte_id, self._tenant_id)
        return c.nombre if c else None
