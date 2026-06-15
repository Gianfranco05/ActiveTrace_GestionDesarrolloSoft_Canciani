"""Salario repository — SalarioBase, SalarioPlus, GrupoMateria queries."""

import uuid
from datetime import date

from sqlalchemy import select

from app.models.liquidacion import GrupoMateria, SalarioBase, SalarioPlus
from app.repositories.base import BaseRepository


class SalarioBaseRepository(BaseRepository[SalarioBase]):
    def __init__(self, session, tenant_id):
        super().__init__(session, tenant_id, SalarioBase)

    async def get_by_rol(self, rol: str) -> SalarioBase | None:
        query = select(SalarioBase).where(
            SalarioBase.tenant_id == self._tenant_id,
            SalarioBase.rol == rol,
            SalarioBase.deleted_at.is_(None),
        )
        result = await self._session.execute(query)
        return result.scalar_one_or_none()

    async def get_active_for_period(
        self, rol: str, mes_start: date
    ) -> SalarioBase | None:
        from sqlalchemy import or_

        query = select(SalarioBase).where(
            SalarioBase.tenant_id == self._tenant_id,
            SalarioBase.rol == rol,
            SalarioBase.deleted_at.is_(None),
            SalarioBase.vig_desde <= mes_start,
            or_(
                SalarioBase.vig_hasta.is_(None),
                SalarioBase.vig_hasta >= mes_start,
            ),
        )
        result = await self._session.execute(query)
        return result.scalar_one_or_none()

    async def create_or_update(self, data: dict) -> SalarioBase:
        existing = await self.get_by_rol(data["rol"])
        if existing:
            for key, value in data.items():
                if value is not None:
                    setattr(existing, key, value)
            await self._session.commit()
            await self._session.refresh(existing)
            return existing
        return await self.create(data)

    async def list_all(self) -> list[SalarioBase]:
        return await self.list()


class SalarioPlusRepository(BaseRepository[SalarioPlus]):
    def __init__(self, session, tenant_id):
        super().__init__(session, tenant_id, SalarioPlus)

    async def get_by_grupo_rol(
        self, grupo: str, rol: str
    ) -> SalarioPlus | None:
        query = select(SalarioPlus).where(
            SalarioPlus.tenant_id == self._tenant_id,
            SalarioPlus.grupo == grupo,
            SalarioPlus.rol == rol,
            SalarioPlus.deleted_at.is_(None),
        )
        result = await self._session.execute(query)
        return result.scalar_one_or_none()

    async def get_active_for_period(
        self, grupo: str, rol: str, mes_start: date
    ) -> SalarioPlus | None:
        from sqlalchemy import or_

        query = select(SalarioPlus).where(
            SalarioPlus.tenant_id == self._tenant_id,
            SalarioPlus.grupo == grupo,
            SalarioPlus.rol == rol,
            SalarioPlus.deleted_at.is_(None),
            SalarioPlus.vig_desde <= mes_start,
            or_(
                SalarioPlus.vig_hasta.is_(None),
                SalarioPlus.vig_hasta >= mes_start,
            ),
        )
        result = await self._session.execute(query)
        return result.scalar_one_or_none()

    async def create_or_update(self, data: dict) -> SalarioPlus:
        existing = await self.get_by_grupo_rol(
            data["grupo"], data["rol"]
        )
        if existing:
            for key, value in data.items():
                if value is not None:
                    setattr(existing, key, value)
            await self._session.commit()
            await self._session.refresh(existing)
            return existing
        return await self.create(data)

    async def list_all(self) -> list[SalarioPlus]:
        return await self.list()


class GrupoMateriaRepository(BaseRepository[GrupoMateria]):
    def __init__(self, session, tenant_id):
        super().__init__(session, tenant_id, GrupoMateria)

    async def get_by_grupo(self, grupo: str) -> list[GrupoMateria]:
        return await self.list(grupo=grupo)

    async def list_all(self) -> list[GrupoMateria]:
        return await self.list()

    async def delete(self, id: uuid.UUID) -> bool:
        return await self.soft_delete(id)
