import uuid
from datetime import UTC, datetime

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import decrypt
from app.models.comunicacion import Comunicacion, EstadoComunicacion, looks_like_ciphertext


class ComunicacionRepository:
    def __init__(self, session: AsyncSession, tenant_id: uuid.UUID):
        self._session = session
        self._tenant_id = tenant_id

    async def create(self, data: dict) -> Comunicacion:
        payload = dict(data)
        payload["tenant_id"] = self._tenant_id
        entity = Comunicacion(**payload)
        self._session.add(entity)
        await self._session.commit()
        await self._session.refresh(entity)
        return self._decrypt(entity)

    async def get_by_id(self, id: uuid.UUID) -> Comunicacion | None:
        query = select(Comunicacion).where(
            Comunicacion.id == id,
            Comunicacion.tenant_id == self._tenant_id,
            Comunicacion.deleted_at.is_(None),
        )
        result = await self._session.execute(query)
        entity = result.scalar_one_or_none()
        return self._decrypt(entity) if entity else None

    async def list_by_estado(self, estado: str) -> list[Comunicacion]:
        query = select(Comunicacion).where(
            Comunicacion.tenant_id == self._tenant_id,
            Comunicacion.estado == estado,
            Comunicacion.deleted_at.is_(None),
        )
        result = await self._session.execute(query)
        return self._decrypt_list(result.scalars().all())

    async def list_by_lote(self, lote_id: uuid.UUID) -> list[Comunicacion]:
        query = select(Comunicacion).where(
            Comunicacion.tenant_id == self._tenant_id,
            Comunicacion.lote_id == lote_id,
            Comunicacion.deleted_at.is_(None),
        )
        result = await self._session.execute(query)
        return self._decrypt_list(result.scalars().all())

    async def list_by_date_range(
        self, desde: datetime, hasta: datetime,
    ) -> list[Comunicacion]:
        query = select(Comunicacion).where(
            Comunicacion.tenant_id == self._tenant_id,
            Comunicacion.created_at >= desde,
            Comunicacion.created_at <= hasta,
            Comunicacion.deleted_at.is_(None),
        )
        result = await self._session.execute(query)
        return self._decrypt_list(result.scalars().all())

    async def list_filtered(
        self,
        estado: str | None = None,
        lote_id: uuid.UUID | None = None,
        desde: datetime | None = None,
        hasta: datetime | None = None,
    ) -> list[Comunicacion]:
        query = select(Comunicacion).where(
            Comunicacion.tenant_id == self._tenant_id,
            Comunicacion.deleted_at.is_(None),
        )
        if estado:
            query = query.where(Comunicacion.estado == estado)
        if lote_id:
            query = query.where(Comunicacion.lote_id == lote_id)
        if desde:
            query = query.where(Comunicacion.created_at >= desde)
        if hasta:
            query = query.where(Comunicacion.created_at <= hasta)
        query = query.order_by(Comunicacion.created_at.desc())
        result = await self._session.execute(query)
        return self._decrypt_list(result.scalars().all())

    async def update_estado(
        self, id: uuid.UUID, estado: str, extra: dict | None = None,
    ) -> Comunicacion | None:
        entity = await self.get_by_id(id)
        if entity is None:
            return None
        entity.estado = estado
        if extra:
            for k, v in extra.items():
                setattr(entity, k, v)
        await self._session.commit()
        await self._session.refresh(entity)
        return self._decrypt(entity)

    async def soft_delete(self, id: uuid.UUID) -> bool:
        entity = await self.get_by_id(id)
        if entity is None:
            return False
        entity.deleted_at = datetime.now(UTC)
        await self._session.commit()
        return True

    async def bulk_set_aprobado(
        self, lote_id: uuid.UUID, aprobado_por: uuid.UUID,
    ) -> int:
        result = await self._session.execute(
            update(Comunicacion)
            .where(
                Comunicacion.tenant_id == self._tenant_id,
                Comunicacion.lote_id == lote_id,
                Comunicacion.estado == EstadoComunicacion.PENDIENTE.value,
                Comunicacion.aprobado_por.is_(None),
                Comunicacion.deleted_at.is_(None),
            )
            .values(
                aprobado_por=aprobado_por,
                aprobado_at=datetime.now(UTC),
            ),
        )
        await self._session.commit()
        return result.rowcount

    async def bulk_cancel_by_lote(self, lote_id: uuid.UUID) -> int:
        result = await self._session.execute(
            update(Comunicacion)
            .where(
                Comunicacion.tenant_id == self._tenant_id,
                Comunicacion.lote_id == lote_id,
                Comunicacion.estado == EstadoComunicacion.PENDIENTE.value,
                Comunicacion.deleted_at.is_(None),
            )
            .values(estado=EstadoComunicacion.CANCELADO.value),
        )
        await self._session.commit()
        return result.rowcount

    def _decrypt(self, entity: Comunicacion) -> Comunicacion:
        if entity.destinatario and looks_like_ciphertext(entity.destinatario):
            entity.destinatario = decrypt(entity.destinatario)
        return entity

    def _decrypt_list(self, entities: list[Comunicacion]) -> list[Comunicacion]:
        for e in entities:
            self._decrypt(e)
        return entities

    async def count_by_lote(self, lote_id: uuid.UUID) -> int:
        query = select(Comunicacion).where(
            Comunicacion.tenant_id == self._tenant_id,
            Comunicacion.lote_id == lote_id,
            Comunicacion.deleted_at.is_(None),
        )
        result = await self._session.execute(query)
        return len(result.scalars().all())
