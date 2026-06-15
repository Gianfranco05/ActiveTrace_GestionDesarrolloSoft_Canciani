"""Usuario Pydantic schemas — safe and full response variants."""

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class UsuarioCreate(BaseModel):
    email: str
    password: str | None = None
    nombre: str
    apellidos: str = ""
    dni: str = ""
    cuil: str = ""
    roles: list[str] = []
    cbu: str | None = None
    alias_cbu: str | None = None
    banco: str | None = None
    regional: str | None = None
    legajo: str | None = None
    legajo_profesional: str | None = None
    facturador: bool = False
    estado: str = "Activo"

    model_config = ConfigDict(extra="forbid")


class UsuarioUpdate(BaseModel):
    nombre: str | None = None
    email: str | None = None
    password: str | None = None
    apellidos: str | None = None
    dni: str | None = None
    cuil: str | None = None
    roles: list[str] | None = None
    cbu: str | None = None
    alias_cbu: str | None = None
    banco: str | None = None
    regional: str | None = None
    legajo: str | None = None
    legajo_profesional: str | None = None
    facturador: bool | None = None
    estado: str | None = None

    model_config = ConfigDict(extra="forbid")


class UsuarioResponse(BaseModel):
    id: uuid.UUID
    tenant_id: uuid.UUID
    nombre: str
    apellidos: str
    dni: str | None = None
    cuil: str | None = None
    cbu: str | None = None
    alias_cbu: str | None = None
    banco: str | None = None
    regional: str | None = None
    legajo: str | None = None
    legajo_profesional: str | None = None
    facturador: bool = False
    estado: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True, extra="forbid")


class EstadoToggleRequest(BaseModel):
    estado: str

    model_config = ConfigDict(extra="forbid")


class AdminResetPasswordRequest(BaseModel):
    new_password: str = Field(..., min_length=8)

    model_config = ConfigDict(extra="forbid")


class UsuarioSafeResponse(BaseModel):
    id: uuid.UUID
    tenant_id: uuid.UUID
    nombre: str
    apellidos: str
    email: str | None = None
    roles: list[str] = []
    activo: bool = True
    banco: str | None = None
    regional: str | None = None
    legajo: str | None = None
    legajo_profesional: str | None = None
    facturador: bool = False
    estado: str

    model_config = ConfigDict(from_attributes=True, extra="forbid")
