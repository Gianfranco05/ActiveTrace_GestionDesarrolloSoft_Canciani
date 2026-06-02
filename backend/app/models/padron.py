from __future__ import annotations

from sqlalchemy import Column, ForeignKey, Boolean, Text
from sqlalchemy.orm import relationship

from .base import BaseModelMixin


class VersionPadron(BaseModelMixin):
    __tablename__ = "version_padron"

    materia_id = Column(ForeignKey("materia.id"), nullable=False)
    cohorte_id = Column(ForeignKey("cohorte.id"), nullable=False)
    activa = Column(Boolean, nullable=False, server_default="true")


class EntradaPadron(BaseModelMixin):
    __tablename__ = "entrada_padron"

    version_id = Column(ForeignKey("version_padron.id"), nullable=False)
    usuario_id = Column(ForeignKey("usuario.id"), nullable=True)
    nombre = Column(String(120), nullable=False)
    apellidos = Column(String(120), nullable=False)
    email = Column(Text, nullable=True)
    comision = Column(String(80), nullable=True)
    regional = Column(String(80), nullable=True)

    version = relationship("VersionPadron")
