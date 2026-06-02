from uuid import UUID

from sqlalchemy import select

from app.models.carrera import Carrera
from app.repositories.base import BaseRepository


class CarreraRepository(BaseRepository[Carrera]):
    def __init__(self, session, tenant_id: UUID) -> None:
        super().__init__(session, tenant_id, Carrera)

    async def get_by_codigo(self, codigo: str) -> Carrera | None:
        query = (
            select(Carrera)
            .where(
                Carrera.tenant_id == self._tenant_id,
                Carrera.codigo == codigo,
            )
        )
        query = self._apply_soft_delete_filter(query)
        result = await self._session.execute(query)
        return result.scalar_one_or_none()
