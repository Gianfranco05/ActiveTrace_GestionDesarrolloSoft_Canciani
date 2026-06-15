import uuid
from datetime import date, time

from sqlalchemy import Date, ForeignKey, String, Text, Time
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import BaseModelMixin


class InstanciaEncuentro(BaseModelMixin, Base):
    __tablename__ = "instancia_encuentro"

    slot_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("slot_encuentro.id", ondelete="SET NULL"), nullable=True
    )
    materia_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("materia.id", ondelete="RESTRICT"), nullable=False
    )
    asignacion_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("asignacion.id", ondelete="RESTRICT"), nullable=False
    )
    fecha: Mapped[date] = mapped_column(Date, nullable=False)
    hora: Mapped[time] = mapped_column(Time, nullable=False)
    titulo: Mapped[str] = mapped_column(String(200), nullable=False)
    estado: Mapped[str] = mapped_column(String(20), nullable=False, default="Programado")
    meet_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    video_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    comentario: Mapped[str | None] = mapped_column(Text, nullable=True)

    slot = relationship("SlotEncuentro", back_populates="instancias")
    materia = relationship("Materia", lazy="selectin")
    asignacion = relationship("Asignacion", lazy="selectin")
