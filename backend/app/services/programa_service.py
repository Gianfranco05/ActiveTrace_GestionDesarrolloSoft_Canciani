import uuid

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.audit_codes import AuditAction
from app.models.carrera import Carrera
from app.models.cohorte import Cohorte
from app.models.materia import Materia
from app.repositories.programa_materia_repository import ProgramaMateriaRepository
from app.schemas.programas import ProgramaMateriaCreateRequest, ProgramaMateriaResponse


class ProgramaService:
    def __init__(
        self,
        session: AsyncSession,
        repo: ProgramaMateriaRepository,
    ) -> None:
        self._session = session
        self._repo = repo

    async def upload_programa(
        self,
        archivo,
        request: ProgramaMateriaCreateRequest,
        tenant_id: uuid.UUID,
        actor_id: uuid.UUID,
    ) -> ProgramaMateriaResponse:
        content = await archivo.read()
        if not content or len(content) == 0:
            raise HTTPException(status_code=422, detail="File must not be empty")

        await self._validate_materia(request.materia_id, tenant_id)
        await self._validate_carrera(request.carrera_id, tenant_id)
        await self._validate_cohorte(request.cohorte_id, tenant_id)

        referencia = f"store://programas/{uuid.uuid4()}/{archivo.filename}"

        entity = await self._repo.create({
            "materia_id": request.materia_id,
            "carrera_id": request.carrera_id,
            "cohorte_id": request.cohorte_id,
            "titulo": request.titulo,
            "referencia_archivo": referencia,
        })

        if hasattr(self, '_audit') and self._audit:
            await self._audit.log(
                AuditAction.PROGRAMA_SUBIR,
                actor_id, tenant_id,
                detalle={"titulo": request.titulo, "referencia_archivo": referencia},
                materia_id=request.materia_id,
            )

        return ProgramaMateriaResponse.model_validate(entity)

    async def listar(
        self,
        *,
        materia_id: uuid.UUID | None,
        carrera_id: uuid.UUID | None,
        cohorte_id: uuid.UUID | None,
        offset: int,
        limit: int,
        tenant_id: uuid.UUID,
    ) -> tuple[list[ProgramaMateriaResponse], int]:
        items, total = await self._repo.list_by_filters(
            tenant_id,
            materia_id=materia_id,
            carrera_id=carrera_id,
            cohorte_id=cohorte_id,
            offset=offset,
            limit=limit,
        )
        return [ProgramaMateriaResponse.model_validate(item) for item in items], total

    async def obtener(
        self, id: uuid.UUID, tenant_id: uuid.UUID,
    ) -> ProgramaMateriaResponse:
        entity = await self._repo.get_by_id(id, tenant_id)
        if entity is None:
            raise HTTPException(status_code=404, detail="Programa not found")
        return ProgramaMateriaResponse.model_validate(entity)

    async def eliminar(
        self, id: uuid.UUID, tenant_id: uuid.UUID, actor_id: uuid.UUID,
    ) -> None:
        entity = await self._repo.get_by_id(id, tenant_id)
        if entity is None:
            raise HTTPException(status_code=404, detail="Programa not found")
        await self._repo.soft_delete(id, tenant_id)

    async def _validate_materia(self, materia_id: uuid.UUID, tenant_id: uuid.UUID) -> None:
        query = select(Materia).where(
            Materia.id == materia_id,
            Materia.tenant_id == tenant_id,
        )
        result = await self._session.execute(query)
        if result.scalar_one_or_none() is None:
            raise HTTPException(status_code=404, detail="Materia not found")

    async def _validate_carrera(self, carrera_id: uuid.UUID, tenant_id: uuid.UUID) -> None:
        query = select(Carrera).where(
            Carrera.id == carrera_id,
            Carrera.tenant_id == tenant_id,
        )
        result = await self._session.execute(query)
        if result.scalar_one_or_none() is None:
            raise HTTPException(status_code=404, detail="Carrera not found")

    async def _validate_cohorte(self, cohorte_id: uuid.UUID, tenant_id: uuid.UUID) -> None:
        query = select(Cohorte).where(
            Cohorte.id == cohorte_id,
            Cohorte.tenant_id == tenant_id,
        )
        result = await self._session.execute(query)
        if result.scalar_one_or_none() is None:
            raise HTTPException(status_code=404, detail="Cohorte not found")
