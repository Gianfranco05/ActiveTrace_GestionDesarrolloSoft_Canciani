import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class SampleRecipient(BaseModel):
    nombre: str
    apellidos: str
    email: str | None = None
    asunto: str
    cuerpo: str


class PreviewRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    materia_id: uuid.UUID
    cohorte_id: uuid.UUID
    template_body: str
    template_asunto: str = ""


class PreviewResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    sample: list[SampleRecipient]
    total_estimado: int
    preview_token: str
    preview_token_timestamp: str


class EnqueueRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    preview_token: str
    preview_token_timestamp: str
    materia_id: uuid.UUID
    cohorte_id: uuid.UUID
    template_body: str
    template_asunto: str = ""
    template_id: uuid.UUID | None = None


class EnqueueResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    lote_id: str
    creados: int


class ApproveRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    lote_id: uuid.UUID | None = None
    comunicacion_id: uuid.UUID | None = None


class ApproveResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    aprobados: int


class CancelRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    lote_id: uuid.UUID | None = None
    comunicacion_id: uuid.UUID | None = None


class CancelResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    cancelados: int


class ComunicacionResponse(BaseModel):
    model_config = ConfigDict(extra="forbid", from_attributes=True)

    id: uuid.UUID
    tenant_id: uuid.UUID
    lote_id: uuid.UUID
    destinatario: str
    asunto: str
    cuerpo: str
    estado: str
    requiere_aprobacion: bool
    aprobado_por: uuid.UUID | None = None
    aprobado_at: datetime | None = None
    enviado_at: datetime | None = None
    error_detalle: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None


class ComunicacionFilterParams(BaseModel):
    model_config = ConfigDict(extra="forbid")

    estado: str | None = None
    lote_id: uuid.UUID | None = None
    desde: datetime | None = None
    hasta: datetime | None = None


class ComunicacionListResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    items: list[ComunicacionResponse]
    total: int
