from __future__ import annotations

from sqlalchemy import Column, ForeignKey, String, Text
from sqlalchemy.orm import relationship

from .base import BaseModelMixin


class Usuario(BaseModelMixin):
    __tablename__ = "usuario"

    id = Column(ForeignKey("auth_user.id"), primary_key=True)
    nombre = Column(String(120), nullable=False)
    apellidos = Column(String(120), nullable=False)
    dni = Column(Text, nullable=True)
    cuil = Column(Text, nullable=True)
    cbu = Column(Text, nullable=True)
    alias_cbu = Column(Text, nullable=True)
    facturador = Column(String(20), nullable=False, server_default="false")
    estado = Column(String(20), nullable=False, server_default="Activo")

    auth_user = relationship("AuthUser", back_populates="usuario", uselist=False)
