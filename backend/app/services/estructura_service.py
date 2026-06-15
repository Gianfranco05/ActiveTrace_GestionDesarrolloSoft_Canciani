import uuid

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.carrera import Carrera
from app.repositories.cohorte_repository import CohorteRepository


class CohorteService:
    def __init__(
        self,
        repo: CohorteRepository,
        session: AsyncSession,
        tenant_id: uuid.UUID,
    ) -> None:
        self._repo = repo
        self._session = session
        self._tenant_id = tenant_id

    async def _check_carrera_activa(self, carrera_id: uuid.UUID) -> None:
        query = select(Carrera).where(
            Carrera.id == carrera_id,
            Carrera.tenant_id == self._tenant_id,
        )
        result = await self._session.execute(query)
        carrera = result.scalar_one_or_none()

        if carrera is None:
            raise HTTPException(status_code=404, detail="Carrera not found")

        if carrera.estado != "Activa":
            raise HTTPException(
                status_code=409,
                detail="Carrera must be active to create cohorts",
            )

    async def create(self, data: dict):
        carrera_id = data.get("carrera_id")
        if carrera_id:
            await self._check_carrera_activa(carrera_id)
        return await self._repo.create(data)

    async def update(self, id: uuid.UUID, data: dict):
        if "estado" in data and data["estado"] == "Activa":
            carrera_id = data.get("carrera_id")
            if carrera_id:
                await self._check_carrera_activa(carrera_id)
        return await self._repo.update(id, data)
