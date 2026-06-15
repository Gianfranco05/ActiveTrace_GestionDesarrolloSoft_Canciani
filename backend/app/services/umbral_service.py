from uuid import UUID

from fastapi import HTTPException

from app.repositories.materia_repository import MateriaRepository
from app.repositories.umbral_repository import UmbralRepository


class UmbralService:
    def __init__(self, session, tenant_id):
        self._umbral_repo = UmbralRepository(session, tenant_id)
        self._materia_repo = MateriaRepository(session, tenant_id)
        self._session = session

    async def get_umbral(self, materia_id: UUID) -> dict:
        materia = await self._materia_repo.get(materia_id)
        if not materia:
            raise HTTPException(status_code=404, detail="Materia no encontrada")

        umbral = await self._umbral_repo.get_by_materia(materia_id)
        if not umbral:
            return {
                "materia_id": materia_id,
                "asignacion_id": None,
                "umbral_pct": 60,
                "valores_aprobatorios": ["Satisfactorio", "Supera lo esperado"],
            }

        return {
            "materia_id": umbral.materia_id,
            "asignacion_id": umbral.asignacion_id,
            "umbral_pct": umbral.umbral_pct,
            "valores_aprobatorios": umbral.valores_aprobatorios,
        }

    async def set_umbral(self, materia_id: UUID, umbral_pct: int, valores_aprobatorios: list[str] | None = None) -> dict:
        materia = await self._materia_repo.get(materia_id)
        if not materia:
            raise HTTPException(status_code=404, detail="Materia no encontrada")

        if umbral_pct < 1 or umbral_pct > 100:
            raise HTTPException(status_code=422, detail="El umbral debe estar entre 1 y 100")

        data = {"umbral_pct": umbral_pct}
        if valores_aprobatorios is not None:
            data["valores_aprobatorios"] = valores_aprobatorios

        umbral = await self._umbral_repo.upsert(materia_id, data)

        return {
            "materia_id": umbral.materia_id,
            "asignacion_id": umbral.asignacion_id,
            "umbral_pct": umbral.umbral_pct,
            "valores_aprobatorios": umbral.valores_aprobatorios,
        }
