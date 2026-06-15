import uuid
from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field


class AlcanceEnum(StrEnum):
    Global = "Global"
    PorMateria = "PorMateria"
    PorCohorte = "PorCohorte"
    PorRol = "PorRol"


class SeveridadEnum(StrEnum):
    Info = "Info"
    Advertencia = "Advertencia"
    Critico = "Critico"


class AvisoCreateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    alcance: AlcanceEnum
    materia_id: uuid.UUID | None = None
    cohorte_id: uuid.UUID | None = None
    rol_destino: str | None = None
    severidad: SeveridadEnum
    titulo: str = Field(max_length=200)
    cuerpo: str
    inicio_en: datetime
    fin_en: datetime
    orden: int = 0
    activo: bool = True
    requiere_ack: bool = False


class AvisoUpdateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    alcance: AlcanceEnum | None = None
    materia_id: uuid.UUID | None = None
    cohorte_id: uuid.UUID | None = None
    rol_destino: str | None = None
    severidad: SeveridadEnum | None = None
    titulo: str | None = Field(default=None, max_length=200)
    cuerpo: str | None = None
    inicio_en: datetime | None = None
    fin_en: datetime | None = None
    orden: int | None = None
    activo: bool | None = None
    requiere_ack: bool | None = None


class AvisoResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True, extra="forbid")

    id: uuid.UUID
    tenant_id: uuid.UUID
    alcance: AlcanceEnum
    materia_id: uuid.UUID | None
    cohorte_id: uuid.UUID | None
    rol_destino: str | None
    severidad: SeveridadEnum
    titulo: str
    cuerpo: str
    inicio_en: datetime
    fin_en: datetime
    orden: int
    activo: bool
    requiere_ack: bool
    created_at: datetime
    updated_at: datetime


class AvisoListItemResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True, extra="forbid")

    id: uuid.UUID
    alcance: AlcanceEnum
    severidad: SeveridadEnum
    titulo: str
    inicio_en: datetime
    fin_en: datetime
    orden: int
    activo: bool
    requiere_ack: bool
    acknowledged: bool
    created_at: datetime


class AvisoDetailResponse(AvisoResponse):
    model_config = ConfigDict(from_attributes=True, extra="forbid")

    acknowledged: bool


class AckResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True, extra="forbid")

    aviso_id: uuid.UUID
    usuario_id: uuid.UUID
    confirmado_at: datetime


class AckStatsResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    aviso_id: uuid.UUID
    total_views: int
    total_acks: int
    pendientes_ack: int


class AcuseResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True, extra="forbid")

    id: uuid.UUID
    aviso_id: uuid.UUID
    usuario_id: uuid.UUID
    usuario_nombre: str = ""
    confirmado: bool = True
    confirmado_at: datetime | None = None


class AvisoListResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    items: list[AvisoListItemResponse]
    total: int
    offset: int
    limit: int
