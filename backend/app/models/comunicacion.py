from __future__ import annotations

import uuid
from datetime import datetime
from enum import StrEnum

from sqlalchemy import JSON, Boolean, DateTime, ForeignKey, Index, String, Text, event
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.core.security import encrypt

from .base import BaseModelMixin


class EstadoComunicacion(StrEnum):
    PENDIENTE = "Pendiente"
    ENVIANDO = "Enviando"
    ENVIADO = "Enviado"
    ERROR = "Error"
    CANCELADO = "Cancelado"


class Comunicacion(BaseModelMixin, Base):
    __tablename__ = "comunicacion"

    lote_id: Mapped[uuid.UUID] = mapped_column(nullable=False, index=True)
    enviado_por: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("usuario.id"), nullable=True,
    )
    materia_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("materia.id"), nullable=True,
    )
    entrada_padron_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("entrada_padron.id"), nullable=True,
    )
    destinatario: Mapped[str] = mapped_column(Text, nullable=False)
    asunto: Mapped[str] = mapped_column(Text, nullable=False)
    cuerpo: Mapped[str] = mapped_column(Text, nullable=False)
    template_id: Mapped[uuid.UUID | None] = mapped_column(nullable=True)
    variables: Mapped[dict] = mapped_column(
        JSON, nullable=False, default=dict, server_default="{}",
    )
    estado: Mapped[str] = mapped_column(
        String(20), nullable=False, default=EstadoComunicacion.PENDIENTE.value,
    )
    requiere_aprobacion: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default="false",
    )
    aprobado_por: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("usuario.id"), nullable=True,
    )
    aprobado_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True,
    )
    enviado_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True,
    )
    error_detalle: Mapped[str | None] = mapped_column(
        Text, nullable=True,
    )


Index("ix_comunicacion_tenant_estado", Comunicacion.tenant_id, Comunicacion.estado)
Index("ix_comunicacion_tenant_created", Comunicacion.tenant_id, Comunicacion.created_at)


def looks_like_ciphertext(value: str) -> bool:
    if len(value) < 30:
        return False
    return "@" not in value


@event.listens_for(Comunicacion, "before_insert")
@event.listens_for(Comunicacion, "before_update")
def encrypt_destinatario(mapper, connection, target):
    if target.destinatario and not looks_like_ciphertext(target.destinatario):
        target.destinatario = encrypt(target.destinatario)
