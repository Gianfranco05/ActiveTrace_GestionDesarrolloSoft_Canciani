from __future__ import annotations

from typing import Optional

from sqlalchemy import DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from .base import BaseModelMixin


class Asignacion(BaseModelMixin, Base):
    __tablename__ = "asignacion"

    usuario_id: Mapped[Optional[str]] = mapped_column(ForeignKey("usuario.id"), nullable=False)
    rol_id: Mapped[Optional[str]] = mapped_column(ForeignKey("rol.id"), nullable=False)
    vig_desde: Mapped[DateTime] = mapped_column(DateTime, nullable=False)
    vig_hasta: Mapped[Optional[DateTime]] = mapped_column(DateTime, nullable=True)
    responsable_id: Mapped[Optional[str]] = mapped_column(ForeignKey("asignacion.id"), nullable=True)

    usuario = relationship("Usuario")
    rol = relationship("Rol")
