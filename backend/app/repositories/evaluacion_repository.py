import uuid
from datetime import date

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.asignacion import Asignacion
from app.models.cohorte import Cohorte
from app.models.evaluacion import Evaluacion
from app.models.materia import Materia
from app.models.padron import EntradaPadron, VersionPadron
from app.models.reserva_evaluacion import ReservaEvaluacion
from app.models.resultado_evaluacion import ResultadoEvaluacion
from app.models.rol import Rol
from app.models.usuario import Usuario
from app.repositories.base import BaseRepository


class EvaluacionRepository(BaseRepository[Evaluacion]):
    def __init__(self, session: AsyncSession, tenant_id: uuid.UUID):
        super().__init__(session, tenant_id, Evaluacion)

    async def create(self, evaluacion: Evaluacion) -> Evaluacion:
        self._session.add(evaluacion)
        await self._session.flush()
        return evaluacion

    # ── Batch lookups ──

    async def get_materias_by_ids(self, ids: list[uuid.UUID]) -> dict[uuid.UUID, Materia]:
        if not ids:
            return {}
        q = select(Materia).where(
            Materia.id.in_(ids), Materia.tenant_id == self._tenant_id,
            Materia.deleted_at.is_(None),
        )
        r = await self._session.execute(q)
        return {m.id: m for m in r.scalars().all()}

    async def get_cohortes_by_ids(self, ids: list[uuid.UUID]) -> dict[uuid.UUID, Cohorte]:
        if not ids:
            return {}
        q = select(Cohorte).where(
            Cohorte.id.in_(ids), Cohorte.tenant_id == self._tenant_id,
            Cohorte.deleted_at.is_(None),
        )
        r = await self._session.execute(q)
        return {c.id: c for c in r.scalars().all()}

    async def get_usuarios_by_ids(self, ids: list[uuid.UUID]) -> dict[uuid.UUID, Usuario]:
        if not ids:
            return {}
        q = select(Usuario).where(
            Usuario.id.in_(ids), Usuario.tenant_id == self._tenant_id,
            Usuario.deleted_at.is_(None),
        )
        r = await self._session.execute(q)
        return {u.id: u for u in r.scalars().all()}

    async def get_usuario(self, usuario_id: uuid.UUID) -> Usuario | None:
        q = select(Usuario).where(
            Usuario.id == usuario_id, Usuario.tenant_id == self._tenant_id,
            Usuario.deleted_at.is_(None),
        )
        r = await self._session.execute(q)
        return r.scalar_one_or_none()

    async def get_usuario_roles(self, usuario_id: uuid.UUID) -> list[str]:
        q = (
            select(Rol.nombre).join(Asignacion, Asignacion.rol_id == Rol.id)
            .where(
                Asignacion.usuario_id == usuario_id,
                Asignacion.tenant_id == self._tenant_id,
                Asignacion.deleted_at.is_(None),
            )
        )
        r = await self._session.execute(q)
        return list(r.scalars().all())

    async def get_usuarios_with_roles(
        self, ids: list[uuid.UUID],
    ) -> dict[uuid.UUID, tuple[Usuario | None, list[str]]]:
        usuarios = await self.get_usuarios_by_ids(ids)
        result: dict[uuid.UUID, tuple[Usuario | None, list[str]]] = {}
        for uid in ids:
            u = usuarios.get(uid)
            if u is None:
                result[uid] = (None, [])
            else:
                roles = await self.get_usuario_roles(uid)
                result[uid] = (u, roles)
        return result

    # ── Evaluacion listing with batch metrics ──

    async def list_evaluaciones_with_metrics(
        self,
        materia_id: uuid.UUID | None = None,
        cohorte_id: uuid.UUID | None = None,
        tipo: str | None = None,
        activa: bool | None = None,
        incluir_inactivas: bool = False,
        offset: int = 0,
        limit: int = 20,
    ) -> tuple[list[dict], int]:
        base = select(Evaluacion).where(
            Evaluacion.tenant_id == self._tenant_id,
            Evaluacion.deleted_at.is_(None),
        )
        if materia_id:
            base = base.where(Evaluacion.materia_id == materia_id)
        if cohorte_id:
            base = base.where(Evaluacion.cohorte_id == cohorte_id)
        if tipo:
            base = base.where(Evaluacion.tipo == tipo)
        if activa is not None:
            base = base.where(Evaluacion.activa == activa)

        count_q = select(func.count()).select_from(base.subquery())
        total = (await self._session.execute(count_q)).scalar_one()

        items_q = base.order_by(Evaluacion.created_at.desc()).offset(offset).limit(limit)
        result = await self._session.execute(items_q)
        evaluaciones = list(result.scalars().all())

        if not evaluaciones:
            return [], total

        ev_ids = [e.id for e in evaluaciones]
        materias = await self.get_materias_by_ids(list({e.materia_id for e in evaluaciones}))
        cohortes = await self.get_cohortes_by_ids(list({e.cohorte_id for e in evaluaciones}))
        reservas_counts = await self._count_reservas_batch(ev_ids)
        resultados_counts = await self._count_resultados_batch(ev_ids)

        items = []
        for e in evaluaciones:
            materia = materias.get(e.materia_id)
            cohorte = cohortes.get(e.cohorte_id)
            res_count = reservas_counts.get(e.id, 0)
            total_cupos = sum(d["cupo"] for d in (e.cupos_por_dia or []))
            items.append({
                "id": e.id,
                "materia_id": e.materia_id,
                "materia_nombre": materia.nombre if materia else "",
                "cohorte_id": e.cohorte_id,
                "cohorte_nombre": cohorte.nombre if cohorte else "",
                "tipo": e.tipo,
                "instancia": e.instancia,
                "cupos_por_dia": e.cupos_por_dia,
                "activa": e.activa,
                "total_convocados": len(e.alumnos_convocados or []),
                "total_reservas": res_count,
                "total_resultados": resultados_counts.get(e.id, 0),
                "cupos_libres": max(0, total_cupos - res_count),
            })

        return items, total

    async def _count_reservas_batch(self, ev_ids: list[uuid.UUID]) -> dict[uuid.UUID, int]:
        if not ev_ids:
            return {}
        q = (
            select(ReservaEvaluacion.evaluacion_id, func.count().label("cnt"))
            .where(
                ReservaEvaluacion.evaluacion_id.in_(ev_ids),
                ReservaEvaluacion.tenant_id == self._tenant_id,
                ReservaEvaluacion.estado == "Activa",
                ReservaEvaluacion.deleted_at.is_(None),
            ).group_by(ReservaEvaluacion.evaluacion_id)
        )
        r = await self._session.execute(q)
        return {row.evaluacion_id: row.cnt for row in r.all()}

    async def _count_resultados_batch(self, ev_ids: list[uuid.UUID]) -> dict[uuid.UUID, int]:
        if not ev_ids:
            return {}
        q = (
            select(ResultadoEvaluacion.evaluacion_id, func.count().label("cnt"))
            .where(
                ResultadoEvaluacion.evaluacion_id.in_(ev_ids),
                ResultadoEvaluacion.tenant_id == self._tenant_id,
                ResultadoEvaluacion.deleted_at.is_(None),
            ).group_by(ResultadoEvaluacion.evaluacion_id)
        )
        r = await self._session.execute(q)
        return {row.evaluacion_id: row.cnt for row in r.all()}

    # ── Counts for single evaluacion ──

    async def count_reservas_activas_by_evaluacion(self, evaluacion_id: uuid.UUID) -> int:
        q = select(func.count()).select_from(ReservaEvaluacion).where(
            ReservaEvaluacion.evaluacion_id == evaluacion_id,
            ReservaEvaluacion.tenant_id == self._tenant_id,
            ReservaEvaluacion.estado == "Activa",
            ReservaEvaluacion.deleted_at.is_(None),
        )
        return (await self._session.execute(q)).scalar_one()

    async def count_resultados_by_evaluacion(self, evaluacion_id: uuid.UUID) -> int:
        q = select(func.count()).select_from(ResultadoEvaluacion).where(
            ResultadoEvaluacion.evaluacion_id == evaluacion_id,
            ResultadoEvaluacion.tenant_id == self._tenant_id,
            ResultadoEvaluacion.deleted_at.is_(None),
        )
        return (await self._session.execute(q)).scalar_one()

    # ── Reservas ──

    async def count_reservas_activas(self, evaluacion_id: uuid.UUID, fecha: date) -> int:
        q = select(func.count()).select_from(ReservaEvaluacion).where(
            ReservaEvaluacion.evaluacion_id == evaluacion_id,
            ReservaEvaluacion.tenant_id == self._tenant_id,
            ReservaEvaluacion.estado == "Activa",
            ReservaEvaluacion.deleted_at.is_(None),
            func.date(ReservaEvaluacion.fecha_hora) == fecha,
        )
        return (await self._session.execute(q)).scalar_one()

    async def get_reserva_activa(
        self, evaluacion_id: uuid.UUID, alumno_id: uuid.UUID,
    ) -> ReservaEvaluacion | None:
        q = select(ReservaEvaluacion).where(
            ReservaEvaluacion.evaluacion_id == evaluacion_id,
            ReservaEvaluacion.alumno_id == alumno_id,
            ReservaEvaluacion.tenant_id == self._tenant_id,
            ReservaEvaluacion.estado == "Activa",
            ReservaEvaluacion.deleted_at.is_(None),
        )
        r = await self._session.execute(q)
        return r.scalar_one_or_none()

    async def create_reserva(self, data: dict) -> ReservaEvaluacion:
        data["tenant_id"] = self._tenant_id
        reserva = ReservaEvaluacion(**data)
        self._session.add(reserva)
        await self._session.commit()
        await self._session.refresh(reserva)
        return reserva

    async def get_reserva(self, reserva_id: uuid.UUID) -> ReservaEvaluacion | None:
        q = select(ReservaEvaluacion).where(
            ReservaEvaluacion.id == reserva_id,
            ReservaEvaluacion.tenant_id == self._tenant_id,
            ReservaEvaluacion.deleted_at.is_(None),
        )
        r = await self._session.execute(q)
        return r.scalar_one_or_none()

    async def list_reservas(
        self, evaluacion_id: uuid.UUID, estado: str | None = None,
    ) -> list[ReservaEvaluacion]:
        q = select(ReservaEvaluacion).where(
            ReservaEvaluacion.evaluacion_id == evaluacion_id,
            ReservaEvaluacion.tenant_id == self._tenant_id,
            ReservaEvaluacion.deleted_at.is_(None),
        )
        if estado:
            q = q.where(ReservaEvaluacion.estado == estado)
        r = await self._session.execute(q)
        return list(r.scalars().all())

    async def list_reservas_by_alumno(
        self, alumno_id: uuid.UUID, estado: str | None = None,
    ) -> list[ReservaEvaluacion]:
        q = select(ReservaEvaluacion).where(
            ReservaEvaluacion.alumno_id == alumno_id,
            ReservaEvaluacion.tenant_id == self._tenant_id,
            ReservaEvaluacion.deleted_at.is_(None),
        )
        if estado:
            q = q.where(ReservaEvaluacion.estado == estado)
        r = await self._session.execute(q)
        return list(r.scalars().all())

    async def list_reservas_global(
        self,
        materia_id: uuid.UUID | None = None,
        evaluacion_id: uuid.UUID | None = None,
        fecha_desde: date | None = None,
        fecha_hasta: date | None = None,
        offset: int = 0,
        limit: int = 20,
    ) -> tuple[list[ReservaEvaluacion], int]:
        base = select(ReservaEvaluacion).where(
            ReservaEvaluacion.tenant_id == self._tenant_id,
            ReservaEvaluacion.estado == "Activa",
            ReservaEvaluacion.deleted_at.is_(None),
        )
        if evaluacion_id:
            base = base.where(ReservaEvaluacion.evaluacion_id == evaluacion_id)
        if fecha_desde:
            base = base.where(func.date(ReservaEvaluacion.fecha_hora) >= fecha_desde)
        if fecha_hasta:
            base = base.where(func.date(ReservaEvaluacion.fecha_hora) <= fecha_hasta)
        if materia_id:
            base = base.join(Evaluacion, ReservaEvaluacion.evaluacion_id == Evaluacion.id).where(
                Evaluacion.materia_id == materia_id,
            )
        count_q = select(func.count()).select_from(base.subquery())
        total = (await self._session.execute(count_q)).scalar_one()
        items_q = base.offset(offset).limit(limit).order_by(ReservaEvaluacion.fecha_hora.asc())
        r = await self._session.execute(items_q)
        return list(r.scalars().all()), total

    async def get_evaluaciones_by_ids(self, ids: list[uuid.UUID]) -> dict[uuid.UUID, Evaluacion]:
        if not ids:
            return {}
        q = select(Evaluacion).where(
            Evaluacion.id.in_(ids), Evaluacion.tenant_id == self._tenant_id,
            Evaluacion.deleted_at.is_(None),
        )
        r = await self._session.execute(q)
        return {e.id: e for e in r.scalars().all()}

    # ── Resultados ──

    async def create_resultado(self, data: dict) -> ResultadoEvaluacion:
        data["tenant_id"] = self._tenant_id
        resultado = ResultadoEvaluacion(**data)
        self._session.add(resultado)
        await self._session.commit()
        await self._session.refresh(resultado)
        return resultado

    async def get_resultado(
        self, evaluacion_id: uuid.UUID, alumno_id: uuid.UUID,
    ) -> ResultadoEvaluacion | None:
        q = select(ResultadoEvaluacion).where(
            ResultadoEvaluacion.evaluacion_id == evaluacion_id,
            ResultadoEvaluacion.alumno_id == alumno_id,
            ResultadoEvaluacion.tenant_id == self._tenant_id,
            ResultadoEvaluacion.deleted_at.is_(None),
        )
        r = await self._session.execute(q)
        return r.scalar_one_or_none()

    async def list_resultados(self, evaluacion_id: uuid.UUID) -> list[ResultadoEvaluacion]:
        q = select(ResultadoEvaluacion).where(
            ResultadoEvaluacion.evaluacion_id == evaluacion_id,
            ResultadoEvaluacion.tenant_id == self._tenant_id,
            ResultadoEvaluacion.deleted_at.is_(None),
        )
        r = await self._session.execute(q)
        return list(r.scalars().all())

    async def list_resultados_global(
        self,
        materia_id: uuid.UUID | None = None,
        cohorte_id: uuid.UUID | None = None,
        alumno_id: uuid.UUID | None = None,
        offset: int = 0,
        limit: int = 20,
    ) -> tuple[list[ResultadoEvaluacion], int]:
        base = select(ResultadoEvaluacion).where(
            ResultadoEvaluacion.tenant_id == self._tenant_id,
            ResultadoEvaluacion.deleted_at.is_(None),
        ).join(Evaluacion, ResultadoEvaluacion.evaluacion_id == Evaluacion.id)
        if materia_id:
            base = base.where(Evaluacion.materia_id == materia_id)
        if cohorte_id:
            base = base.where(Evaluacion.cohorte_id == cohorte_id)
        if alumno_id:
            base = base.where(ResultadoEvaluacion.alumno_id == alumno_id)
        count_q = select(func.count()).select_from(base.subquery())
        total = (await self._session.execute(count_q)).scalar_one()
        items_q = base.offset(offset).limit(limit)
        r = await self._session.execute(items_q)
        return list(r.scalars().all()), total

    async def upsert_resultado(self, data: dict) -> ResultadoEvaluacion:
        existing = await self.get_resultado(data["evaluacion_id"], data["alumno_id"])
        if existing:
            existing.nota_final = data["nota_final"]
            await self._session.commit()
            await self._session.refresh(existing)
            return existing
        return await self.create_resultado(data)

    # ── Padron ──

    async def get_alumnos_from_padron(
        self, materia_id: uuid.UUID, cohorte_id: uuid.UUID,
    ) -> list[uuid.UUID]:
        q = (
            select(EntradaPadron.usuario_id).join(
                VersionPadron, EntradaPadron.version_id == VersionPadron.id
            ).where(
                VersionPadron.materia_id == materia_id,
                VersionPadron.cohorte_id == cohorte_id,
                VersionPadron.tenant_id == self._tenant_id,
                VersionPadron.activa,
                VersionPadron.deleted_at.is_(None),
                EntradaPadron.deleted_at.is_(None),
            ).distinct()
        )
        r = await self._session.execute(q)
        return [row[0] for row in r.all() if row[0] is not None]

    async def list_with_metrics(self) -> list[dict]:
        items, _ = await self.list_evaluaciones_with_metrics()
        return items

    # ── Metricas ──

    async def count_evaluaciones_activas(self) -> int:
        q = select(func.count()).select_from(Evaluacion).where(
            Evaluacion.tenant_id == self._tenant_id,
            Evaluacion.activa,
            Evaluacion.deleted_at.is_(None),
        )
        return (await self._session.execute(q)).scalar_one()

    async def get_activas_with_convocados(self) -> list[Evaluacion]:
        q = select(Evaluacion).where(
            Evaluacion.tenant_id == self._tenant_id,
            Evaluacion.activa,
            Evaluacion.deleted_at.is_(None),
        )
        r = await self._session.execute(q)
        return list(r.scalars().all())

    async def count_reservas_activas_global(self) -> int:
        q = select(func.count()).select_from(ReservaEvaluacion).where(
            ReservaEvaluacion.tenant_id == self._tenant_id,
            ReservaEvaluacion.estado == "Activa",
            ReservaEvaluacion.deleted_at.is_(None),
        )
        return (await self._session.execute(q)).scalar_one()

    async def count_resultados_global(self) -> int:
        q = select(func.count()).select_from(ResultadoEvaluacion).where(
            ResultadoEvaluacion.tenant_id == self._tenant_id,
            ResultadoEvaluacion.deleted_at.is_(None),
        )
        return (await self._session.execute(q)).scalar_one()
