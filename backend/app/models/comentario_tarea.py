from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy import DateTime, ForeignKey, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

from .base import BaseModelMixin


class ComentarioTarea(BaseModelMixin, Base):
    __tablename__ = "comentario_tarea"

    tarea_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("tarea.id", ondelete="CASCADE"), nullable=False, index=True,
    )
    autor_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("usuario.id", ondelete="RESTRICT"), nullable=False,
    )
    texto: Mapped[str] = mapped_column(Text, nullable=False)
    creado_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        default=lambda: datetime.now(UTC),
    )

    tarea: Mapped[Tarea] = relationship("Tarea", back_populates="comentarios")  # noqa: F821
    autor: Mapped[Usuario] = relationship("Usuario", lazy="selectin")  # noqa: F821
