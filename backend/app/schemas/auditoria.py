import uuid
from datetime import date, datetime

from pydantic import BaseModel, ConfigDict


class AccionPorDia(BaseModel):
    model_config = ConfigDict(extra="forbid")
    dia: date
    total_acciones: int


class AccionesPorDiaResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")
    items: list[AccionPorDia]
    desde: date
    hasta: date


class EstadoPorDocente(BaseModel):
    model_config = ConfigDict(extra="forbid")
    usuario_id: uuid.UUID
    usuario_nombre: str | None = None
    materia_id: uuid.UUID | None = None
    materia_nombre: str | None = None
    pendiente: int = 0
    enviando: int = 0
    enviado: int = 0
    error: int = 0
    cancelado: int = 0


class EstadoComunicacionesResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")
    items: list[EstadoPorDocente]


class InteraccionRow(BaseModel):
    model_config = ConfigDict(extra="forbid")
    usuario_id: uuid.UUID
    usuario_nombre: str | None = None
    materia_id: uuid.UUID | None = None
    materia_nombre: str | None = None
    accion: str
    cantidad: int


class InteraccionesResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")
    items: list[InteraccionRow]


class UltimaAccionResponse(BaseModel):
    model_config = ConfigDict(extra="forbid", from_attributes=True)
    id: uuid.UUID
    fecha_hora: datetime
    actor_id: uuid.UUID
    actor_nombre: str | None = None
    materia_id: uuid.UUID | None = None
    materia_nombre: str | None = None
    accion: str
    detalle: dict | None = None
    filas_afectadas: int = 0
    ip: str | None = None
    user_agent: str | None = None


class UltimasAccionesResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")
    items: list[UltimaAccionResponse]
    max_registros: int


class AuditoriaLogResponse(BaseModel):
    model_config = ConfigDict(extra="forbid", from_attributes=True)
    id: uuid.UUID
    fecha_hora: datetime
    actor_id: uuid.UUID
    actor_nombre: str | None = None
    materia_id: uuid.UUID | None = None
    materia_nombre: str | None = None
    accion: str
    detalle: dict | None = None
    filas_afectadas: int = 0
    ip: str | None = None
    user_agent: str | None = None


class AuditoriaLogListResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")
    items: list[AuditoriaLogResponse]
    total: int
    offset: int
    limit: int
