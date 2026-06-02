import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.permiso import Permiso
from app.models.rol import Rol
from app.models.rol_permiso import RolPermiso


class RbacRepository:

    @staticmethod
    async def get_effective_permissions(
        session: AsyncSession,
        role_names: list[str],
    ) -> set[str]:
        if not role_names:
            return set()

        stmt = (
            select(Permiso.codigo)
            .distinct()
            .join(RolPermiso, RolPermiso.permiso_id == Permiso.id)
            .join(Rol, Rol.id == RolPermiso.rol_id)
            .where(Rol.nombre.in_(role_names), Rol.deleted_at.is_(None))
        )
        result = await session.execute(stmt)
        return {row[0] for row in result.fetchall()}

    @staticmethod
    async def get_roles_by_tenant(
        session: AsyncSession,
        tenant_id: uuid.UUID,
    ) -> list[Rol]:
        stmt = (
            select(Rol)
            .where(Rol.tenant_id == tenant_id, Rol.deleted_at.is_(None))
            .order_by(Rol.nombre)
        )
        result = await session.execute(stmt)
        return list(result.scalars().all())

    @staticmethod
    async def get_permisos_catalog(
        session: AsyncSession,
    ) -> list[Permiso]:
        stmt = select(Permiso).order_by(Permiso.codigo)
        result = await session.execute(stmt)
        return list(result.scalars().all())

    @staticmethod
    async def assign_permisos_to_rol(
        session: AsyncSession,
        rol_id: uuid.UUID,
        permiso_ids: list[uuid.UUID],
    ) -> None:
        existing = await session.execute(
            select(RolPermiso).where(RolPermiso.rol_id == rol_id),
        )
        for rp in existing.scalars().all():
            await session.delete(rp)
        await session.flush()

        for pid in permiso_ids:
            session.add(RolPermiso(rol_id=rol_id, permiso_id=pid))
        await session.commit()
