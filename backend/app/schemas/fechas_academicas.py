import uuid
from datetime import date

from pydantic import BaseModel, ConfigDict, Field


class FechaAcademicaCreateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    materia_id: uuid.UUID
    cohorte_id: uuid.UUID
    tipo: str
    numero: int = Field(ge=1)
    periodo: str
    fecha: date
    titulo: str | None = None


class FechaAcademicaUpdateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    tipo: str | None = None
    numero: int | None = Field(default=None, ge=1)
    periodo: str | None = None
    fecha: date | None = None
    titulo: str | None = None


class FechaAcademicaResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True, extra="forbid")

    id: uuid.UUID
    materia_id: uuid.UUID
    cohorte_id: uuid.UUID
    tipo: str
    numero: int
    periodo: str
    fecha: date
    titulo: str | None


class FechasLmsHtmlResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    html: str
