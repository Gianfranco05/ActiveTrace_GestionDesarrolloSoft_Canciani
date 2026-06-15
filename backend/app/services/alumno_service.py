from sqlalchemy import func, select

from app.core.tenant_aware import get_tenant_scoped
from app.models.asignacion import Asignacion
from app.models.calificacion import Calificacion, UmbralMateria
from app.models.carrera import Carrera
from app.models.cohorte import Cohorte
from app.models.materia import Materia
from app.models.padron import EntradaPadron
from app.models.rol import Rol
from app.schemas.alumno import EstadoAcademicoResponse, MateriaEstadoResponse


class AlumnoService:
    def __init__(self, session, tenant_id, user_id):
        self._session = session
        self._tenant_id = tenant_id
        self._user_id = user_id

    async def get_estado_academico(self) -> EstadoAcademicoResponse:
        asignaciones_query = (
            select(
                Asignacion.materia_id,
                Asignacion.carrera_id,
                Asignacion.cohorte_id,
            )
            .join(Rol, Asignacion.rol_id == Rol.id)
            .where(
                Asignacion.tenant_id == self._tenant_id,
                Asignacion.usuario_id == self._user_id,
                Asignacion.deleted_at.is_(None),
                Asignacion.materia_id.isnot(None),
                Rol.nombre == "ALUMNO",
            )
        )
        result = await self._session.execute(asignaciones_query)
        rows = result.all()

        if not rows:
            return EstadoAcademicoResponse(
                materias=[],
                resumen={
                    "materias_totales": 0,
                    "materias_regulares": 0,
                    "materias_en_riesgo": 0,
                },
            )

        unique_tuplas = set(
            (r.materia_id, r.carrera_id, r.cohorte_id) for r in rows
        )

        materias_estado = []
        regulares = 0
        en_riesgo = 0

        for materia_id, carrera_id, cohorte_id in unique_tuplas:
            actividades_total = await self._contar_actividades(materia_id, cohorte_id)
            actividades_aprobadas = await self._contar_aprobadas(materia_id, cohorte_id)

            umbral = await self._obtener_umbral(materia_id)
            umbral_pct = umbral.umbral_pct if umbral else 60

            if actividades_total == 0:
                porcentaje = 100.0
            else:
                porcentaje = (actividades_aprobadas / actividades_total) * 100

            estado = "Regular" if porcentaje >= umbral_pct else "En riesgo"

            if estado == "Regular":
                regulares += 1
            else:
                en_riesgo += 1

            materia = await get_tenant_scoped(self._session, Materia, materia_id, self._tenant_id)
            carrera = await get_tenant_scoped(self._session, Carrera, carrera_id, self._tenant_id)
            cohorte = await get_tenant_scoped(self._session, Cohorte, cohorte_id, self._tenant_id)

            materias_estado.append(
                MateriaEstadoResponse(
                    materia_id=materia_id,
                    materia_nombre=materia.nombre if materia else "Desconocida",
                    carrera_nombre=carrera.nombre if carrera else "Desconocida",
                    cohorte_nombre=cohorte.nombre if cohorte else "Desconocida",
                    actividades_aprobadas=actividades_aprobadas,
                    actividades_totales=actividades_total,
                    porcentaje_aprobacion=round(porcentaje, 2),
                    estado=estado,
                )
            )

        return EstadoAcademicoResponse(
            materias=materias_estado,
            resumen={
                "materias_totales": len(materias_estado),
                "materias_regulares": regulares,
                "materias_en_riesgo": en_riesgo,
            },
        )

    async def _contar_actividades(self, materia_id, cohorte_id) -> int:
        query = (
            select(func.count(Calificacion.id))
            .join(EntradaPadron, Calificacion.entrada_padron_id == EntradaPadron.id)
            .where(
                Calificacion.tenant_id == self._tenant_id,
                Calificacion.materia_id == materia_id,
                Calificacion.cohorte_id == cohorte_id,
                Calificacion.deleted_at.is_(None),
                EntradaPadron.usuario_id == self._user_id,
            )
        )
        result = await self._session.execute(query)
        return result.scalar() or 0

    async def _contar_aprobadas(self, materia_id, cohorte_id) -> int:
        query = (
            select(func.count(Calificacion.id))
            .join(EntradaPadron, Calificacion.entrada_padron_id == EntradaPadron.id)
            .where(
                Calificacion.tenant_id == self._tenant_id,
                Calificacion.materia_id == materia_id,
                Calificacion.cohorte_id == cohorte_id,
                Calificacion.deleted_at.is_(None),
                Calificacion.aprobado.is_(True),
                EntradaPadron.usuario_id == self._user_id,
            )
        )
        result = await self._session.execute(query)
        return result.scalar() or 0

    async def _obtener_umbral(self, materia_id):
        query = (
            select(UmbralMateria)
            .where(
                UmbralMateria.tenant_id == self._tenant_id,
                UmbralMateria.materia_id == materia_id,
                UmbralMateria.deleted_at.is_(None),
            )
        )
        result = await self._session.execute(query)
        return result.scalars().first()
