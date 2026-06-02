from __future__ import annotations

from typing import Optional

from sqlalchemy import String, Text, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import BaseModelMixin


class Usuario(BaseModelMixin):
    __tablename__ = "usuario"

    id: Mapped[Optional[str]] = mapped_column(ForeignKey("auth_user.id"), primary_key=True)
    nombre: Mapped[str] = mapped_column(String(120), nullable=False)
    apellidos: Mapped[str] = mapped_column(String(120), nullable=False)
    dni: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    cuil: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    cbu: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    alias_cbu: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    facturador: Mapped[str] = mapped_column(String(20), nullable=False, server_default="false")
    estado: Mapped[str] = mapped_column(String(20), nullable=False, server_default="Activo")

    auth_user = relationship("AuthUser", back_populates="usuario", uselist=False)
