import uuid
from datetime import date, time

from sqlalchemy import Date, ForeignKey, Integer, String, Time
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import BaseModelMixin


class SlotEncuentro(BaseModelMixin, Base):
    __tablename__ = "slot_encuentro"

    asignacion_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("asignacion.id", ondelete="RESTRICT"), nullable=False
    )
    materia_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("materia.id", ondelete="RESTRICT"), nullable=False
    )
    titulo: Mapped[str] = mapped_column(String(200), nullable=False)
    hora: Mapped[time] = mapped_column(Time, nullable=False)
    dia_semana: Mapped[str | None] = mapped_column(String(10), nullable=True)
    fecha_inicio: Mapped[date | None] = mapped_column(Date, nullable=True)
    cant_semanas: Mapped[int | None] = mapped_column(Integer, nullable=True)
    fecha_unica: Mapped[date | None] = mapped_column(Date, nullable=True)
    meet_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    vig_desde: Mapped[date | None] = mapped_column(Date, nullable=True)
    vig_hasta: Mapped[date | None] = mapped_column(Date, nullable=True)

    materia = relationship("Materia", lazy="selectin")
    asignacion = relationship("Asignacion", lazy="selectin")
    instancias = relationship(
        "InstanciaEncuentro",
        back_populates="slot",
        lazy="selectin",
        order_by="InstanciaEncuentro.fecha",
    )
