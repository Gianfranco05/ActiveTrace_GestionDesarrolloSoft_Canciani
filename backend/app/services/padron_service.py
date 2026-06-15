from datetime import UTC, datetime
from uuid import UUID

from fastapi import HTTPException

from app.repositories.padron_repository import PadronRepository
from app.services.file_parser import FileParser


class PadronService:
    def __init__(self, session, tenant_id, current_user_id: UUID | None = None):
        self._parser = FileParser()
        self._repo = PadronRepository(session, tenant_id)
        self._tenant_id = tenant_id
        self._current_user_id = current_user_id

    def preview(self, file_bytes: bytes, filename: str | None = None) -> dict:
        res = self._parser.parse_bytes(file_bytes, filename)
        if res.total_rows == 0:
            raise HTTPException(status_code=400, detail="El archivo no contiene filas de datos")
        return {"total_rows": res.total_rows, "rows": res.rows}

    async def confirm_import(self, entries: list[dict], materia_id: UUID | None = None, cohorte_id: UUID | None = None):
        if not entries:
            raise HTTPException(status_code=400, detail="No hay entradas para importar")

        await self._repo.deactivate_previous_active(materia_id, cohorte_id)

        version_data = {
            "materia_id": materia_id,
            "cohorte_id": cohorte_id,
            "cargado_por": self._current_user_id,
            "cargado_at": datetime.now(UTC),
            "activa": True,
        }
        version = await self._repo.create_version(version_data)

        for e in entries:
            await self._repo.create_entry(version.id, e)

        return version

    async def list_versions(self, materia_id: UUID | None = None, cohorte_id: UUID | None = None, offset: int = 0, limit: int = 100) -> tuple[list, int]:
        items = await self._repo.list_versions(materia_id, cohorte_id, offset, limit)
        all_items = await self._repo.list_versions(materia_id, cohorte_id, offset=0, limit=10000)
        return items, len(all_items)

    async def get_version(self, id: UUID):
        version = await self._repo.get_version(id)
        if version is None:
            raise HTTPException(status_code=404, detail="Versión no encontrada")
        return version

    async def get_entries(self, version_id: UUID, offset: int = 0, limit: int = 100) -> tuple[list, int]:
        version = await self._repo.get_version(version_id)
        if version is None:
            raise HTTPException(status_code=404, detail="Versión no encontrada")

        items = await self._repo.get_entries(version_id, offset, limit)
        total = await self._repo.count_entries(version_id)
        return items, total

    async def vaciar_version(self, version_id: UUID):
        version = await self._repo.get_version(version_id)
        if version is None:
            raise HTTPException(status_code=404, detail="Versión no encontrada")
        if version.activa:
            raise HTTPException(status_code=409, detail="No se puede vaciar una versión activa")

        count = await self._repo.vaciar_entries(version_id)
        return count
