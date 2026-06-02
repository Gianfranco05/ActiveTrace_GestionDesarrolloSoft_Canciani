from typing import Generic, TypeVar

from app.repositories.base import BaseRepository
from app.models.usuario import Usuario
import uuid

T = TypeVar("T")


class UsuarioRepository(BaseRepository[Usuario]):
    """Repository for Usuario — uses BaseRepository for common CRUD.
    Additional helpers can be added here (get_by_legajo, get_by_cuil, etc.).
    """

    async def get_by_legajo(self, legajo: str):
        return await self.get_by(field_name="legajo", value=legajo)

    def __init__(self, session, tenant_id):
        super().__init__(session, tenant_id, Usuario)

    async def create(self, data: dict):
        # Ensure PK present for Usuario (can be provided by UsuarioService when linking to AuthUser)
        if "id" not in data or data["id"] is None:
            data["id"] = uuid.uuid4()
        if "tenant_id" not in data or data["tenant_id"] is None:
            # BaseRepository stores tenant_id in _tenant_id
            data["tenant_id"] = getattr(self, "_tenant_id", None)
        return await super().create(data)
