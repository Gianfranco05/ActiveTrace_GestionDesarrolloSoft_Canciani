from __future__ import annotations

from typing import Optional
import uuid

from sqlalchemy import Date, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from .base import BaseModelMixin


class Asignacion(BaseModelMixin, Base):
    __tablename__ = "asignacion"

    usuario_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("usuario.id"), nullable=False)
    rol_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("rol.id"), nullable=False)
    materia_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("materia.id"), nullable=True)
    carrera_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("carrera.id"), nullable=True)
    cohorte_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("cohorte.id"), nullable=True)
    comisiones: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    vig_desde: Mapped[Date] = mapped_column(Date, nullable=False)
    vig_hasta: Mapped[Optional[Date]] = mapped_column(Date, nullable=True)
    responsable_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("asignacion.id"), nullable=True)

    usuario = relationship("Usuario")
    rol = relationship("Rol")
    materia = relationship("Materia")
    carrera = relationship("Carrera")
    cohorte = relationship("Cohorte")

    @property
    def estado_vigencia(self) -> str:
        """Computed state for the assignment's vigencia.

        Returns one of: 'futuro' (starts in the future), 'vigente' (currently active),
        or 'vencida' (ended).
        """
        from datetime import date

        hoy = date.today()
        if self.vig_desde and self.vig_desde > hoy:
            return "Futuro"
        if self.vig_hasta and self.vig_hasta < hoy:
            return "Vencida"
        return "Vigente"
