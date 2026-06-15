from collections import defaultdict
from decimal import Decimal
from uuid import UUID

from sqlalchemy import select

from app.models.calificacion import Calificacion
from app.models.padron import EntradaPadron, VersionPadron
from app.schemas.analisis import NotaFinalRow, RankingRow


class RankingResult:
    def __init__(self, items, total_aprobados, materia_id=None, cohorte_id=None):
        self.items = items
        self.total_aprobados = total_aprobados
        self.materia_id = materia_id
        self.cohorte_id = cohorte_id
        self._dicts = [
            {
                "posicion": item.posicion,
                "entrada_padron_id": str(item.entrada_padron_id),
                "nombre": item.nombre,
                "apellidos": item.apellidos,
                "aprobadas": item.aprobadas,
                "total_actividades": item.total_actividades,
                "porcentaje": item.porcentaje,
            }
            for item in items
        ]

    def __iter__(self):
        return iter(self._dicts)

    def __len__(self):
        return len(self._dicts)


class NotasFinalesResult:
    def __init__(self, items, materia_id=None, cohorte_id=None):
        self.items = items
        self.materia_id = materia_id
        self.cohorte_id = cohorte_id
        self._dicts = [
            {
                "entrada_padron_id": str(item.entrada_padron_id),
                "nombre": item.nombre,
                "apellidos": item.apellidos,
                "nota_promedio": item.nota_promedio,
                "actividades_aprobadas": item.actividades_aprobadas,
                "total_actividades": item.total_actividades,
                "estado": item.estado,
            }
            for item in items
        ]

    def __iter__(self):
        return iter(self._dicts)

    def __len__(self):
        return len(self._dicts)


class RankingService:
    def __init__(self, session, tenant_id: UUID):
        self._session = session
        self._tenant_id = tenant_id

    async def get_ranking(
        self,
        materia_id: UUID | None = None,
        cohorte_id: UUID | None = None,
    ) -> RankingResult:
        califs_query = select(Calificacion).where(
            Calificacion.tenant_id == self._tenant_id,
            Calificacion.deleted_at.is_(None),
        )
        if materia_id:
            califs_query = califs_query.where(Calificacion.materia_id == materia_id)
        if cohorte_id:
            califs_query = califs_query.where(Calificacion.cohorte_id == cohorte_id)

        califs = (await self._session.execute(califs_query)).scalars().all()

        actividades = sorted({c.actividad for c in califs})
        total_actividades = len(actividades)
        if total_actividades == 0:
            return RankingResult(items=[], total_aprobados=0, materia_id=materia_id, cohorte_id=cohorte_id)

        approved_by_entrada: dict[UUID, int] = defaultdict(int)
        for c in califs:
            if c.aprobado:
                approved_by_entrada[c.entrada_padron_id] += 1

        # Get student names
        version_ids_query = select(VersionPadron.id).where(
            VersionPadron.tenant_id == self._tenant_id,
            VersionPadron.deleted_at.is_(None),
        )
        if materia_id:
            version_ids_query = version_ids_query.where(VersionPadron.materia_id == materia_id)
        if cohorte_id:
            version_ids_query = version_ids_query.where(VersionPadron.cohorte_id == cohorte_id)

        version_ids = (await self._session.execute(version_ids_query)).scalars().all()

        entries = []
        if version_ids:
            entries_query = select(EntradaPadron).where(
                EntradaPadron.version_id.in_(version_ids),
                EntradaPadron.tenant_id == self._tenant_id,
                EntradaPadron.deleted_at.is_(None),
            )
            entries = (await self._session.execute(entries_query)).scalars().all()

        entry_map = {e.id: e for e in entries}

        # Build ranking
        rows = []
        for entrada_id, count in approved_by_entrada.items():
            if count == 0:
                continue
            entry = entry_map.get(entrada_id)
            if not entry:
                continue
            pct = Decimal(str(round(count / total_actividades * 100, 2)))
            rows.append({
                "entrada_padron_id": entrada_id,
                "nombre": entry.nombre,
                "apellidos": entry.apellidos,
                "aprobadas": count,
                "total_actividades": total_actividades,
                "porcentaje": pct,
            })

        rows.sort(key=lambda r: (-r["aprobadas"], r["apellidos"], r["nombre"]))

        items = []
        for pos, r in enumerate(rows, start=1):
            items.append(RankingRow(
                posicion=pos,
                entrada_padron_id=r["entrada_padron_id"],
                nombre=r["nombre"],
                apellidos=r["apellidos"],
                aprobadas=r["aprobadas"],
                total_actividades=r["total_actividades"],
                porcentaje=r["porcentaje"],
            ))

        return RankingResult(
            items=items,
            total_aprobados=len(items),
            materia_id=materia_id,
            cohorte_id=cohorte_id,
        )


class NotasFinalesService:
    def __init__(self, session, tenant_id: UUID):
        self._session = session
        self._tenant_id = tenant_id

    async def get_notas(
        self,
        materia_id: UUID | None = None,
        cohorte_id: UUID | None = None,
    ) -> NotasFinalesResult:
        califs_query = select(Calificacion).where(
            Calificacion.tenant_id == self._tenant_id,
            Calificacion.deleted_at.is_(None),
        )
        if materia_id:
            califs_query = califs_query.where(Calificacion.materia_id == materia_id)
        if cohorte_id:
            califs_query = califs_query.where(Calificacion.cohorte_id == cohorte_id)

        califs = (await self._session.execute(califs_query)).scalars().all()

        actividades = sorted({c.actividad for c in califs})
        total_actividades = len(actividades)

        # Get all students from padron
        version_query = select(VersionPadron).where(
            VersionPadron.tenant_id == self._tenant_id,
            VersionPadron.activa.is_(True),
            VersionPadron.deleted_at.is_(None),
        )
        if materia_id:
            version_query = version_query.where(VersionPadron.materia_id == materia_id)
        if cohorte_id:
            version_query = version_query.where(VersionPadron.cohorte_id == cohorte_id)

        versions = (await self._session.execute(version_query)).scalars().all()

        items = []
        for v in versions:
            entries_query = select(EntradaPadron).where(
                EntradaPadron.version_id == v.id,
                EntradaPadron.tenant_id == self._tenant_id,
                EntradaPadron.deleted_at.is_(None),
            )
            entries = (await self._session.execute(entries_query)).scalars().all()

            for entry in entries:
                entry_califs = [c for c in califs if c.entrada_padron_id == entry.id]
                numeric_grades = [
                    c.nota_numerica for c in entry_califs
                    if c.tipo == "Numerica" and c.nota_numerica is not None
                ]

                nota_promedio = None
                if numeric_grades:
                    avg = sum(float(g) for g in numeric_grades) / len(numeric_grades)
                    nota_promedio = Decimal(str(round(avg, 2)))

                aprobadas = sum(1 for c in entry_califs if c.aprobado)

                if not entry_califs:
                    estado = "Sin datos"
                elif (total_actividades > 0
                      and aprobadas / total_actividades >= 0.6):
                    estado = "Regular"
                else:
                    estado = "Libre"

                items.append(NotaFinalRow(
                    entrada_padron_id=entry.id,
                    nombre=entry.nombre,
                    apellidos=entry.apellidos,
                    nota_promedio=nota_promedio,
                    actividades_aprobadas=aprobadas,
                    total_actividades=total_actividades,
                    estado=estado,
                ))

        return NotasFinalesResult(
            items=items,
            materia_id=materia_id,
            cohorte_id=cohorte_id,
        )
