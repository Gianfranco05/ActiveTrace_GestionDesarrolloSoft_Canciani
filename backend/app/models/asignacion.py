from __future__ import annotations

from sqlalchemy import Column, ForeignKey, DateTime
from sqlalchemy.orm import relationship

from .base import BaseModelMixin


class Asignacion(BaseModelMixin):
    __tablename__ = "asignacion"

    usuario_id = Column(ForeignKey("usuario.id"), nullable=False)
    rol_id = Column(ForeignKey("rol.id"), nullable=False)
    vig_desde = Column(DateTime, nullable=False)
    vig_hasta = Column(DateTime, nullable=True)
    responsable_id = Column(ForeignKey("asignacion.id"), nullable=True)

    usuario = relationship("Usuario")
    rol = relationship("Rol")
