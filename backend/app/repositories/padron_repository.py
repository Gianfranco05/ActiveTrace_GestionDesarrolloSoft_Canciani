from app.repositories.base import BaseRepository
from app.models.padron import VersionPadron, EntradaPadron


class PadronRepository(BaseRepository[VersionPadron]):
    def __init__(self, session, tenant_id):
        super().__init__(session, tenant_id, VersionPadron)

    async def create_version(self, payload):
        return await self.create(payload)

    async def create_entry(self, version_id, data):
        entry = EntradaPadron(tenant_id=self._tenant_id, version_id=version_id, **data)
        self._session.add(entry)
        await self._session.commit()
        await self._session.refresh(entry)
        return entry

    async def create_entries(self, version_id, entries):
        return [await self.create_entry(version_id, e) for e in entries]
