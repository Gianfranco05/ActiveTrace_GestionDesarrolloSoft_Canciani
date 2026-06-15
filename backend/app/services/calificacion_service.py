from datetime import UTC, datetime
from decimal import Decimal
from uuid import UUID

from fastapi import HTTPException

from app.core.audit_codes import AuditAction
from app.repositories.calificacion_repository import CalificacionRepository
from app.repositories.padron_repository import PadronRepository
from app.repositories.umbral_repository import UmbralRepository
from app.services.audit_service import AuditService
from app.services.grade_file_parser import GradeFileParser


def compute_aprobado(
    tipo: str,
    nota_numerica: Decimal | None,
    nota_textual: str | None,
    umbral_pct: int,
    valores_aprobatorios: list[str] | None,
) -> bool:
    umbral = umbral_pct if umbral_pct else 60
    valores = (
        [v.strip() for v in valores_aprobatorios]
        if valores_aprobatorios
        else ["Satisfactorio", "Supera lo esperado"]
    )

    if tipo == "Numerica":
        if nota_numerica is None:
            return False
        return float(nota_numerica) >= umbral
    else:
        if nota_textual is None:
            return False
        return nota_textual.strip().lower() in [v.lower() for v in valores]


_SUBMITTED_VALUES = {"entregado", "finalizado", "completado", "presentado", "si"}


def _is_submitted(value: str | None) -> bool:
    if value is None:
        return False
    return value.strip().lower() in _SUBMITTED_VALUES


class CalificacionService:
    def __init__(self, session, tenant_id, current_user_id: UUID | None = None):
        self._parser = GradeFileParser()
        self._calificacion_repo = CalificacionRepository(session, tenant_id)
        self._umbral_repo = UmbralRepository(session, tenant_id)
        self._padron_repo = PadronRepository(session, tenant_id)
        self._audit_svc = AuditService(session, None)
        self._session = session
        self._tenant_id = tenant_id
        self._current_user_id = current_user_id

    async def preview(self, file_bytes: bytes, filename: str | None = None, preview_limit: int = 20) -> dict:
        result = self._parser.parse_grade_file(file_bytes, filename)
        return {
            "filename": filename or "",
            "total_rows": result.total_rows,
            "preview_rows": result.rows[:preview_limit] if result.rows else [],
            "actividades_detectadas": [
                {"header": a.header, "nombre": a.nombre, "tipo": a.tipo}
                for a in result.activities
            ],
        }

    async def confirm_import(
        self,
        file_bytes: bytes,
        filename: str | None,
        materia_id: UUID,
        cohorte_id: UUID,
        actividad_mapping: dict[str, str] | None = None,
    ) -> dict:
        from app.repositories.materia_repository import MateriaRepository

        materia_repo = MateriaRepository(self._session, self._tenant_id)
        materia = await materia_repo.get(materia_id)
        if not materia:
            raise HTTPException(status_code=404, detail="Materia no encontrada")

        result = self._parser.parse_grade_file(file_bytes, filename)
        if not result.activities:
            raise HTTPException(status_code=400, detail="No se detectaron actividades en el archivo")
        if not result.rows:
            raise HTTPException(status_code=400, detail="El archivo no contiene filas de datos")

        padron_version = await self._padron_repo.get_active_version(materia_id, cohorte_id)
        if not padron_version:
            raise HTTPException(status_code=400, detail="No hay un padrón activo para esta materia y cohorte")

        entries = await self._padron_repo.get_entries(padron_version.id)
        if not entries:
            raise HTTPException(status_code=400, detail="El padrón activo no contiene estudiantes")

        umbral = await self._umbral_repo.get_by_materia(materia_id)
        umbral_pct = umbral.umbral_pct if umbral else 60
        valores_aprobatorios = (
            umbral.valores_aprobatorios if umbral and umbral.valores_aprobatorios
            else ["Satisfactorio", "Supera lo esperado"]
        )

        activity_headers = self._parser.get_activity_headers(list(result.rows[0].keys()))
        column_types = self._parser.classify_columns(list(result.rows[0].keys()))

        calificaciones = []
        count = 0
        for row in result.rows:
            entrada = self._match_entrada(row, entries)
            if not entrada:
                continue

            for activity_header in activity_headers:
                actividad_name = (
                    actividad_mapping.get(activity_header, activity_header)
                    if actividad_mapping
                    else activity_header
                )

                tipo = column_types.get(activity_header, "Textual")
                raw_value = row.get(activity_header)

                if tipo == "Numerica":
                    nota_numerica = self._parse_numeric(raw_value)
                    nota_textual = None
                else:
                    nota_numerica = None
                    nota_textual = str(raw_value) if raw_value is not None else None

                aprobado = compute_aprobado(
                    tipo=tipo,
                    nota_numerica=nota_numerica,
                    nota_textual=nota_textual,
                    umbral_pct=umbral_pct,
                    valores_aprobatorios=valores_aprobatorios,
                )

                calificaciones.append({
                    "materia_id": materia_id,
                    "cohorte_id": cohorte_id,
                    "entrada_padron_id": entrada.id,
                    "actividad": actividad_name,
                    "tipo": tipo,
                    "nota_numerica": nota_numerica,
                    "nota_textual": nota_textual,
                    "aprobado": aprobado,
                    "origen": "Importado",
                    "cargado_por": self._current_user_id,
                    "importado_at": datetime.now(UTC),
                })
                count += 1

        if not calificaciones:
            raise HTTPException(status_code=400, detail="No se pudieron crear calificaciones (sin estudiantes coincidentes)")

        await self._calificacion_repo.bulk_create(calificaciones)

        from app.repositories.audit_repository import AuditLogRepository
        audit_repo = AuditLogRepository(self._session, self._tenant_id)
        self._audit_svc._repository = audit_repo
        await self._audit_svc.log(
            accion=AuditAction.CALIFICACIONES_IMPORTAR,
            actor_id=self._current_user_id,
            tenant_id=self._tenant_id,
            detalle={
                "materia_id": str(materia_id),
                "cohorte_id": str(cohorte_id),
                "actividades": list(column_types.keys()),
            },
            filas_afectadas=count,
            materia_id=materia_id,
        )

        return {
            "materia_id": materia_id,
            "cohorte_id": cohorte_id,
            "calificaciones_creadas": count,
        }

    async def reporte_finalizacion(
        self,
        file_bytes: bytes,
        filename: str | None,
        materia_id: UUID,
        cohorte_id: UUID,
    ) -> dict:
        result = self._parser.parse_grade_file(file_bytes, filename)
        if not result.rows:
            return {
                "filename": filename or "",
                "total_actividades_revisadas": 0,
                "posibles_sin_corregir": [],
            }

        headers = list(result.rows[0].keys())
        activity_headers = self._parser.get_activity_headers(headers)
        column_types = self._parser.classify_columns(headers)

        textual_activities = [h for h in activity_headers if column_types.get(h) == "Textual"]

        padron_version = await self._padron_repo.get_active_version(materia_id, cohorte_id)
        entries = await self._padron_repo.get_entries(padron_version.id) if padron_version else []

        pending_by_actividad: dict[str, list[dict]] = {}

        for row in result.rows:
            entrada = self._match_entrada(row, entries)
            if not entrada:
                continue

            for act_header in textual_activities:
                completion_value = row.get(act_header)
                if not _is_submitted(str(completion_value) if completion_value is not None else None):
                    continue

                existing = await self._calificacion_repo.get_by_entrada_padron(entrada.id, act_header)
                if existing is not None:
                    continue

                if act_header not in pending_by_actividad:
                    pending_by_actividad[act_header] = []

                alumno = {
                    "nombre": entrada.nombre,
                    "apellidos": entrada.apellidos,
                    "email": entrada.email,
                }

                existing_alumnos = {a["email"] for a in pending_by_actividad[act_header]}
                if alumno["email"] not in existing_alumnos:
                    pending_by_actividad[act_header].append(alumno)

        posibles_sin_corregir = [
            {"actividad": act, "alumnos": alumnos}
            for act, alumnos in pending_by_actividad.items()
        ]

        return {
            "filename": filename or "",
            "total_actividades_revisadas": len(textual_activities),
            "posibles_sin_corregir": posibles_sin_corregir,
        }

    def _match_entrada(self, row: dict, entries) -> object | None:
        nombre = str(row.get("nombre") or row.get("name") or row.get("nombres") or "").strip().lower()
        apellidos = str(row.get("apellidos") or row.get("apellido") or row.get("surname") or "").strip().lower()
        email = str(row.get("email") or row.get("e-mail") or row.get("correo") or row.get("mail") or "").strip().lower()

        if not nombre or not apellidos:
            return None

        for e in entries:
            if (e.nombre.strip().lower() == nombre
                    and e.apellidos.strip().lower() == apellidos):
                return e

        if email:
            for e in entries:
                if e.email and e.email.strip().lower() == email:
                    return e

        return None

    def _parse_numeric(self, value) -> Decimal | None:
        if value is None:
            return None
        try:
            return Decimal(str(value))
        except (ValueError, TypeError):
            return None
