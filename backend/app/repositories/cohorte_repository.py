from uuid import UUID

from sqlalchemy import select

from app.models.cohorte import Cohorte
from app.repositories.base import BaseRepository


class CohorteRepository(BaseRepository[Cohorte]):
    def __init__(self, session, tenant_id: UUID) -> None:
        super().__init__(session, tenant_id, Cohorte)

    async def get_by_carrera(self, carrera_id: UUID) -> list[Cohorte]:
        query = (
            select(Cohorte)
            .where(
                Cohorte.tenant_id == self._tenant_id,
                Cohorte.carrera_id == carrera_id,
            )
        )
        query = self._apply_soft_delete_filter(query)
        result = await self._session.execute(query)
        return list(result.scalars().all())

    async def get_activas_by_carrera(self, carrera_id: UUID) -> list[Cohorte]:
        query = (
            select(Cohorte)
            .where(
                Cohorte.tenant_id == self._tenant_id,
                Cohorte.carrera_id == carrera_id,
                Cohorte.estado == "Activa",
            )
        )
        query = self._apply_soft_delete_filter(query)
        result = await self._session.execute(query)
        return list(result.scalars().all())
