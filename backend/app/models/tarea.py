from __future__ import annotations

import uuid

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

from .base import BaseModelMixin


class Tarea(BaseModelMixin, Base):
    __tablename__ = "tarea"

    materia_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("materia.id", ondelete="SET NULL"), nullable=True,
    )
    asignado_a: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("usuario.id", ondelete="RESTRICT"), nullable=False, index=True,
    )
    asignado_por: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("usuario.id", ondelete="RESTRICT"), nullable=False, index=True,
    )
    estado: Mapped[str] = mapped_column(
        String(20), nullable=False, default="Pendiente", server_default="Pendiente",
    )
    descripcion: Mapped[str] = mapped_column(Text, nullable=False)
    contexto_id: Mapped[uuid.UUID | None] = mapped_column(nullable=True)

    asignado_a_usuario: Mapped[Usuario] = relationship(  # noqa: F821
        "Usuario", foreign_keys=[asignado_a], lazy="selectin",
    )
    asignado_por_usuario: Mapped[Usuario] = relationship(  # noqa: F821
        "Usuario", foreign_keys=[asignado_por], lazy="selectin",
    )
    materia: Mapped[Materia | None] = relationship(  # noqa: F821
        "Materia", lazy="selectin",
    )
    comentarios: Mapped[list[ComentarioTarea]] = relationship(  # noqa: F821
        "ComentarioTarea", back_populates="tarea", lazy="selectin",
        order_by="ComentarioTarea.creado_at",
    )
