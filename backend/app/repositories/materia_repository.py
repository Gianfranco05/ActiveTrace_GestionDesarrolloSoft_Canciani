from uuid import UUID

from sqlalchemy import select

from app.models.materia import Materia
from app.repositories.base import BaseRepository


class MateriaRepository(BaseRepository[Materia]):
    def __init__(self, session, tenant_id: UUID) -> None:
        super().__init__(session, tenant_id, Materia)

    async def get_by_codigo(self, codigo: str) -> Materia | None:
        query = (
            select(Materia)
            .where(
                Materia.tenant_id == self._tenant_id,
                Materia.codigo == codigo,
            )
        )
        query = self._apply_soft_delete_filter(query)
        result = await self._session.execute(query)
        return result.scalar_one_or_none()
