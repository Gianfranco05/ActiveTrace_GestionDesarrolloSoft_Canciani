from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class VersionPadronResponse(BaseModel):
    model_config = ConfigDict(extra='forbid', from_attributes=True)
    id: UUID
    materia_id: UUID | None = None
    cohorte_id: UUID | None = None
    cargado_por: UUID | None = None
    cargado_at: datetime | None = None
    activa: bool = True
    created_at: datetime
    updated_at: datetime


class EntradaPadronResponse(BaseModel):
    model_config = ConfigDict(extra='forbid', from_attributes=True)
    id: UUID
    nombre: str
    apellidos: str
    email: str | None = None
    comision: str | None = None
    regional: str | None = None


class ImportPreviewResponse(BaseModel):
    model_config = ConfigDict(extra='forbid')
    total_rows: int
    rows: list[dict]


class ImportConfirmRequest(BaseModel):
    model_config = ConfigDict(extra='forbid')
    entries: list[dict]
    materia_id: UUID | None = None
    cohorte_id: UUID | None = None
    column_mapping: dict | None = None


class VaciarResponse(BaseModel):
    model_config = ConfigDict(extra='forbid')
    version_id: UUID
    deleted_entries: int
