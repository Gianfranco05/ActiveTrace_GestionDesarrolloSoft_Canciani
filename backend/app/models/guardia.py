import uuid
from datetime import UTC, datetime

from sqlalchemy import DateTime, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import BaseModelMixin


class Guardia(BaseModelMixin, Base):
    __tablename__ = "guardia"

    asignacion_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("asignacion.id", ondelete="RESTRICT"), nullable=False
    )
    materia_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("materia.id", ondelete="RESTRICT"), nullable=False
    )
    carrera_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("carrera.id", ondelete="RESTRICT"), nullable=False
    )
    cohorte_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("cohorte.id", ondelete="RESTRICT"), nullable=False
    )
    dia: Mapped[str] = mapped_column(String(10), nullable=False)
    horario: Mapped[str] = mapped_column(String(50), nullable=False)
    estado: Mapped[str] = mapped_column(String(20), nullable=False, default="Pendiente")
    comentarios: Mapped[str | None] = mapped_column(Text, nullable=True)
    creada_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        default=lambda: datetime.now(UTC),
    )

    materia = relationship("Materia", lazy="selectin")
    carrera = relationship("Carrera", lazy="selectin")
    cohorte = relationship("Cohorte", lazy="selectin")
    asignacion = relationship("Asignacion", lazy="selectin")
