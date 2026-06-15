import csv
import io
import uuid

import sqlalchemy as sa
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.audit_codes import AuditAction
from app.models.guardia import Guardia
from app.repositories.guardia_repository import GuardiaRepository
from app.schemas.guardias import GuardiaCreateRequest, GuardiaUpdateRequest
from app.services.audit_service import AuditService


class GuardiaService:
    def __init__(
        self,
        session: AsyncSession,
        tenant_id: uuid.UUID,
        audit_service: AuditService,
    ):
        self._session = session
        self._tenant_id = tenant_id
        self._repo = GuardiaRepository(session, tenant_id)
        self._audit = audit_service

    async def registrar_guardia(
        self,
        request: GuardiaCreateRequest,
        actor_id: uuid.UUID,
        roles: list[str],
    ) -> Guardia:
        from fastapi import HTTPException

        from app.models.asignacion import Asignacion

        if "COORDINADOR" not in roles and "ADMIN" not in roles:
            result = await self._session.execute(
                sa.select(Asignacion).where(
                    Asignacion.id == request.asignacion_id,
                    Asignacion.usuario_id == actor_id,
                    Asignacion.tenant_id == self._tenant_id,
                    Asignacion.deleted_at.is_(None),
                )
            )
            if result.scalar_one_or_none() is None:
                raise HTTPException(
                    status_code=403,
                    detail="No puedes registrar una guardia con esta asignación",
                )

        guardia = Guardia(
            tenant_id=self._tenant_id,
            asignacion_id=request.asignacion_id,
            materia_id=request.materia_id,
            carrera_id=request.carrera_id,
            cohorte_id=request.cohorte_id,
            dia=request.dia.value,
            horario=request.horario,
            comentarios=request.comentarios,
            estado="Pendiente",
        )
        await self._repo.create(guardia)
        await self._session.commit()

        await self._audit.log(
            accion=AuditAction.GUARDIA_REGISTRAR,
            actor_id=actor_id,
            tenant_id=self._tenant_id,
            detalle={
                "guardia_id": str(guardia.id),
                "materia_id": str(request.materia_id),
            },
        )
        return guardia

    async def editar_guardia(
        self,
        guardia_id: uuid.UUID,
        request: GuardiaUpdateRequest,
        actor_id: uuid.UUID,
        roles: list[str],
    ) -> Guardia | None:
        from fastapi import HTTPException

        from app.models.asignacion import Asignacion

        guardia = await self._repo.get_by_id(guardia_id, self._tenant_id)
        if guardia is None:
            return None

        if "COORDINADOR" not in roles and "ADMIN" not in roles:
            result = await self._session.execute(
                sa.select(Asignacion).where(
                    Asignacion.id == guardia.asignacion_id,
                    Asignacion.usuario_id == actor_id,
                    Asignacion.tenant_id == self._tenant_id,
                    Asignacion.deleted_at.is_(None),
                )
            )
            if result.scalar_one_or_none() is None:
                raise HTTPException(
                    status_code=403,
                    detail="No puedes editar esta guardia",
                )

        data = request.model_dump(exclude_none=True)
        for key, value in data.items():
            setattr(guardia, key, value)

        await self._session.commit()

        await self._audit.log(
            accion=AuditAction.GUARDIA_REGISTRAR,
            actor_id=actor_id,
            tenant_id=self._tenant_id,
            detalle={
                "guardia_id": str(guardia_id),
                "campos_modificados": list(data.keys()),
            },
        )
        return guardia

    async def listar_guardias(
        self,
        filtros: dict,
        actor_id: uuid.UUID,
        tenant_id: uuid.UUID,
        roles: list[str],
    ) -> tuple[list[Guardia], int]:
        asignacion_id = None
        if "COORDINADOR" not in roles and "ADMIN" not in roles:
            from app.models.asignacion import Asignacion
            result = await self._session.execute(
                sa.select(Asignacion.id).where(
                    Asignacion.usuario_id == actor_id,
                    Asignacion.tenant_id == tenant_id,
                    Asignacion.deleted_at.is_(None),
                )
            )
            own_ids = [r[0] for r in result.all()]
            if not own_ids:
                return [], 0
            all_guardias = []
            for aid in own_ids:
                chunk, _ = await self._repo.list_by_filters(
                    tenant_id,
                    materia_id=filtros.get("materia_id"),
                    carrera_id=filtros.get("carrera_id"),
                    cohorte_id=filtros.get("cohorte_id"),
                    dia=filtros.get("dia"),
                    estado=filtros.get("estado"),
                    asignacion_id=aid,
                    offset=0,
                    limit=200,
                )
                all_guardias.extend(chunk)
            total = len(all_guardias)
            offset = filtros.get("offset", 0)
            limit = filtros.get("limit", 20)
            return all_guardias[offset:offset + limit], total

        return await self._repo.list_by_filters(
            tenant_id,
            materia_id=filtros.get("materia_id"),
            carrera_id=filtros.get("carrera_id"),
            cohorte_id=filtros.get("cohorte_id"),
            dia=filtros.get("dia"),
            estado=filtros.get("estado"),
            asignacion_id=asignacion_id,
            offset=filtros.get("offset", 0),
            limit=filtros.get("limit", 20),
        )

    async def exportar_guardias(
        self,
        filtros: dict,
        actor_id: uuid.UUID,
        tenant_id: uuid.UUID,
        roles: list[str],
    ) -> str:
        asignacion_id = None
        if "COORDINADOR" not in roles and "ADMIN" not in roles:
            from app.models.asignacion import Asignacion
            result = await self._session.execute(
                sa.select(Asignacion.id).where(
                    Asignacion.usuario_id == actor_id,
                    Asignacion.tenant_id == tenant_id,
                    Asignacion.deleted_at.is_(None),
                )
            )
            own_ids = [r[0] for r in result.all()]
            if not own_ids:
                asignacion_id = uuid.UUID("00000000-0000-0000-0000-000000000000")
            else:
                pass  # handle per-id below

        if asignacion_id is None and "COORDINADOR" not in roles and "ADMIN" not in roles:
            items = []
            for aid in own_ids:
                items.extend(await self._repo.list_for_export(
                    tenant_id,
                    materia_id=filtros.get("materia_id"),
                    carrera_id=filtros.get("carrera_id"),
                    cohorte_id=filtros.get("cohorte_id"),
                    dia=filtros.get("dia"),
                    estado=filtros.get("estado"),
                    asignacion_id=aid,
                ))
        else:
            items = await self._repo.list_for_export(
                tenant_id,
                materia_id=filtros.get("materia_id"),
                carrera_id=filtros.get("carrera_id"),
                cohorte_id=filtros.get("cohorte_id"),
                dia=filtros.get("dia"),
                estado=filtros.get("estado"),
                asignacion_id=asignacion_id,
            )

        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow([
            "id", "materia", "carrera", "cohorte", "dia", "horario",
            "estado", "comentarios", "creada_at", "tutor",
        ])
        for g in items:
            writer.writerow([
                str(g.id),
                str(g.materia_id),
                str(g.carrera_id),
                str(g.cohorte_id),
                g.dia,
                g.horario,
                g.estado,
                g.comentarios or "",
                g.creada_at.isoformat(),
                str(g.asignacion_id),
            ])
        return output.getvalue()
