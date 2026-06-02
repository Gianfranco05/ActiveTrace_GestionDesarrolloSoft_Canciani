from __future__ import annotations

from typing import Optional

from sqlalchemy import Boolean, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import BaseModelMixin


class VersionPadron(BaseModelMixin):
    __tablename__ = "version_padron"

    materia_id: Mapped[str] = mapped_column(ForeignKey("materia.id"), nullable=False)
    cohorte_id: Mapped[str] = mapped_column(ForeignKey("cohorte.id"), nullable=False)
    activa: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="true")


class EntradaPadron(BaseModelMixin):
    __tablename__ = "entrada_padron"

    version_id: Mapped[str] = mapped_column(ForeignKey("version_padron.id"), nullable=False)
    usuario_id: Mapped[Optional[str]] = mapped_column(ForeignKey("usuario.id"), nullable=True)
    nombre: Mapped[str] = mapped_column(String(120), nullable=False)
    apellidos: Mapped[str] = mapped_column(String(120), nullable=False)
    email: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    comision: Mapped[Optional[str]] = mapped_column(String(80), nullable=True)
    regional: Mapped[Optional[str]] = mapped_column(String(80), nullable=True)

    version = relationship("VersionPadron")
