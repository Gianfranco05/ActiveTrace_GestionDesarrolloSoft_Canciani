from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base

from .base import BaseModelMixin


class Aviso(BaseModelMixin, Base):
    __tablename__ = "aviso"

    alcance: Mapped[str] = mapped_column(String(20), nullable=False)
    materia_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("materia.id", ondelete="RESTRICT"), nullable=True,
    )
    cohorte_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("cohorte.id", ondelete="RESTRICT"), nullable=True,
    )
    rol_destino: Mapped[str | None] = mapped_column(String(50), nullable=True)
    severidad: Mapped[str] = mapped_column(String(20), nullable=False)
    titulo: Mapped[str] = mapped_column(String(200), nullable=False)
    cuerpo: Mapped[str] = mapped_column(Text, nullable=False)
    inicio_en: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False,
    )
    fin_en: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False,
    )
    orden: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, server_default="0",
    )
    activo: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True, server_default="true",
    )
    requiere_ack: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default="false",
    )
