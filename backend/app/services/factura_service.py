"""Factura service — CRUD and state machine for facturador billing."""

import uuid

from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.liquidacion import Factura
from app.repositories.factura_repository import FacturaRepository
from app.schemas.liquidacion import FacturaCreate


class FacturaService:
    def __init__(self, db: AsyncSession, tenant_id: uuid.UUID):
        self._db = db
        self._repo = FacturaRepository(db, tenant_id)

    async def create(self, data: FacturaCreate) -> Factura:
        from sqlalchemy import select

        from app.models.usuario import Usuario

        query = select(Usuario).where(
            Usuario.id == data.usuario_id,
            Usuario.deleted_at.is_(None),
        )
        result = await self._db.execute(query)
        usuario = result.scalar_one_or_none()
        if usuario is None:
            raise HTTPException(status_code=404, detail="Usuario not found")
        if not usuario.facturador:
            raise HTTPException(
                status_code=409,
                detail="El usuario no es facturador",
            )
        return await self._repo.create(data.model_dump())

    async def get_by_id(self, id: uuid.UUID) -> Factura | None:
        return await self._repo.get(id)

    async def list_all(
        self,
        usuario_id: uuid.UUID | None = None,
        periodo: str | None = None,
        estado: str | None = None,
        busqueda: str | None = None,
    ) -> list[Factura]:
        return await self._repo.list_all(
            usuario_id=usuario_id,
            periodo=periodo,
            estado=estado,
            busqueda=busqueda,
        )

    async def soft_delete(self, id: uuid.UUID) -> bool:
        return await self._repo.soft_delete(id)

    async def abonar(self, id: uuid.UUID) -> Factura:
        factura = await self._repo.get(id)
        if factura is None:
            raise HTTPException(status_code=404, detail="Factura not found")
        if factura.estado != "Pendiente":
            raise HTTPException(
                status_code=409,
                detail="Solo se puede abonar una factura Pendiente",
            )
        return await self._repo.update_estado(id, "Abonada", timestamp_field="abonada_at")

    async def reabrir(self, id: uuid.UUID) -> Factura:
        factura = await self._repo.get(id)
        if factura is None:
            raise HTTPException(status_code=404, detail="Factura not found")
        if factura.estado != "Abonada":
            raise HTTPException(
                status_code=409,
                detail="Solo se puede reabrir una factura Abonada",
            )
        return await self._repo.update_estado(id, "Pendiente")
