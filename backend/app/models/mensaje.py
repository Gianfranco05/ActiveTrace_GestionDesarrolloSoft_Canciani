from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

from .base import BaseModelMixin


class Mensaje(BaseModelMixin, Base):
    __tablename__ = "mensaje"

    sender_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("usuario.id", ondelete="RESTRICT"), nullable=False, index=True,
    )
    recipient_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("usuario.id", ondelete="RESTRICT"), nullable=False, index=True,
    )
    parent_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("mensaje.id", ondelete="CASCADE"), nullable=True, index=True,
    )
    asunto: Mapped[str] = mapped_column(String(250), nullable=False)
    cuerpo: Mapped[str] = mapped_column(Text, nullable=False)
    leido: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default="false",
    )
    leido_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True,
    )

    sender: Mapped[Usuario] = relationship(  # noqa: F821
        "Usuario", foreign_keys=[sender_id], lazy="selectin",
    )
    recipient: Mapped[Usuario] = relationship(  # noqa: F821
        "Usuario", foreign_keys=[recipient_id], lazy="selectin",
    )
    parent: Mapped[Mensaje | None] = relationship(
        "Mensaje", remote_side="Mensaje.id", back_populates="replies", lazy="selectin",
    )
    replies: Mapped[list[Mensaje]] = relationship(
        "Mensaje", back_populates="parent", lazy="selectin",
        order_by="Mensaje.created_at",
    )
