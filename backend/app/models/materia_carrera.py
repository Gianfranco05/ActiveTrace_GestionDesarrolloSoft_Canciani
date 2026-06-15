from __future__ import annotations

import uuid

from sqlalchemy import ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.base import BaseModelMixin


class MateriaCarrera(BaseModelMixin, Base):
    __tablename__ = "materia_carrera"

    materia_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("materia.id", ondelete="CASCADE"), nullable=False,
    )
    carrera_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("carrera.id", ondelete="CASCADE"), nullable=False,
    )

    __table_args__ = (
        UniqueConstraint("materia_id", "carrera_id", name="uq_materia_carrera"),
    )
