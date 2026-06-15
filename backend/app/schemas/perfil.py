import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class PerfilResponse(BaseModel):
    model_config = ConfigDict(extra="forbid", from_attributes=True)

    id: uuid.UUID
    tenant_id: uuid.UUID
    nombre: str
    apellidos: str
    email: str
    dni: str | None = None
    cuil: str | None = None
    banco: str | None = None
    cbu: str | None = None
    alias_cbu: str | None = None
    regional: str | None = None
    legajo: str | None = None
    legajo_profesional: str | None = None
    facturador: bool = False
    estado: str
    created_at: datetime
    updated_at: datetime


class PerfilUpdateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    nombre: str | None = Field(default=None, max_length=120)
    apellidos: str | None = Field(default=None, max_length=120)
    dni: str | None = None
    banco: str | None = Field(default=None, max_length=80)
    cbu: str | None = None
    alias_cbu: str | None = None
    regional: str | None = Field(default=None, max_length=80)
    legajo_profesional: str | None = Field(default=None, max_length=30)
    facturador: bool | None = None
