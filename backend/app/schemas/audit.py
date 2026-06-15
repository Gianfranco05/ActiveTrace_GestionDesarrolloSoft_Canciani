import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class AuditLogResponse(BaseModel):
    model_config = ConfigDict(extra="forbid", from_attributes=True)

    id: uuid.UUID
    tenant_id: uuid.UUID
    fecha_hora: datetime
    actor_id: uuid.UUID
    impersonado_id: uuid.UUID | None = None
    materia_id: uuid.UUID | None = None
    accion: str
    detalle: dict | None = None
    filas_afectadas: int = 0
    ip: str | None = None
    user_agent: str | None = None
    created_at: datetime


class AuditLogListResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    items: list[AuditLogResponse]
    total: int
    offset: int
    limit: int
