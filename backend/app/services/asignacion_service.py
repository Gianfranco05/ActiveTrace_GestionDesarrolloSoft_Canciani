"""Asignacion service — business rules and overlap enforcement."""

import uuid
from datetime import date, datetime

from fastapi import HTTPException
from sqlalchemy import select

from app.core.tenant_aware import get_tenant_scoped

from app.models.asignacion import Asignacion
from app.repositories.asignacion_repository import AsignacionRepository
from app.schemas.asignaciones import AsignacionCreate, AsignacionUpdate


class AsignacionService:
    def __init__(self, repo: AsignacionRepository):
        self._repo = repo

    async def create(self, data: AsignacionCreate) -> Asignacion:
        await self._validate_fk_refs(data)
        await self._check_overlapping(data)
        return await self._repo.create(data.model_dump())

    async def get(self, id: uuid.UUID) -> Asignacion | None:
        return await self._repo.get(id)

    async def update(self, id: uuid.UUID, data: AsignacionUpdate) -> Asignacion | None:
        entity = await self._repo.get(id)
        if entity is None:
            return None
        update_data = data.model_dump(exclude_unset=True)
        return await self._repo.update(id, update_data)

    async def soft_delete(self, id: uuid.UUID) -> bool:
        return await self._repo.soft_delete(id)

    async def list(self, **filters) -> list[Asignacion]:
        return await self._repo.list(**filters)

    async def _validate_fk_refs(self, data: AsignacionCreate) -> None:
        from app.models.rol import Rol
        from app.models.usuario import Usuario

        session = self._repo._session
        tenant_id = self._repo._tenant_id

        usuario = await get_tenant_scoped(session, Usuario, data.usuario_id, tenant_id)
        if usuario is None:
            raise HTTPException(status_code=404, detail="Usuario not found")

        rol = await get_tenant_scoped(session, Rol, data.rol_id, tenant_id)
        if rol is None:
            raise HTTPException(status_code=404, detail="Rol not found")

        if data.materia_id is not None:
            from app.models.materia import Materia
            materia = await get_tenant_scoped(session, Materia, data.materia_id, tenant_id)
            if materia is None:
                raise HTTPException(status_code=404, detail="Materia not found")

        if data.carrera_id is not None:
            from app.models.carrera import Carrera
            carrera = await get_tenant_scoped(session, Carrera, data.carrera_id, tenant_id)
            if carrera is None:
                raise HTTPException(status_code=404, detail="Carrera not found")

        if data.cohorte_id is not None:
            from app.models.cohorte import Cohorte
            cohorte = await get_tenant_scoped(session, Cohorte, data.cohorte_id, tenant_id)
            if cohorte is None:
                raise HTTPException(status_code=404, detail="Cohorte not found")

    async def _check_overlapping(self, data: AsignacionCreate) -> None:
        overlapping = await self._find_overlapping(
            usuario_id=data.usuario_id,
            rol_id=data.rol_id,
            materia_id=data.materia_id,
            carrera_id=data.carrera_id,
            cohorte_id=data.cohorte_id,
            vig_desde=data.vig_desde,
            vig_hasta=data.vig_hasta,
        )
        if overlapping:
            raise HTTPException(
                status_code=409,
                detail="Overlapping vigencia for the same context",
            )

    async def _find_overlapping(
        self,
        usuario_id: uuid.UUID,
        rol_id: uuid.UUID,
        materia_id: uuid.UUID | None,
        carrera_id: uuid.UUID | None,
        cohorte_id: uuid.UUID | None,
        vig_desde: date,
        vig_hasta: date | None,
    ) -> list:
        query = (
            select(Asignacion)
            .where(
                Asignacion.tenant_id == self._repo._tenant_id,
                Asignacion.usuario_id == usuario_id,
                Asignacion.rol_id == rol_id,
                Asignacion.deleted_at.is_(None),
                Asignacion.materia_id == materia_id if materia_id is not None else Asignacion.materia_id.is_(None),
                Asignacion.carrera_id == carrera_id if carrera_id is not None else Asignacion.carrera_id.is_(None),
                Asignacion.cohorte_id == cohorte_id if cohorte_id is not None else Asignacion.cohorte_id.is_(None),
            )
        )
        result = await self._repo._session.execute(query)
        existing = result.scalars().all()
        overlapping = []
        for ex in existing:
            # Normalize incoming and existing vigencias to date for comparison
            if vig_hasta is None:
                ends = date.max
            else:
                ends = vig_hasta

            ex_vig_desde = ex.vig_desde.date() if isinstance(ex.vig_desde, datetime) else ex.vig_desde
            ex_vig_hasta = ex.vig_hasta.date() if isinstance(ex.vig_hasta, datetime) else ex.vig_hasta
            ex_ends = ex_vig_hasta if ex_vig_hasta is not None else date.max

            if vig_desde <= ex_ends and ends >= ex_vig_desde:
                overlapping.append(ex)
        return overlapping
