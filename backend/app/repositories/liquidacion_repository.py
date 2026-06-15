"""Liquidacion repository — bulk ops and queries for liquidaciones."""

import uuid
from datetime import UTC, datetime

from sqlalchemy import func, select, update

from app.models.liquidacion import Liquidacion
from app.models.usuario import Usuario
from app.repositories.base import BaseRepository


class LiquidacionRepository(BaseRepository[Liquidacion]):
    def __init__(self, session, tenant_id):
        super().__init__(session, tenant_id, Liquidacion)

    async def get_by_cohorte_periodo(
        self, cohorte_id: uuid.UUID, periodo: str
    ) -> list[Liquidacion]:
        query = (
            select(Liquidacion)
            .where(
                Liquidacion.tenant_id == self._tenant_id,
                Liquidacion.cohorte_id == cohorte_id,
                Liquidacion.periodo == periodo,
                Liquidacion.deleted_at.is_(None),
            )
        )
        result = await self._session.execute(query)
        return list(result.scalars().all())

    async def get_by_cohorte_periodo_with_users(
        self, cohorte_id: uuid.UUID, periodo: str
    ) -> list[dict]:
        query = (
            select(Liquidacion, Usuario)
            .join(Usuario, Liquidacion.usuario_id == Usuario.id)
            .where(
                Liquidacion.tenant_id == self._tenant_id,
                Liquidacion.cohorte_id == cohorte_id,
                Liquidacion.periodo == periodo,
                Liquidacion.deleted_at.is_(None),
            )
        )
        result = await self._session.execute(query)
        rows = []
        for liq, usr in result.all():
            rows.append({
                "id": liq.id,
                "cohorte_id": liq.cohorte_id,
                "periodo": liq.periodo,
                "usuario_id": liq.usuario_id,
                "rol": liq.rol,
                "comisiones": liq.comisiones,
                "monto_base": liq.monto_base,
                "monto_plus": liq.monto_plus,
                "total": liq.total,
                "es_nexo": liq.es_nexo,
                "excluido_por_factura": liq.excluido_por_factura,
                "estado": liq.estado,
                "docente_nombre": usr.nombre,
                "docente_apellidos": usr.apellidos,
            })
        return rows

    async def upsert_bulk(
        self, records: list[dict]
    ) -> list[Liquidacion]:
        entities = []
        for data in records:
            existing = await self._get_by_unique_key(
                data["cohorte_id"],
                data["periodo"],
                data["usuario_id"],
            )
            if existing:
                for key, value in data.items():
                    setattr(existing, key, value)
                entities.append(existing)
            else:
                data["tenant_id"] = self._tenant_id
                entity = Liquidacion(**data)
                self._session.add(entity)
                entities.append(entity)
        await self._session.commit()
        for e in entities:
            await self._session.refresh(e)
        return entities

    async def close_by_cohorte_periodo(
        self, cohorte_id: uuid.UUID, periodo: str
    ) -> list[Liquidacion]:
        liquidaciones = await self.get_by_cohorte_periodo(cohorte_id, periodo)
        for liq in liquidaciones:
            liq.estado = "Cerrada"
        await self._session.commit()
        for liq in liquidaciones:
            await self._session.refresh(liq)
        return liquidaciones

    async def get_history(self, cohorte_id: uuid.UUID) -> list[Liquidacion]:
        query = (
            select(Liquidacion)
            .where(
                Liquidacion.tenant_id == self._tenant_id,
                Liquidacion.cohorte_id == cohorte_id,
                Liquidacion.estado == "Cerrada",
                Liquidacion.deleted_at.is_(None),
            )
            .order_by(Liquidacion.periodo.desc())
        )
        result = await self._session.execute(query)
        return list(result.scalars().all())

    async def get_by_usuario_periodo(
        self, usuario_id: uuid.UUID, periodo: str
    ) -> Liquidacion | None:
        query = (
            select(Liquidacion)
            .where(
                Liquidacion.tenant_id == self._tenant_id,
                Liquidacion.usuario_id == usuario_id,
                Liquidacion.periodo == periodo,
                Liquidacion.deleted_at.is_(None),
            )
        )
        result = await self._session.execute(query)
        return result.scalar_one_or_none()

    async def count_by_estado(
        self, cohorte_id: uuid.UUID, periodo: str
    ) -> dict[str, int]:
        query = (
            select(Liquidacion.estado, func.count(Liquidacion.id))
            .where(
                Liquidacion.tenant_id == self._tenant_id,
                Liquidacion.cohorte_id == cohorte_id,
                Liquidacion.periodo == periodo,
                Liquidacion.deleted_at.is_(None),
            )
            .group_by(Liquidacion.estado)
        )
        result = await self._session.execute(query)
        return dict(result.all())

    async def delete_by_cohorte_periodo(
        self, cohorte_id: uuid.UUID, periodo: str
    ) -> int:
        now = datetime.now(UTC)
        stmt = (
            update(Liquidacion)
            .where(
                Liquidacion.tenant_id == self._tenant_id,
                Liquidacion.cohorte_id == cohorte_id,
                Liquidacion.periodo == periodo,
                Liquidacion.estado == "Abierta",
                Liquidacion.deleted_at.is_(None),
            )
            .values(deleted_at=now)
        )
        result = await self._session.execute(stmt)
        await self._session.commit()
        return result.rowcount

    async def _get_by_unique_key(
        self, cohorte_id: uuid.UUID, periodo: str, usuario_id: uuid.UUID
    ) -> Liquidacion | None:
        query = select(Liquidacion).where(
            Liquidacion.tenant_id == self._tenant_id,
            Liquidacion.cohorte_id == cohorte_id,
            Liquidacion.periodo == periodo,
            Liquidacion.usuario_id == usuario_id,
            Liquidacion.deleted_at.is_(None),
        )
        result = await self._session.execute(query)
        return result.scalar_one_or_none()
