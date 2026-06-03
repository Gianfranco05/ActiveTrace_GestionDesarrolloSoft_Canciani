from typing import TypeVar, Optional

from sqlalchemy import select

from app.repositories.base import BaseRepository
from app.models.usuario import Usuario
import uuid
from app.models.auth_user import AuthUser
from sqlalchemy import insert

T = TypeVar("T")


class UsuarioRepository(BaseRepository[Usuario]):
    """Repository for Usuario — uses BaseRepository for common CRUD.
    Additional helpers can be added here (get_by_legajo, get_by_cuil, etc.).
    """

    async def get_by_legajo(self, legajo: str) -> Optional[Usuario]:
        query = select(Usuario).where(
            Usuario.tenant_id == self._tenant_id,
            Usuario.legajo == legajo,
            Usuario.deleted_at.is_(None),
        )
        result = await self._session.execute(query)
        return result.scalar_one_or_none()

    def __init__(self, session, tenant_id):
        super().__init__(session, tenant_id, Usuario)

    async def create(self, data: dict):
        # Ensure PK present for Usuario (can be provided by UsuarioService when linking to AuthUser)
        if "id" not in data or data["id"] is None:
            # Create or ensure AuthUser exists and reuse its id as Usuario.id
            # If caller provided auth_user_id, trust it; otherwise create a stub AuthUser
            auth_user_id = data.get("id")
            if not auth_user_id:
                # create stub AuthUser
                auth_payload = {
                    "email": f"user+{uuid.uuid4().hex}@example.invalid",
                    "password_hash": "stub",  # tests don't validate password
                    # Ensure tenant_id is set for AuthUser creation
                    "tenant_id": getattr(self, "_tenant_id", None),
                }
                stmt = insert(AuthUser).values(**auth_payload).returning(AuthUser.id)
                res = await self._session.execute(stmt)
                auth_user_id = res.scalar_one()
            data["id"] = auth_user_id
        if "tenant_id" not in data or data["tenant_id"] is None:
            # BaseRepository stores tenant_id in _tenant_id
            data["tenant_id"] = getattr(self, "_tenant_id", None)
        return await super().create(data)
