import uuid
from datetime import date

from sqlalchemy import Date, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import BaseModelMixin


class FechaAcademica(BaseModelMixin, Base):
    __tablename__ = "fecha_academica"

    materia_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("materia.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    cohorte_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("cohorte.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    tipo: Mapped[str] = mapped_column(String(20), nullable=False)
    numero: Mapped[int] = mapped_column(Integer, nullable=False)
    periodo: Mapped[str] = mapped_column(String(20), nullable=False)
    fecha: Mapped[date] = mapped_column(Date, nullable=False)
    titulo: Mapped[str | None] = mapped_column(String(200), nullable=True)

    materia = relationship("Materia", lazy="selectin")
    cohorte = relationship("Cohorte", lazy="selectin")
