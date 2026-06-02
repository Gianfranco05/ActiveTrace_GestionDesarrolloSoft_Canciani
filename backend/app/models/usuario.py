from __future__ import annotations

from typing import Optional
import uuid

from sqlalchemy import String, Text, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from .base import BaseModelMixin


class Usuario(BaseModelMixin, Base):
    __tablename__ = "usuario"

    id: Mapped[uuid.UUID] = mapped_column(ForeignKey("auth_user.id", ondelete="CASCADE"), primary_key=True)
    nombre: Mapped[str] = mapped_column(String(120), nullable=False)
    apellidos: Mapped[str] = mapped_column(String(120), nullable=False)
    dni: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    cuil: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    cbu: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    alias_cbu: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    from sqlalchemy import Boolean

    facturador: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default="false")
    estado: Mapped[str] = mapped_column(String(20), nullable=False, server_default="Activo")

    auth_user = relationship("AuthUser", back_populates="usuario", uselist=False)
