
from pydantic import BaseModel, ConfigDict


class UsuarioCreate(BaseModel):
    model_config = ConfigDict(extra='forbid')
    nombre: str
    apellidos: str
    dni: str | None = None
    cuil: str | None = None
    cbu: str | None = None
    alias_cbu: str | None = None


class UsuarioResponse(BaseModel):
    model_config = ConfigDict(extra='forbid', from_attributes=True)
    id: str
    tenant_id: str
    nombre: str
    apellidos: str
    dni: str | None = None
    cuil: str | None = None
    cbu: str | None = None
    alias_cbu: str | None = None
    facturador: bool
    estado: str


class UsuarioSafeResponse(BaseModel):
    model_config = ConfigDict(extra='forbid', from_attributes=True)
    id: str
    tenant_id: str
    nombre: str
    apellidos: str
    facturador: bool
    estado: str
