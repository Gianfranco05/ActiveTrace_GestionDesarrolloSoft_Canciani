from __future__ import annotations

import uuid
from datetime import UTC, datetime
from decimal import Decimal

from sqlalchemy import JSON, Boolean, DateTime, ForeignKey, Integer, Numeric, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base

from .base import BaseModelMixin


class Calificacion(BaseModelMixin, Base):
    __tablename__ = "calificacion"

    materia_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("materia.id"), nullable=False)
    cohorte_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("cohorte.id"), nullable=False)
    entrada_padron_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("entrada_padron.id"), nullable=False)
    actividad: Mapped[str] = mapped_column(String(200), nullable=False)
    tipo: Mapped[str] = mapped_column(String(20), nullable=False)
    nota_numerica: Mapped[Decimal | None] = mapped_column(Numeric(5, 2), nullable=True)
    nota_textual: Mapped[str | None] = mapped_column(Text, nullable=True)
    aprobado: Mapped[bool] = mapped_column(Boolean, nullable=False)
    origen: Mapped[str] = mapped_column(String(20), nullable=False, default="Importado")
    cargado_por: Mapped[uuid.UUID] = mapped_column(ForeignKey("usuario.id"), nullable=False)
    importado_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC),
    )


class UmbralMateria(BaseModelMixin, Base):
    __tablename__ = "umbral_materia"

    materia_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("materia.id"), nullable=False)
    asignacion_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("asignacion.id"), nullable=True
    )
    umbral_pct: Mapped[int] = mapped_column(Integer, nullable=False, default=60)
    valores_aprobatorios: Mapped[list[str]] = mapped_column(
        JSON, nullable=False, default=list,
    )

    __table_args__ = (
        UniqueConstraint(
            "tenant_id", "materia_id", "asignacion_id",
            name="uq_umbral_materia",
        ),
    )
