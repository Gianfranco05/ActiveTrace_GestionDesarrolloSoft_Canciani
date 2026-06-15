import uuid
from datetime import date

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.cohorte import Cohorte
from app.models.materia import Materia
from app.repositories.fecha_academica_repository import FechaAcademicaRepository
from app.schemas.fechas_academicas import (
    FechaAcademicaCreateRequest,
    FechaAcademicaResponse,
    FechaAcademicaUpdateRequest,
)


class FechaAcademicaService:
    def __init__(
        self,
        session: AsyncSession,
        repo: FechaAcademicaRepository,
    ) -> None:
        self._session = session
        self._repo = repo

    async def crear(
        self,
        request: FechaAcademicaCreateRequest,
        tenant_id: uuid.UUID,
        actor_id: uuid.UUID,
    ) -> FechaAcademicaResponse:
        await self._validate_materia(request.materia_id, tenant_id)
        await self._validate_cohorte(request.cohorte_id, tenant_id)

        entity = await self._repo.create({
            "materia_id": request.materia_id,
            "cohorte_id": request.cohorte_id,
            "tipo": request.tipo,
            "numero": request.numero,
            "periodo": request.periodo,
            "fecha": request.fecha,
            "titulo": request.titulo,
        })
        return FechaAcademicaResponse.model_validate(entity)

    async def listar(
        self,
        *,
        materia_id: uuid.UUID | None,
        cohorte_id: uuid.UUID | None,
        tipo: str | None,
        periodo: str | None,
        offset: int,
        limit: int,
        tenant_id: uuid.UUID,
    ) -> tuple[list[FechaAcademicaResponse], int]:
        items, total = await self._repo.list_by_filters(
            tenant_id,
            materia_id=materia_id,
            cohorte_id=cohorte_id,
            tipo=tipo,
            periodo=periodo,
            offset=offset,
            limit=limit,
        )
        return [FechaAcademicaResponse.model_validate(item) for item in items], total

    async def calendario(
        self,
        *,
        tenant_id: uuid.UUID,
        materia_id: uuid.UUID | None = None,
        cohorte_id: uuid.UUID | None = None,
        periodo: str | None = None,
        fecha_desde: date | None = None,
        fecha_hasta: date | None = None,
    ) -> list[FechaAcademicaResponse]:
        items = await self._repo.get_calendario(
            tenant_id,
            materia_id=materia_id,
            cohorte_id=cohorte_id,
            periodo=periodo,
            fecha_desde=fecha_desde,
            fecha_hasta=fecha_hasta,
        )
        return [FechaAcademicaResponse.model_validate(item) for item in items]

    async def actualizar(
        self,
        id: uuid.UUID,
        request: FechaAcademicaUpdateRequest,
        tenant_id: uuid.UUID,
        actor_id: uuid.UUID,
    ) -> FechaAcademicaResponse:
        entity = await self._repo.get_by_id(id, tenant_id)
        if entity is None:
            raise HTTPException(status_code=404, detail="FechaAcademica not found")

        data = request.model_dump(exclude_none=True)
        if not data:
            return FechaAcademicaResponse.model_validate(entity)

        updated = await self._repo.update(id, tenant_id, **data)
        if updated is None:
            raise HTTPException(status_code=404, detail="FechaAcademica not found")
        return FechaAcademicaResponse.model_validate(updated)

    async def eliminar(
        self, id: uuid.UUID, tenant_id: uuid.UUID, actor_id: uuid.UUID,
    ) -> None:
        entity = await self._repo.get_by_id(id, tenant_id)
        if entity is None:
            raise HTTPException(status_code=404, detail="FechaAcademica not found")
        await self._repo.soft_delete(id, tenant_id)

    async def generar_html_lms(
        self,
        materia_id: uuid.UUID,
        cohorte_id: uuid.UUID,
        tenant_id: uuid.UUID,
    ) -> str:
        materia = await self._get_materia(materia_id, tenant_id)
        if materia is None:
            raise HTTPException(status_code=404, detail="Materia not found")

        fechas = await self._repo.get_calendario(
            tenant_id,
            materia_id=materia_id,
            cohorte_id=cohorte_id,
        )

        if not fechas:
            return (
                f'<div style="font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto;">'
                f'<h3 style="color: #334155;">Cronograma de Evaluaciones — {materia.nombre}</h3>'
                f'<p style="color: #64748b; font-style: italic;">'
                f'Aún no hay fechas de evaluación programadas para esta materia y cohorte.'
                f'</p>'
                f'</div>'
            )

        rows = []
        for f in fechas:
            rows.append(
                f'<tr>'
                f'<td style="padding: 8px 12px; border-bottom: 1px solid #e2e8f0;">{f.fecha.isoformat()}</td>'
                f'<td style="padding: 8px 12px; border-bottom: 1px solid #e2e8f0;">{f.tipo}</td>'
                f'<td style="padding: 8px 12px; border-bottom: 1px solid #e2e8f0;">{f.numero}</td>'
                f'<td style="padding: 8px 12px; border-bottom: 1px solid #e2e8f0;">{f.titulo or ""}</td>'
                f'</tr>'
            )

        html = (
            f'<div style="font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto;">'
            f'<h3 style="color: #334155;">Cronograma de Evaluaciones — {materia.nombre}</h3>'
            f'<table style="width: 100%; border-collapse: collapse; color: #1e293b;">'
            f'<thead>'
            f'<tr style="background-color: #f1f5f9; text-align: left;">'
            f'<th style="padding: 8px 12px;">Fecha</th>'
            f'<th style="padding: 8px 12px;">Tipo</th>'
            f'<th style="padding: 8px 12px;">N° Instancia</th>'
            f'<th style="padding: 8px 12px;">Título</th>'
            f'</tr>'
            f'</thead>'
            f'<tbody>'
            f'{"".join(rows)}'
            f'</tbody>'
            f'</table>'
            f'</div>'
        )
        return html

    async def _validate_materia(self, materia_id: uuid.UUID, tenant_id: uuid.UUID) -> None:
        query = select(Materia).where(
            Materia.id == materia_id,
            Materia.tenant_id == tenant_id,
        )
        result = await self._session.execute(query)
        if result.scalar_one_or_none() is None:
            raise HTTPException(status_code=404, detail="Materia not found")

    async def _validate_cohorte(self, cohorte_id: uuid.UUID, tenant_id: uuid.UUID) -> None:
        query = select(Cohorte).where(
            Cohorte.id == cohorte_id,
            Cohorte.tenant_id == tenant_id,
        )
        result = await self._session.execute(query)
        if result.scalar_one_or_none() is None:
            raise HTTPException(status_code=404, detail="Cohorte not found")

    async def _get_materia(self, materia_id: uuid.UUID, tenant_id: uuid.UUID) -> Materia | None:
        query = select(Materia).where(
            Materia.id == materia_id,
            Materia.tenant_id == tenant_id,
        )
        result = await self._session.execute(query)
        return result.scalar_one_or_none()
