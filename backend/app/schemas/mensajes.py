import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class MensajeCreateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    recipient_id: uuid.UUID
    asunto: str = Field(min_length=1, max_length=250)
    cuerpo: str = Field(min_length=1, max_length=5000)


class MensajeReplyRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    cuerpo: str = Field(min_length=1, max_length=5000)


class MensajeResponse(BaseModel):
    model_config = ConfigDict(extra="forbid", from_attributes=True)

    id: uuid.UUID
    sender_id: uuid.UUID
    sender_nombre: str
    recipient_id: uuid.UUID
    recipient_nombre: str
    parent_id: uuid.UUID | None = None
    asunto: str
    cuerpo: str
    leido: bool
    leido_at: datetime | None = None
    created_at: datetime


class InboxThreadResponse(BaseModel):
    model_config = ConfigDict(extra="forbid", from_attributes=True)

    thread_id: uuid.UUID
    asunto: str
    sender_nombre: str
    last_message_preview: str
    message_count: int
    unread_count: int
    last_activity: datetime


class ThreadDetailResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    thread: MensajeResponse
    replies: list[MensajeResponse]
