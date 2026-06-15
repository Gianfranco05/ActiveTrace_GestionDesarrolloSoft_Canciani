import uuid
from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field


class DiaSemana(StrEnum):
    LUNES = "Lunes"
    MARTES = "Martes"
    MIERCOLES = "Miércoles"
    JUEVES = "Jueves"
    VIERNES = "Viernes"
    SABADO = "Sábado"
    DOMINGO = "Domingo"


class EstadoGuardia(StrEnum):
    PENDIENTE = "Pendiente"
    REALIZADA = "Realizada"
    CANCELADA = "Cancelada"


class GuardiaCreateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    asignacion_id: uuid.UUID
    materia_id: uuid.UUID
    carrera_id: uuid.UUID
    cohorte_id: uuid.UUID
    dia: DiaSemana
    horario: str = Field(max_length=50)
    comentarios: str | None = None


class GuardiaUpdateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    estado: EstadoGuardia | None = None
    comentarios: str | None = None


class GuardiaResponse(BaseModel):
    model_config = ConfigDict(extra="forbid", from_attributes=True)

    id: uuid.UUID
    asignacion_id: uuid.UUID
    materia_id: uuid.UUID
    carrera_id: uuid.UUID
    cohorte_id: uuid.UUID
    dia: str
    horario: str
    estado: str
    comentarios: str | None = None
    creada_at: datetime
    created_at: datetime
    updated_at: datetime
    materia_nombre: str | None = None
    carrera_nombre: str | None = None
    cohorte_nombre: str | None = None


class GuardiasListResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    items: list
    total: int
    offset: int = 0
    limit: int = 20
