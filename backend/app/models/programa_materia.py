import uuid
from datetime import UTC, datetime

from sqlalchemy import DateTime, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import BaseModelMixin


class ProgramaMateria(BaseModelMixin, Base):
    __tablename__ = "programa_materia"

    materia_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("materia.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    carrera_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("carrera.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    cohorte_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("cohorte.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    titulo: Mapped[str] = mapped_column(String(300), nullable=False)
    referencia_archivo: Mapped[str] = mapped_column(String(500), nullable=False)
    cargado_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        default=lambda: datetime.now(UTC),
    )

    materia = relationship("Materia", lazy="selectin")
    carrera = relationship("Carrera", lazy="selectin")
    cohorte = relationship("Cohorte", lazy="selectin")
