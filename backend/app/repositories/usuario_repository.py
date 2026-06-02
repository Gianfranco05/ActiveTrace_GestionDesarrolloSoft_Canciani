from typing import Generic, TypeVar

from app.repositories.base import BaseRepository
from app.models.usuario import Usuario

T = TypeVar("T")


class UsuarioRepository(BaseRepository[Usuario]):
    """Repository for Usuario — uses BaseRepository for common CRUD.
    Additional helpers can be added here (get_by_legajo, get_by_cuil, etc.).
    """

    async def get_by_legajo(self, legajo: str):
        return await self.get_by(field_name="legajo", value=legajo)

    def __init__(self, session, tenant_id):
        super().__init__(session, tenant_id, Usuario)
