import uuid
from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class CupoPorDia(BaseModel):
    fecha: date
    cupo: int = Field(gt=0)
    model_config = ConfigDict(extra="forbid")


class EvaluacionCreateRequest(BaseModel):
    materia_id: uuid.UUID
    cohorte_id: uuid.UUID
    tipo: Literal["Parcial", "TP", "Coloquio", "Recuperatorio"]
    instancia: str = Field(min_length=1, max_length=200)
    cupos_por_dia: list[CupoPorDia] = Field(min_length=1)
    model_config = ConfigDict(extra="forbid")


class EvaluacionUpdateRequest(BaseModel):
    instancia: str | None = Field(default=None, min_length=1, max_length=200)
    cupos_por_dia: list[CupoPorDia] | None = None
    activa: bool | None = None
    model_config = ConfigDict(extra="forbid")


class ImportarAlumnosRequest(BaseModel):
    modo: Literal["manual", "padron"]
    usuario_ids: list[uuid.UUID] | None = Field(default=None, max_length=500)
    materia_id: uuid.UUID | None = None
    cohorte_id: uuid.UUID | None = None
    model_config = ConfigDict(extra="forbid")


class EvaluacionResponse(BaseModel):
    id: uuid.UUID
    materia_id: uuid.UUID
    materia_nombre: str
    cohorte_id: uuid.UUID
    cohorte_nombre: str
    tipo: str
    instancia: str
    cupos_por_dia: list[dict]
    activa: bool
    total_convocados: int
    total_reservas: int
    total_resultados: int
    cupos_libres: int
    model_config = ConfigDict(extra="forbid", from_attributes=True)


class EvaluacionDetailResponse(BaseModel):
    id: uuid.UUID
    materia_id: uuid.UUID
    cohorte_id: uuid.UUID
    tipo: str
    instancia: str
    cupos_por_dia: list[dict]
    activa: bool
    alumnos_convocados: list[str]
    model_config = ConfigDict(extra="forbid", from_attributes=True)


class ReservaRequest(BaseModel):
    fecha_hora: datetime
    model_config = ConfigDict(extra="forbid")


class ReservaResponse(BaseModel):
    id: uuid.UUID
    evaluacion_id: uuid.UUID
    alumno_id: uuid.UUID
    fecha_hora: datetime
    estado: str
    model_config = ConfigDict(extra="forbid", from_attributes=True)


class ReservaAgendaResponse(BaseModel):
    id: uuid.UUID
    evaluacion_id: uuid.UUID
    materia_nombre: str
    cohorte_nombre: str
    instancia: str
    alumno_nombre: str
    alumno_apellidos: str
    fecha_hora: datetime
    estado: str
    model_config = ConfigDict(extra="forbid")


class ResultadoRequest(BaseModel):
    alumno_id: uuid.UUID
    nota_final: str = Field(min_length=1, max_length=50)
    model_config = ConfigDict(extra="forbid")


class ResultadoResponse(BaseModel):
    id: uuid.UUID
    evaluacion_id: uuid.UUID
    alumno_id: uuid.UUID
    alumno_nombre: str
    alumno_apellidos: str
    nota_final: str
    model_config = ConfigDict(extra="forbid", from_attributes=True)


class ConsolidadoResponse(BaseModel):
    alumno_id: uuid.UUID
    alumno_nombre: str
    alumno_apellidos: str
    materia_nombre: str
    instancia: str
    nota_final: str
    fecha_registro: datetime | None
    model_config = ConfigDict(extra="forbid")


class ConvocatoriaMetricasResponse(BaseModel):
    evaluacion_id: uuid.UUID
    total_convocados: int
    total_reservas: int
    total_resultados: int
    cupos_libres: int
    model_config = ConfigDict(extra="forbid")


class PanelMetricasResponse(BaseModel):
    total_convocatorias_activas: int
    total_convocados: int
    total_reservas_activas: int
    total_resultados: int
    tasa_aprobacion: float | None
    model_config = ConfigDict(extra="forbid")
