from collections import defaultdict
from decimal import Decimal
from uuid import UUID

from sqlalchemy import select

from app.models.calificacion import Calificacion
from app.models.padron import EntradaPadron, VersionPadron
from app.schemas.analisis import ReporteMateria, TPSinCorregirRow


class ReportesService:
    def __init__(self, session, tenant_id: UUID):
        self._session = session
        self._tenant_id = tenant_id

    async def get_reporte(self, materia_id: UUID) -> ReporteMateria:
        version_query = select(VersionPadron).where(
            VersionPadron.tenant_id == self._tenant_id,
            VersionPadron.materia_id == materia_id,
            VersionPadron.activa.is_(True),
            VersionPadron.deleted_at.is_(None),
        )
        version = (await self._session.execute(version_query)).scalar_one_or_none()
        if not version:
            return ReporteMateria(
                materia_id=materia_id,
                materia_nombre="",
                cohorte_id=UUID(int=0),
                cohorte_nombre="",
                total_alumnos=0,
                alumnos_con_nota=0,
                alumnos_aprobados=0,
                alumnos_atrasados=0,
                pct_aprobados=Decimal("0"),
                pct_atrasados=Decimal("0"),
                actividades_count=0,
                sin_datos=True,
            )

        entries_query = select(EntradaPadron).where(
            EntradaPadron.version_id == version.id,
            EntradaPadron.tenant_id == self._tenant_id,
            EntradaPadron.deleted_at.is_(None),
        )
        entries = (await self._session.execute(entries_query)).scalars().all()
        total_alumnos = len(entries)

        califs_query = select(Calificacion).where(
            Calificacion.tenant_id == self._tenant_id,
            Calificacion.materia_id == materia_id,
            Calificacion.cohorte_id == version.cohorte_id,
            Calificacion.deleted_at.is_(None),
        )
        califs = (await self._session.execute(califs_query)).scalars().all()

        # Import materia and cohorte names
        from app.repositories.materia_repository import MateriaRepository
        materia_repo = MateriaRepository(self._session, self._tenant_id)
        materia_obj = await materia_repo.get(materia_id)
        materia_nombre = materia_obj.nombre if materia_obj else ""

        from app.repositories.cohorte_repository import CohorteRepository
        cohorte_repo = CohorteRepository(self._session, self._tenant_id)
        cohorte_obj = await cohorte_repo.get(version.cohorte_id)
        cohorte_nombre = cohorte_obj.nombre if cohorte_obj else ""

        actividades = sorted({c.actividad for c in califs})
        actividades_count = len(actividades)

        sin_datos = len(califs) == 0

        alumnos_con_nota = set()
        alumnos_aprobados = set()
        aprendiz_by_entry: dict[UUID, list] = defaultdict(list)
        for c in califs:
            alumnos_con_nota.add(c.entrada_padron_id)
            if c.aprobado:
                alumnos_aprobados.add(c.entrada_padron_id)
            aprendiz_by_entry[c.entrada_padron_id].append(c)

        alumnos_con_nota_count = len(alumnos_con_nota)
        alumnos_aprobados_count = len(alumnos_aprobados)

        # Compute atrasados
        alumnos_atrasados = set()
        for entry in entries:
            if sin_datos:
                alumnos_atrasados.add(entry.id)
                continue
            entry_califs = aprendiz_by_entry.get(entry.id, [])
            entry_actividades = {c.actividad for c in entry_califs}
            faltantes = [a for a in actividades if a not in entry_actividades]
            reprobadas = [c.actividad for c in entry_califs if not c.aprobado]
            if faltantes or reprobadas:
                alumnos_atrasados.add(entry.id)

        alumnos_atrasados_count = len(alumnos_atrasados)

        pct_aprobados = Decimal("0")
        if total_alumnos > 0:
            pct_aprobados = Decimal(str(round(alumnos_aprobados_count / total_alumnos * 100, 2)))

        pct_atrasados = Decimal("0")
        if total_alumnos > 0:
            pct_atrasados = Decimal(str(round(alumnos_atrasados_count / total_alumnos * 100, 2)))

        ultima_importacion = None
        if califs:
            ultima_importacion = max(c.importado_at for c in califs)

        return ReporteMateria(
            materia_id=materia_id,
            materia_nombre=materia_nombre,
            cohorte_id=version.cohorte_id,
            cohorte_nombre=cohorte_nombre,
            total_alumnos=total_alumnos,
            alumnos_con_nota=alumnos_con_nota_count,
            alumnos_aprobados=alumnos_aprobados_count,
            alumnos_atrasados=alumnos_atrasados_count,
            pct_aprobados=pct_aprobados,
            pct_atrasados=pct_atrasados,
            actividades_count=actividades_count,
            ultima_importacion=ultima_importacion,
            sin_datos=sin_datos,
        )


class ExportService:
    def __init__(self, session, tenant_id: UUID):
        self._session = session
        self._tenant_id = tenant_id

    async def export_tps_sin_corregir(
        self,
        materia_id: UUID,
        cohorte_id: UUID,
    ) -> list[TPSinCorregirRow]:
        califs_query = select(Calificacion).where(
            Calificacion.tenant_id == self._tenant_id,
            Calificacion.materia_id == materia_id,
            Calificacion.cohorte_id == cohorte_id,
            Calificacion.tipo == "Textual",
            Calificacion.nota_numerica.is_(None),
            Calificacion.nota_textual.is_(None),
            Calificacion.deleted_at.is_(None),
        )
        califs = (await self._session.execute(califs_query)).scalars().all()

        entrada_ids = list({c.entrada_padron_id for c in califs})
        entries = []
        if entrada_ids:
            entries_query = select(EntradaPadron).where(
                EntradaPadron.id.in_(entrada_ids),
                EntradaPadron.tenant_id == self._tenant_id,
                EntradaPadron.deleted_at.is_(None),
            )
            entries = (await self._session.execute(entries_query)).scalars().all()

        entry_map = {e.id: e for e in entries}

        rows = []
        for c in califs:
            entry = entry_map.get(c.entrada_padron_id)
            if not entry:
                continue
            rows.append(TPSinCorregirRow(
                actividad=c.actividad,
                entrada_padron_id=entry.id,
                nombre=entry.nombre,
                apellidos=entry.apellidos,
                email=entry.email,
                comision=entry.comision,
            ))

        return rows
