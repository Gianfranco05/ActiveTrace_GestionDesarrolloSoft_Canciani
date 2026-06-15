from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class CalificacionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True, extra='forbid')

    id: UUID
    materia_id: UUID
    cohorte_id: UUID
    entrada_padron_id: UUID
    actividad: str
    tipo: str
    nota_numerica: Decimal | None = None
    nota_textual: str | None = None
    aprobado: bool
    origen: str
    importado_at: datetime


class UmbralMateriaResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True, extra='forbid')

    materia_id: UUID
    asignacion_id: UUID | None = None
    umbral_pct: int
    valores_aprobatorios: list[str]


class UmbralMateriaUpdate(BaseModel):
    model_config = ConfigDict(extra='forbid')

    umbral_pct: int


class ActividadDetectada(BaseModel):
    model_config = ConfigDict(extra='forbid')

    header: str
    nombre: str
    tipo: str


class ImportPreviewResponse(BaseModel):
    model_config = ConfigDict(extra='forbid')

    filename: str
    total_rows: int
    preview_rows: list[dict]
    actividades_detectadas: list[ActividadDetectada]


class ImportConfirmResponse(BaseModel):
    model_config = ConfigDict(extra='forbid')

    materia_id: UUID
    cohorte_id: UUID
    calificaciones_creadas: int


class ReporteAlumno(BaseModel):
    model_config = ConfigDict(extra='forbid')

    nombre: str
    apellidos: str
    email: str | None = None


class ReporteActividadSinCorregir(BaseModel):
    model_config = ConfigDict(extra='forbid')

    actividad: str
    alumnos: list[ReporteAlumno]


class ReporteFinalizacionResponse(BaseModel):
    model_config = ConfigDict(extra='forbid')

    filename: str
    total_actividades_revisadas: int
    posibles_sin_corregir: list[ReporteActividadSinCorregir]
