from app.repositories.base import BaseRepository
from app.models.asignacion import Asignacion


class AsignacionRepository(BaseRepository[Asignacion]):
    def __init__(self, session, tenant_id):
        super().__init__(session, tenant_id, Asignacion)

    async def get_by_usuario(self, usuario_id):
        return await self.list(filters={"usuario_id": usuario_id})

    async def get_activas_by_usuario(self, usuario_id):
        # simplistic filter; real implementation should check vigencia
        return await self.list(filters={"usuario_id": usuario_id})
