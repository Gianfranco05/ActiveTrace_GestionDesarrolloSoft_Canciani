"""Asignacion Pydantic schemas."""

import uuid
from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, field_validator


class AsignacionCreate(BaseModel):
    usuario_id: uuid.UUID
    rol_id: uuid.UUID
    materia_id: uuid.UUID | None = None
    carrera_id: uuid.UUID | None = None
    cohorte_id: uuid.UUID | None = None
    comisiones: str | None = None
    responsable_id: uuid.UUID | None = None
    vig_desde: date
    vig_hasta: date | None = None

    model_config = ConfigDict(extra="forbid")


class AsignacionUpdate(BaseModel):
    usuario_id: uuid.UUID | None = None
    rol_id: uuid.UUID | None = None
    materia_id: uuid.UUID | None = None
    carrera_id: uuid.UUID | None = None
    cohorte_id: uuid.UUID | None = None
    comisiones: str | None = None
    responsable_id: uuid.UUID | None = None
    vig_desde: date | None = None
    vig_hasta: date | None = None

    model_config = ConfigDict(extra="forbid")


class AsignacionResponse(BaseModel):
    id: uuid.UUID
    tenant_id: uuid.UUID
    usuario_id: uuid.UUID
    rol_id: uuid.UUID
    rol_nombre: str = ""
    materia_id: uuid.UUID | None = None
    carrera_id: uuid.UUID | None = None
    cohorte_id: uuid.UUID | None = None
    comisiones: str | None = None
    responsable_id: uuid.UUID | None = None
    vig_desde: date
    vig_hasta: date | None = None
    estado_vigencia: str = ""
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True, extra="forbid")


class EquipoResponse(BaseModel):
    materia_id: uuid.UUID
    carrera_id: uuid.UUID
    cohorte_id: uuid.UUID
    materia_nombre: str
    carrera_nombre: str
    cohorte_nombre: str
    total_asignaciones: int

    model_config = ConfigDict(extra="forbid")


class EquipoDetailResponse(BaseModel):
    materia_id: uuid.UUID
    carrera_id: uuid.UUID
    cohorte_id: uuid.UUID
    asignaciones: list[AsignacionResponse]

    model_config = ConfigDict(extra="forbid")


class AsignacionMasivaRequest(BaseModel):
    materia_id: uuid.UUID
    carrera_id: uuid.UUID
    cohorte_id: uuid.UUID
    rol_id: uuid.UUID
    usuario_ids: list[uuid.UUID]
    vig_desde: date
    vig_hasta: date | None = None
    comisiones: str | None = None

    model_config = ConfigDict(extra="forbid")

    @field_validator("usuario_ids")
    @classmethod
    def validate_usuario_ids(cls, v: list[uuid.UUID]) -> list[uuid.UUID]:
        if len(v) < 1:
            raise ValueError("at least 1 usuario_id required")
        if len(v) > 100:
            raise ValueError("at most 100 usuario_ids allowed")
        return v


class ClonarRequest(BaseModel):
    origen_materia_id: uuid.UUID
    origen_carrera_id: uuid.UUID
    origen_cohorte_id: uuid.UUID
    destino_materia_id: uuid.UUID
    destino_carrera_id: uuid.UUID
    destino_cohorte_id: uuid.UUID
    nueva_vig_desde: date
    nueva_vig_hasta: date | None = None

    model_config = ConfigDict(extra="forbid")


class VigenciaUpdateRequest(BaseModel):
    vig_desde: date
    vig_hasta: date | None = None

    model_config = ConfigDict(extra="forbid")


class UsuarioSearchResponse(BaseModel):
    id: uuid.UUID
    nombre: str
    apellidos: str
    legajo: str | None = None

    model_config = ConfigDict(from_attributes=True, extra="forbid")


class MisMateriasResponse(BaseModel):
    id: uuid.UUID
    nombre: str
    comision: str | None

    model_config = ConfigDict(extra="forbid")
