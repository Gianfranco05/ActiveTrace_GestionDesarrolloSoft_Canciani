from app.repositories.base import BaseRepository
from app.models.padron import VersionPadron, EntradaPadron


class PadronRepository(BaseRepository[VersionPadron]):
    def __init__(self, session, tenant_id):
        super().__init__(session, tenant_id, VersionPadron)

    async def create_version(self, payload):
        return await self.create(payload)

    async def create_entries(self, version_id, entries):
        # bulk create EntradaPadron
        items = [dict(version_id=version_id, **e) for e in entries]
        # delegate to base implementation if exists
        return await self._session.execute(self._model_class.__table__.insert(), items)
