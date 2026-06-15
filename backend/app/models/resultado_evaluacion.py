import uuid

from sqlalchemy import ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.base import BaseModelMixin


class ResultadoEvaluacion(BaseModelMixin, Base):
    __tablename__ = "resultado_evaluacion"

    evaluacion_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("evaluacion.id", ondelete="RESTRICT"), nullable=False
    )
    alumno_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("usuario.id", ondelete="RESTRICT"), nullable=False
    )
    nota_final: Mapped[str] = mapped_column(String(50), nullable=False)

    __table_args__ = (
        UniqueConstraint(
            "evaluacion_id", "alumno_id",
            name="uq_resultado_evaluacion_alumno",
        ),
    )
