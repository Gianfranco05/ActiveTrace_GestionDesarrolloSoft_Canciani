import uuid

from sqlalchemy import JSON, Boolean, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.base import BaseModelMixin


class Evaluacion(BaseModelMixin, Base):
    __tablename__ = "evaluacion"

    materia_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("materia.id", ondelete="RESTRICT"), nullable=False
    )
    cohorte_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("cohorte.id", ondelete="RESTRICT"), nullable=False
    )
    tipo: Mapped[str] = mapped_column(String(50), nullable=False)
    instancia: Mapped[str] = mapped_column(String(200), nullable=False)
    cupos_por_dia: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    alumnos_convocados: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    activa: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
