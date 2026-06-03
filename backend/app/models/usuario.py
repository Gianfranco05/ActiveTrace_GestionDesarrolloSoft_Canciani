from __future__ import annotations

from typing import Optional
import uuid

from sqlalchemy import String, Text, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from .base import BaseModelMixin
from sqlalchemy import event, insert
from app.models.auth_user import AuthUser


class Usuario(BaseModelMixin, Base):
    __tablename__ = "usuario"

    id: Mapped[uuid.UUID] = mapped_column(ForeignKey("auth_user.id", ondelete="CASCADE"), primary_key=True)
    nombre: Mapped[str] = mapped_column(String(120), nullable=False)
    apellidos: Mapped[str] = mapped_column(String(120), nullable=False)
    dni: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    cuil: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    cbu: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    alias_cbu: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    banco: Mapped[Optional[str]] = mapped_column(String(80), nullable=True)
    regional: Mapped[Optional[str]] = mapped_column(String(80), nullable=True)
    legajo: Mapped[Optional[str]] = mapped_column(String(30), nullable=True)
    legajo_profesional: Mapped[Optional[str]] = mapped_column(String(30), nullable=True)
    from sqlalchemy import Boolean

    facturador: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default="false")
    estado: Mapped[str] = mapped_column(String(20), nullable=False, server_default="Activo")

    auth_user = relationship("AuthUser", back_populates="usuario", uselist=False)


@event.listens_for(Usuario, "before_insert")
def ensure_auth_user(mapper, connection, target):
    # If Usuario.id is not set, create a stub AuthUser and reuse its id to satisfy FK
    if not getattr(target, "id", None):
        auth_payload = {
            "email": f"user+{uuid.uuid4().hex}@example.invalid",
            "password_hash": "stub",
            "tenant_id": getattr(target, "tenant_id", None),
        }
        stmt = insert(AuthUser).values(**auth_payload).returning(AuthUser.id)
        res = connection.execute(stmt)
        target.id = res.scalar_one()
