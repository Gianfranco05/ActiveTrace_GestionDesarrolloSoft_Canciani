from __future__ import annotations

import uuid

from sqlalchemy import Date, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

from .base import BaseModelMixin


class Asignacion(BaseModelMixin, Base):
    __tablename__ = "asignacion"

    usuario_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("usuario.id"), nullable=False)
    rol_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("rol.id"), nullable=False)
    materia_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("materia.id"), nullable=True)
    carrera_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("carrera.id"), nullable=True)
    cohorte_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("cohorte.id"), nullable=True)
    comisiones: Mapped[str | None] = mapped_column(Text, nullable=True)
    vig_desde: Mapped[Date] = mapped_column(Date, nullable=False)
    vig_hasta: Mapped[Date | None] = mapped_column(Date, nullable=True)
    responsable_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("asignacion.id"), nullable=True)

    usuario = relationship("Usuario")
    rol = relationship("Rol")
    materia = relationship("Materia")
    carrera = relationship("Carrera")
    cohorte = relationship("Cohorte")

    @property
    def estado_vigencia(self) -> str:
        """Computed state for the assignment's vigencia."""
        from datetime import date

        hoy = date.today()
        desde = self.vig_desde.date() if hasattr(self.vig_desde, 'date') else self.vig_desde
        hasta = self.vig_hasta.date() if self.vig_hasta and hasattr(self.vig_hasta, 'date') else self.vig_hasta

        if desde and desde > hoy:
            return "Futuro"
        if hasta and hasta < hoy:
            return "Vencida"
        return "Vigente"
