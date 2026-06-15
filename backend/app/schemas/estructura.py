import uuid
from datetime import date, datetime

from pydantic import BaseModel, ConfigDict


class CarreraCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    codigo: str
    nombre: str
    estado: str | None = None


class CarreraUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    codigo: str | None = None
    nombre: str | None = None
    estado: str | None = None


class CarreraResponse(BaseModel):
    model_config = ConfigDict(extra="forbid", from_attributes=True)

    id: uuid.UUID
    tenant_id: uuid.UUID
    codigo: str
    nombre: str
    estado: str
    created_at: datetime
    updated_at: datetime


class CohorteCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    carrera_id: uuid.UUID
    nombre: str
    anio: int
    vig_desde: date
    vig_hasta: date | None = None
    estado: str | None = None


class CohorteUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    nombre: str | None = None
    anio: int | None = None
    vig_desde: date | None = None
    vig_hasta: date | None = None
    estado: str | None = None
    carrera_id: uuid.UUID | None = None


class CohorteResponse(BaseModel):
    model_config = ConfigDict(extra="forbid", from_attributes=True)

    id: uuid.UUID
    tenant_id: uuid.UUID
    carrera_id: uuid.UUID
    nombre: str
    anio: int
    vig_desde: date
    vig_hasta: date | None
    estado: str
    created_at: datetime
    updated_at: datetime


class MateriaCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    codigo: str
    nombre: str
    estado: str | None = None
    grupo_plus: str | None = None
    carrera_ids: list[uuid.UUID] = []


class MateriaUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    codigo: str | None = None
    nombre: str | None = None
    grupo_plus: str | None = None
    estado: str | None = None
    carrera_ids: list[uuid.UUID] | None = None


class MateriaResponse(BaseModel):
    model_config = ConfigDict(extra="forbid", from_attributes=True)

    id: uuid.UUID
    tenant_id: uuid.UUID
    codigo: str
    nombre: str
    estado: str
    grupo_plus: str | None = None
    created_at: datetime
    updated_at: datetime


class EstructuraListResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    items: list
    total: int
    offset: int = 0
    limit: int = 100
