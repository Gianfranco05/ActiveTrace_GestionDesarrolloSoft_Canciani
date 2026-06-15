"""Factura repository — CRUD queries for facturas."""

import uuid
from datetime import UTC, datetime

from sqlalchemy import select

from app.models.liquidacion import Factura
from app.repositories.base import BaseRepository


class FacturaRepository(BaseRepository[Factura]):
    def __init__(self, session, tenant_id):
        super().__init__(session, tenant_id, Factura)

    async def list_all(
        self,
        usuario_id: uuid.UUID | None = None,
        periodo: str | None = None,
        estado: str | None = None,
        busqueda: str | None = None,
    ) -> list[Factura]:
        query = select(Factura).where(
            Factura.tenant_id == self._tenant_id,
            Factura.deleted_at.is_(None),
        )
        if usuario_id:
            query = query.where(Factura.usuario_id == usuario_id)
        if periodo:
            query = query.where(Factura.periodo == periodo)
        if estado:
            query = query.where(Factura.estado == estado)
        if busqueda:
            query = query.where(Factura.descripcion.ilike(f"%{busqueda}%"))
        result = await self._session.execute(query)
        return list(result.scalars().all())

    async def update_estado(
        self, id: uuid.UUID, estado: str, timestamp_field: str | None = None
    ) -> Factura | None:
        entity = await self.get(id)
        if entity is None:
            return None
        entity.estado = estado
        if timestamp_field == "abonada_at":
            entity.abonada_at = datetime.now(UTC)
        elif timestamp_field is None and estado == "Pendiente":
            entity.abonada_at = None
        await self._session.commit()
        await self._session.refresh(entity)
        return entity
