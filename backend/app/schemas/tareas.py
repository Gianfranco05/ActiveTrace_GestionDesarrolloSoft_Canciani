import uuid
from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field


class EstadoTarea(StrEnum):
    PENDIENTE = "Pendiente"
    EN_PROGRESO = "En progreso"
    RESUELTA = "Resuelta"
    CANCELADA = "Cancelada"


class TareaCreateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", validate_default=True)

    titulo: str = Field(default="", min_length=1, max_length=200)
    materia_id: uuid.UUID | None = Field(default=None)
    asignado_a: uuid.UUID | None = Field(default=None)
    docente_asignado_id: uuid.UUID | None = Field(default=None)
    descripcion: str = Field(default="", min_length=1, max_length=2000)
    criterio_cierre: str | None = Field(default=None, max_length=500)
    contexto_id: uuid.UUID | None = Field(default=None)


class TareaDelegateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    asignado_a: uuid.UUID


class TareaEstadoUpdateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    estado: EstadoTarea


class TareaUpdateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    descripcion: str | None = Field(default=None, min_length=1, max_length=2000)


class ComentarioCreateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    texto: str = Field(default="", min_length=1, max_length=5000)
    contenido: str | None = Field(default=None, max_length=5000)


class ComentarioTareaResponse(BaseModel):
    model_config = ConfigDict(extra="forbid", from_attributes=True)

    id: uuid.UUID
    tarea_id: uuid.UUID
    autor_id: uuid.UUID
    autor_nombre: str = ""
    texto: str
    creado_at: datetime


class TareaResponse(BaseModel):
    model_config = ConfigDict(extra="forbid", from_attributes=True)

    id: uuid.UUID
    tenant_id: uuid.UUID
    titulo: str = ""
    materia_id: uuid.UUID | None = None
    materia_nombre: str | None = None
    asignado_a: uuid.UUID
    asignado_a_nombre: str | None = None
    docente_asignado_id: uuid.UUID | None = None
    docente_asignado_nombre: str | None = None
    asignado_por: uuid.UUID
    asignado_por_nombre: str | None = None
    asignador_nombre: str | None = None
    estado: str
    descripcion: str
    contexto_id: uuid.UUID | None = None
    comentarios_count: int = 0
    created_at: datetime
    updated_at: datetime


class TareaDetailResponse(TareaResponse):
    comentarios: list[ComentarioTareaResponse] = Field(default_factory=list)


class TareaHistorialResponse(BaseModel):
    model_config = ConfigDict(extra="forbid", from_attributes=True)

    id: uuid.UUID
    tarea_id: uuid.UUID
    estado_anterior: str
    estado_nuevo: str
    usuario_id: uuid.UUID
    usuario_nombre: str = ""
    created_at: datetime


class TareasListResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    items: list[TareaResponse]
    total: int
    offset: int = 0
    limit: int = 20
