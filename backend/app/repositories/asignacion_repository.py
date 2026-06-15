from datetime import date

from sqlalchemy import or_, select, update
from sqlalchemy.orm import selectinload

from app.models.asignacion import Asignacion
from app.models.usuario import Usuario
from app.repositories.base import BaseRepository


class AsignacionRepository(BaseRepository[Asignacion]):
    def __init__(self, session, tenant_id):
        super().__init__(session, tenant_id, Asignacion)

    async def get_by_usuario(self, usuario_id):
        query = (
            select(Asignacion)
            .options(selectinload(Asignacion.rol))
            .where(
                Asignacion.tenant_id == self._tenant_id,
                Asignacion.usuario_id == usuario_id,
                Asignacion.deleted_at.is_(None),
            )
        )
        result = await self._session.execute(query)
        return list(result.scalars().all())

    async def get_activas_by_usuario(self, usuario_id):
        today = date.today()
        query = select(Asignacion).where(
            Asignacion.tenant_id == self._tenant_id,
            Asignacion.usuario_id == usuario_id,
            Asignacion.vig_desde <= today,
            Asignacion.deleted_at.is_(None),
            or_(
                Asignacion.vig_hasta.is_(None),
                Asignacion.vig_hasta >= today,
            ),
        )
        result = await self._session.execute(query)
        return list(result.scalars().all())

    async def get_equipo(
        self, materia_id, carrera_id, cohorte_id
    ) -> list[Asignacion]:
        query = (
            select(Asignacion)
            .options(selectinload(Asignacion.rol))
            .where(
                Asignacion.tenant_id == self._tenant_id,
                Asignacion.materia_id == materia_id,
                Asignacion.carrera_id == carrera_id,
                Asignacion.cohorte_id == cohorte_id,
                Asignacion.deleted_at.is_(None),
            )
        )
        result = await self._session.execute(query)
        return list(result.scalars().all())

    async def get_equipos_agrupados(self, tenant_id):
        from sqlalchemy import func

        query = (
            select(
                Asignacion.materia_id,
                Asignacion.carrera_id,
                Asignacion.cohorte_id,
                func.count(Asignacion.id).label("count"),
            )
            .where(
                Asignacion.tenant_id == tenant_id,
                Asignacion.deleted_at.is_(None),
                Asignacion.materia_id.isnot(None),
                Asignacion.carrera_id.isnot(None),
                Asignacion.cohorte_id.isnot(None),
            )
            .group_by(
                Asignacion.materia_id,
                Asignacion.carrera_id,
                Asignacion.cohorte_id,
            )
        )
        result = await self._session.execute(query)
        return result.all()

    async def bulk_create(self, asignaciones: list[Asignacion]) -> list[Asignacion]:
        for a in asignaciones:
            if a.tenant_id is None:
                a.tenant_id = self._tenant_id
            self._session.add(a)
        await self._session.commit()
        for a in asignaciones:
            await self._session.refresh(a, ["rol"])
        return asignaciones

    async def update_vigencia_batch(
        self, equipo_key: tuple, vig_desde: date, vig_hasta: date | None
    ) -> int:
        materia_id, carrera_id, cohorte_id = equipo_key
        stmt = (
            update(Asignacion)
            .where(
                Asignacion.tenant_id == self._tenant_id,
                Asignacion.materia_id == materia_id,
                Asignacion.carrera_id == carrera_id,
                Asignacion.cohorte_id == cohorte_id,
                Asignacion.deleted_at.is_(None),
            )
            .values(vig_desde=vig_desde, vig_hasta=vig_hasta)
        )
        result = await self._session.execute(stmt)
        await self._session.commit()
        return result.rowcount

    async def get_equipo_with_relations(
        self, materia_id, carrera_id, cohorte_id
    ) -> list[dict]:
        query = select(Asignacion).where(
            Asignacion.tenant_id == self._tenant_id,
            Asignacion.materia_id == materia_id,
            Asignacion.carrera_id == carrera_id,
            Asignacion.cohorte_id == cohorte_id,
            Asignacion.deleted_at.is_(None),
        )
        result = await self._session.execute(query)
        asignaciones = result.scalars().all()
        rows = []
        for a in asignaciones:
            await self._session.refresh(a, ["usuario", "rol", "materia", "carrera", "cohorte"])
            rows.append({
                "asignacion": a,
                "usuario": a.usuario,
                "rol": a.rol,
                "materia": a.materia,
                "carrera": a.carrera,
                "cohorte": a.cohorte,
            })
        return rows

    async def search_usuarios(
        self, query_str: str, tenant_id, limit: int = 20
    ) -> list[Usuario]:
        q = (
            select(Usuario)
            .where(
                Usuario.tenant_id == tenant_id,
                Usuario.deleted_at.is_(None),
                or_(
                    Usuario.nombre.ilike(f"%{query_str}%"),
                    Usuario.apellidos.ilike(f"%{query_str}%"),
                    Usuario.legajo.ilike(f"%{query_str}%"),
                ),
            )
            .limit(limit)
        )
        result = await self._session.execute(q)
        return list(result.scalars().all())
