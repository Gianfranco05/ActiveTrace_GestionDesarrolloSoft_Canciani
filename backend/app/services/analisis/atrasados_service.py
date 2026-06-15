from collections import defaultdict
from uuid import UUID

from sqlalchemy import select

from app.models.calificacion import Calificacion
from app.models.padron import EntradaPadron, VersionPadron
from app.schemas.analisis import AlumnoAtrasado


class AtrasadosResult:
    def __init__(self, items, total, sin_datos=False, materia_id=None, cohorte_id=None):
        self.items = items
        self.total = total
        self.sin_datos = sin_datos
        self.materia_id = materia_id
        self.cohorte_id = cohorte_id
        self._dicts = [
            {
                "entrada_padron_id": str(item.entrada_padron_id),
                "nombre": item.nombre,
                "apellidos": item.apellidos,
                "email": item.email,
                "comision": item.comision,
                "motivo": item.motivo,
                "actividades_faltantes": item.actividades_faltantes,
                "actividades_reprobadas": item.actividades_reprobadas,
            }
            for item in items
        ]

    def __iter__(self):
        return iter(self._dicts)

    def __len__(self):
        return len(self._dicts)


class AtrasadosService:
    def __init__(self, session, tenant_id: UUID):
        self._session = session
        self._tenant_id = tenant_id

    async def get_atrasados(
        self,
        materia_id: UUID | None = None,
        cohorte_id: UUID | None = None,
        min_faltantes: int | None = None,
        max_porcentaje: int | None = None,
    ) -> AtrasadosResult:
        query = select(VersionPadron).where(
            VersionPadron.tenant_id == self._tenant_id,
            VersionPadron.activa.is_(True),
            VersionPadron.deleted_at.is_(None),
        )
        if materia_id:
            query = query.where(VersionPadron.materia_id == materia_id)
        if cohorte_id:
            query = query.where(VersionPadron.cohorte_id == cohorte_id)

        versions = (await self._session.execute(query)).scalars().all()
        if not versions:
            return AtrasadosResult(items=[], total=0)

        items = []
        any_sin_datos = False

        for v in versions:
            vp_mat_id = v.materia_id
            vp_coh_id = v.cohorte_id

            entries_query = select(EntradaPadron).where(
                EntradaPadron.version_id == v.id,
                EntradaPadron.tenant_id == self._tenant_id,
                EntradaPadron.deleted_at.is_(None),
            )
            entries = (await self._session.execute(entries_query)).scalars().all()

            califs_query = select(Calificacion).where(
                Calificacion.tenant_id == self._tenant_id,
                Calificacion.materia_id == vp_mat_id,
                Calificacion.cohorte_id == vp_coh_id,
                Calificacion.deleted_at.is_(None),
            )
            califs = (await self._session.execute(califs_query)).scalars().all()

            actividades = sorted({c.actividad for c in califs})
            califs_by_entrada: dict[UUID, list[Calificacion]] = defaultdict(list)
            for c in califs:
                califs_by_entrada[c.entrada_padron_id].append(c)

            sin_datos = len(califs) == 0
            if sin_datos:
                any_sin_datos = True

            for entry in entries:
                entry_califs = califs_by_entrada.get(entry.id, [])

                if sin_datos:
                    items.append(AlumnoAtrasado(
                        entrada_padron_id=entry.id,
                        nombre=entry.nombre,
                        apellidos=entry.apellidos,
                        email=entry.email,
                        comision=entry.comision,
                        motivo="actividades_faltantes",
                        actividades_faltantes=[],
                        actividades_reprobadas=[],
                    ))
                    continue

                entry_actividades = {c.actividad for c in entry_califs}
                faltantes = [a for a in actividades if a not in entry_actividades]
                reprobadas = [c.actividad for c in entry_califs if not c.aprobado]

                if faltantes and reprobadas:
                    motivo = "ambos"
                elif faltantes:
                    motivo = "actividades_faltantes"
                elif reprobadas:
                    motivo = "nota_baja"
                else:
                    continue

                items.append(AlumnoAtrasado(
                    entrada_padron_id=entry.id,
                    nombre=entry.nombre,
                    apellidos=entry.apellidos,
                    email=entry.email,
                    comision=entry.comision,
                    motivo=motivo,
                    actividades_faltantes=faltantes,
                    actividades_reprobadas=reprobadas,
                ))

        # Apply post-query filters
        if min_faltantes is not None:
            items = [i for i in items if len(i.get("actividades_faltantes", [])) >= min_faltantes]
        if max_porcentaje is not None:
            items = [i for i in items if i.get("porcentaje", 100) <= max_porcentaje]

        return AtrasadosResult(
            items=items,
            total=len(items),
            sin_datos=any_sin_datos,
            materia_id=materia_id,
            cohorte_id=cohorte_id,
        )
