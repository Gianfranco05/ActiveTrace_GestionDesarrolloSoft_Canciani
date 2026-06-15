from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import select, update

from app.models.padron import EntradaPadron, VersionPadron
from app.repositories.base import BaseRepository


class PadronRepository(BaseRepository[VersionPadron]):
    def __init__(self, session, tenant_id):
        super().__init__(session, tenant_id, VersionPadron)

    async def create_version(self, payload):
        return await self.create(payload)

    async def get_active_version(self, materia_id: UUID | None = None, cohorte_id: UUID | None = None) -> VersionPadron | None:
        query = select(VersionPadron).where(
            VersionPadron.tenant_id == self._tenant_id,
            VersionPadron.activa.is_(True),
            VersionPadron.deleted_at.is_(None),
        )
        if materia_id:
            query = query.where(VersionPadron.materia_id == materia_id)
        if cohorte_id:
            query = query.where(VersionPadron.cohorte_id == cohorte_id)
        result = await self._session.execute(query)
        return result.scalar_one_or_none()

    async def deactivate_previous_active(self, materia_id: UUID | None = None, cohorte_id: UUID | None = None) -> int:
        query = (
            update(VersionPadron)
            .where(
                VersionPadron.tenant_id == self._tenant_id,
                VersionPadron.activa.is_(True),
                VersionPadron.deleted_at.is_(None),
            )
            .values(activa=False)
        )
        if materia_id:
            query = query.where(VersionPadron.materia_id == materia_id)
        if cohorte_id:
            query = query.where(VersionPadron.cohorte_id == cohorte_id)
        result = await self._session.execute(query)
        await self._session.commit()
        return result.rowcount

    async def create_entry(self, version_id, data):
        entry = EntradaPadron(tenant_id=self._tenant_id, version_id=version_id, **data)
        self._session.add(entry)
        await self._session.commit()
        await self._session.refresh(entry)
        return entry

    async def create_entries(self, version_id, entries):
        return [await self.create_entry(version_id, e) for e in entries]

    async def get_version(self, id: UUID) -> VersionPadron | None:
        return await self.get(id)

    async def list_versions(self, materia_id: UUID | None = None, cohorte_id: UUID | None = None, offset: int = 0, limit: int = 100) -> list[VersionPadron]:
        query = select(VersionPadron).where(
            VersionPadron.tenant_id == self._tenant_id,
            VersionPadron.deleted_at.is_(None),
        )
        if materia_id:
            query = query.where(VersionPadron.materia_id == materia_id)
        if cohorte_id:
            query = query.where(VersionPadron.cohorte_id == cohorte_id)
        query = query.order_by(VersionPadron.created_at.desc()).offset(offset).limit(limit)
        result = await self._session.execute(query)
        return list(result.scalars().all())

    async def get_entries(self, version_id: UUID, offset: int = 0, limit: int = 100) -> list[EntradaPadron]:
        query = (
            select(EntradaPadron)
            .where(
                EntradaPadron.version_id == version_id,
                EntradaPadron.tenant_id == self._tenant_id,
                EntradaPadron.deleted_at.is_(None),
            )
            .offset(offset)
            .limit(limit)
        )
        result = await self._session.execute(query)
        return list(result.scalars().all())

    async def count_entries(self, version_id: UUID) -> int:
        from sqlalchemy import func
        query = select(func.count()).select_from(EntradaPadron).where(
            EntradaPadron.version_id == version_id,
            EntradaPadron.tenant_id == self._tenant_id,
            EntradaPadron.deleted_at.is_(None),
        )
        result = await self._session.execute(query)
        return result.scalar_one()

    async def vaciar_entries(self, version_id: UUID) -> int:
        now = datetime.now(UTC)
        query = (
            update(EntradaPadron)
            .where(
                EntradaPadron.version_id == version_id,
                EntradaPadron.tenant_id == self._tenant_id,
                EntradaPadron.deleted_at.is_(None),
            )
            .values(deleted_at=now)
        )
        result = await self._session.execute(query)
        await self._session.commit()
        return result.rowcount
