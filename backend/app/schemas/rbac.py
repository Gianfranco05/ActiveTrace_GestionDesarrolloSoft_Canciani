import uuid

from pydantic import BaseModel, ConfigDict


class RolCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    nombre: str
    descripcion: str | None = None


class RolResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: uuid.UUID
    nombre: str
    descripcion: str | None = None


class RolUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    nombre: str | None = None
    descripcion: str | None = None


class RolWithPermisosResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: uuid.UUID
    nombre: str
    descripcion: str | None = None
    permisos: list[str] = []


class PermisoCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    codigo: str
    descripcion: str | None = None


class PermisoResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: uuid.UUID
    codigo: str
    descripcion: str | None = None


class SetRolePermisosRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    permiso_ids: list[uuid.UUID]


class RolNameResponse(BaseModel):
    """Lightweight role reference for dropdowns — needs only equipos:asignar."""
    model_config = ConfigDict(from_attributes=True, extra="forbid")

    id: uuid.UUID
    nombre: str
