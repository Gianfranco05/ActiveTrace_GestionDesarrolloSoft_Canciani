from collections import defaultdict
from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from sqlalchemy import select

from app.models.calificacion import Calificacion
from app.models.padron import EntradaPadron, VersionPadron
from app.schemas.analisis import MonitorCoordinacionRow, MonitorGeneralRow, MonitorSeguimientoRow


class MonitoresService:
    def __init__(self, session, tenant_id: UUID):
        self._session = session
        self._tenant_id = tenant_id

    async def get_general(self) -> list[MonitorGeneralRow]:
        return await self.get_monitor_general()

    async def get_monitor_general(self) -> list[MonitorGeneralRow]:
        versions_query = select(VersionPadron).where(
            VersionPadron.tenant_id == self._tenant_id,
            VersionPadron.activa.is_(True),
            VersionPadron.deleted_at.is_(None),
        )
        versions = (await self._session.execute(versions_query)).scalars().all()

        rows = []
        seen = set()

        for v in versions:
            key = (v.materia_id, v.cohorte_id)
            if key in seen:
                continue
            seen.add(key)

            row = await self._build_general_row(v)
            if row:
                rows.append(row)

        return rows

    async def _build_general_row(self, v: VersionPadron) -> MonitorGeneralRow | None:
        entries_query = select(EntradaPadron).where(
            EntradaPadron.version_id == v.id,
            EntradaPadron.tenant_id == self._tenant_id,
            EntradaPadron.deleted_at.is_(None),
        )
        entries = (await self._session.execute(entries_query)).scalars().all()
        total_alumnos = len(entries)
        if total_alumnos == 0:
            return None

        califs_query = select(Calificacion).where(
            Calificacion.tenant_id == self._tenant_id,
            Calificacion.materia_id == v.materia_id,
            Calificacion.cohorte_id == v.cohorte_id,
            Calificacion.deleted_at.is_(None),
        )
        califs = (await self._session.execute(califs_query)).scalars().all()

        actividades = sorted({c.actividad for c in califs})

        from app.repositories.materia_repository import MateriaRepository
        materia_repo = MateriaRepository(self._session, self._tenant_id)
        materia_obj = await materia_repo.get(v.materia_id)
        materia_nombre = materia_obj.nombre if materia_obj else ""

        from app.repositories.cohorte_repository import CohorteRepository
        cohorte_repo = CohorteRepository(self._session, self._tenant_id)
        cohorte_obj = await cohorte_repo.get(v.cohorte_id)
        cohorte_nombre = cohorte_obj.nombre if cohorte_obj else ""

        califs_by_entry: dict[UUID, list] = defaultdict(list)
        for c in califs:
            califs_by_entry[c.entrada_padron_id].append(c)

        approved = 0
        atrasados = 0

        for entry in entries:
            entry_califs = califs_by_entry.get(entry.id, [])
            entry_actividades = {c.actividad for c in entry_califs}
            has_approved = any(c.aprobado for c in entry_califs)
            faltantes = [a for a in actividades if a not in entry_actividades]
            reprobadas = [c.actividad for c in entry_califs if not c.aprobado]

            if has_approved:
                approved += 1
            if faltantes or reprobadas:
                atrasados += 1

        pct = Decimal("0")
        if total_alumnos > 0:
            pct = Decimal(str(round(approved / total_alumnos * 100, 2)))

        # For sin_datos (no califs), all students are atrasados
        if not califs:
            atrasados = total_alumnos

        return MonitorGeneralRow(
            materia_id=v.materia_id,
            materia_nombre=materia_nombre,
            cohorte_id=v.cohorte_id,
            cohorte_nombre=cohorte_nombre,
            total_alumnos=total_alumnos,
            aprobados=approved,
            atrasados=atrasados,
            pct_aprobacion=pct,
        )

    async def get_seguimiento(
        self,
        materia_id: UUID | None = None,
        docente_id: UUID | None = None,
        regional: str | None = None,
        fecha_desde: date | None = None,
        fecha_hasta: date | None = None,
        minimo_actividades: int | None = None,
    ) -> list[MonitorSeguimientoRow]:
        versions_query = select(VersionPadron).where(
            VersionPadron.tenant_id == self._tenant_id,
            VersionPadron.activa.is_(True),
            VersionPadron.deleted_at.is_(None),
        )
        if materia_id:
            versions_query = versions_query.where(VersionPadron.materia_id == materia_id)

        versions = (await self._session.execute(versions_query)).scalars().all()

        all_rows = []
        for v in versions:
            rows = await self._build_seguimiento_rows(v)
            all_rows.extend(rows)

        # Post-query filters
        if docente_id:
            all_rows = [r for r in all_rows if r.get("docente_id") == str(docente_id)]
        if regional:
            all_rows = [r for r in all_rows if (r.get("regional") or "").lower() == regional.lower()]
        if minimo_actividades is not None:
            all_rows = [r for r in all_rows if r.get("total_actividades", 0) >= minimo_actividades]

        return all_rows

    async def _build_seguimiento_rows(self, v: VersionPadron) -> list[MonitorSeguimientoRow]:
        entries_query = select(EntradaPadron).where(
            EntradaPadron.version_id == v.id,
            EntradaPadron.tenant_id == self._tenant_id,
            EntradaPadron.deleted_at.is_(None),
        )
        entries = (await self._session.execute(entries_query)).scalars().all()

        califs_query = select(Calificacion).where(
            Calificacion.tenant_id == self._tenant_id,
            Calificacion.materia_id == v.materia_id,
            Calificacion.cohorte_id == v.cohorte_id,
            Calificacion.deleted_at.is_(None),
        )
        califs = (await self._session.execute(califs_query)).scalars().all()

        actividades = sorted({c.actividad for c in califs})
        total_actividades = len(actividades)

        califs_by_entry: dict[UUID, list] = defaultdict(list)
        for c in califs:
            califs_by_entry[c.entrada_padron_id].append(c)

        rows = []
        for entry in entries:
            entry_califs = califs_by_entry.get(entry.id, [])
            entry_actividades = {c.actividad for c in entry_califs}

            aprobadas = sum(1 for c in entry_califs if c.aprobado)
            reprobadas = sum(1 for c in entry_califs if not c.aprobado)
            faltantes = total_actividades - len(entry_actividades)

            numeric_grades = [
                c.nota_numerica for c in entry_califs
                if c.tipo == "Numerica" and c.nota_numerica is not None
            ]
            nota_promedio = None
            if numeric_grades:
                avg = sum(float(g) for g in numeric_grades) / len(numeric_grades)
                nota_promedio = Decimal(str(round(avg, 2)))

            if not entry_califs:
                estado = "Sin datos"
            elif (total_actividades > 0
                  and aprobadas / total_actividades >= 0.6
                  and faltantes == 0
                  and reprobadas == 0):
                estado = "Al día"
            else:
                estado = "Atrasado"

            rows.append(MonitorSeguimientoRow(
                entrada_padron_id=entry.id,
                nombre=entry.nombre,
                apellidos=entry.apellidos,
                email=entry.email,
                comision=entry.comision,
                actividades_aprobadas=aprobadas,
                actividades_reprobadas=reprobadas,
                actividades_faltantes=faltantes,
                nota_promedio=nota_promedio,
                estado=estado,
            ))

        return rows

    async def get_coordinacion(
        self,
        desde: datetime | None = None,
        hasta: datetime | None = None,
        materia_id: UUID | None = None,
    ) -> list[MonitorCoordinacionRow]:
        versions_query = select(VersionPadron).where(
            VersionPadron.tenant_id == self._tenant_id,
            VersionPadron.activa.is_(True),
            VersionPadron.deleted_at.is_(None),
        )
        if materia_id:
            versions_query = versions_query.where(VersionPadron.materia_id == materia_id)

        versions = (await self._session.execute(versions_query)).scalars().all()

        rows = []
        seen = set()

        for v in versions:
            key = (v.materia_id, v.cohorte_id)
            if key in seen:
                continue
            seen.add(key)

            row = await self._build_coordinacion_row(v, desde, hasta)
            if row:
                rows.append(row)

        return rows

    async def _build_coordinacion_row(
        self,
        v: VersionPadron,
        desde: datetime | None,
        hasta: datetime | None,
    ) -> MonitorCoordinacionRow | None:
        entries_query = select(EntradaPadron).where(
            EntradaPadron.version_id == v.id,
            EntradaPadron.tenant_id == self._tenant_id,
            EntradaPadron.deleted_at.is_(None),
        )
        entries = (await self._session.execute(entries_query)).scalars().all()
        total_alumnos = len(entries)
        if total_alumnos == 0:
            return None

        califs_query = select(Calificacion).where(
            Calificacion.tenant_id == self._tenant_id,
            Calificacion.materia_id == v.materia_id,
            Calificacion.cohorte_id == v.cohorte_id,
            Calificacion.deleted_at.is_(None),
        )
        if desde:
            califs_query = califs_query.where(Calificacion.importado_at >= desde)
        if hasta:
            califs_query = califs_query.where(Calificacion.importado_at <= hasta)

        califs = (await self._session.execute(califs_query)).scalars().all()

        actividades = sorted({c.actividad for c in califs})

        from app.repositories.materia_repository import MateriaRepository
        materia_repo = MateriaRepository(self._session, self._tenant_id)
        materia_obj = await materia_repo.get(v.materia_id)

        from app.repositories.cohorte_repository import CohorteRepository
        cohorte_repo = CohorteRepository(self._session, self._tenant_id)
        cohorte_obj = await cohorte_repo.get(v.cohorte_id)

        califs_by_entry: dict[UUID, list] = defaultdict(list)
        for c in califs:
            califs_by_entry[c.entrada_padron_id].append(c)

        approved = 0
        atrasados = 0

        for entry in entries:
            entry_califs = califs_by_entry.get(entry.id, [])
            entry_actividades = {c.actividad for c in entry_califs}
            has_approved = any(c.aprobado for c in entry_califs)
            faltantes = [a for a in actividades if a not in entry_actividades]
            reprobadas = [c.actividad for c in entry_califs if not c.aprobado]

            if has_approved:
                approved += 1
            if faltantes or reprobadas:
                atrasados += 1

        if not califs and not desde and not hasta:
            atrasados = total_alumnos

        pct = Decimal("0")
        if total_alumnos > 0:
            pct = Decimal(str(round(approved / total_alumnos * 100, 2)))

        return MonitorCoordinacionRow(
            materia_id=v.materia_id,
            materia_nombre=materia_obj.nombre if materia_obj else "",
            cohorte_id=v.cohorte_id,
            cohorte_nombre=cohorte_obj.nombre if cohorte_obj else "",
            total_alumnos=total_alumnos,
            aprobados=approved,
            atrasados=atrasados,
            pct_aprobacion=pct,
            period_desde=desde,
            period_hasta=hasta,
        )
