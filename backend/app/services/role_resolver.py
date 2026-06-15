import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.asignacion import Asignacion
from app.models.rol import Rol


class RoleResolver:
    def __init__(self, session: AsyncSession, tenant_id):
        self._session = session
        self._tenant_id = tenant_id

    async def resolve_roles(self, user_id) -> list[str]:
        q = select(Asignacion).where(
            Asignacion.usuario_id == user_id,
            Asignacion.deleted_at.is_(None),
        )
        # Solo filtrar por tenant si tenemos uno real (no nil UUID)
        if self._tenant_id and self._tenant_id != uuid.UUID(int=0):
            q = q.where(Asignacion.tenant_id == self._tenant_id)
        res = await self._session.execute(q)
        asigns = res.scalars().all()
        role_ids = {a.rol_id for a in asigns}
        if not role_ids:
            return []
        q2 = select(Rol).where(Rol.id.in_(list(role_ids)), Rol.deleted_at.is_(None))
        rres = await self._session.execute(q2)
        roles = rres.scalars().all()
        return list({r.nombre for r in roles})
