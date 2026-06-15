import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.base import BaseModelMixin


class ReservaEvaluacion(BaseModelMixin, Base):
    __tablename__ = "reserva_evaluacion"

    evaluacion_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("evaluacion.id", ondelete="RESTRICT"), nullable=False
    )
    alumno_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("usuario.id", ondelete="RESTRICT"), nullable=False
    )
    fecha_hora: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    estado: Mapped[str] = mapped_column(String(20), nullable=False, default="Activa")
