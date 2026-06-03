from datetime import date

from sqlalchemy import select, or_

from app.repositories.base import BaseRepository
from app.models.asignacion import Asignacion


class AsignacionRepository(BaseRepository[Asignacion]):
    def __init__(self, session, tenant_id):
        super().__init__(session, tenant_id, Asignacion)

    async def get_by_usuario(self, usuario_id):
        return await self.list(usuario_id=usuario_id)

    async def get_activas_by_usuario(self, usuario_id):
        today = date.today()
        query = select(Asignacion).where(
            Asignacion.tenant_id == self._tenant_id,
            Asignacion.usuario_id == usuario_id,
            Asignacion.vig_desde <= today,
            Asignacion.deleted_at.is_(None),
            or_(
                Asignacion.vig_hasta.is_(None),
                Asignacion.vig_hasta >= today,
            ),
        )
        result = await self._session.execute(query)
        return list(result.scalars().all())
