from __future__ import annotations

import uuid
from datetime import UTC, date, datetime
from decimal import Decimal

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.base import BaseModelMixin


class SalarioBase(BaseModelMixin, Base):
    __tablename__ = "salario_base"

    rol: Mapped[str] = mapped_column(String(30), nullable=False)
    monto: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    vig_desde: Mapped[date] = mapped_column(Date, nullable=False)
    vig_hasta: Mapped[date | None] = mapped_column(Date, nullable=True)


class SalarioPlus(BaseModelMixin, Base):
    __tablename__ = "salario_plus"

    grupo: Mapped[str] = mapped_column(String(50), nullable=False)
    rol: Mapped[str] = mapped_column(String(30), nullable=False)
    descripcion: Mapped[str] = mapped_column(String(200), nullable=False)
    monto: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    vig_desde: Mapped[date] = mapped_column(Date, nullable=False)
    vig_hasta: Mapped[date | None] = mapped_column(Date, nullable=True)


class GrupoMateria(BaseModelMixin, Base):
    __tablename__ = "grupo_materia"

    grupo: Mapped[str] = mapped_column(String(50), nullable=False)
    materia_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("materia.id"), nullable=False
    )


class Liquidacion(BaseModelMixin, Base):
    __tablename__ = "liquidacion"

    cohorte_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("cohorte.id"), nullable=False
    )
    periodo: Mapped[str] = mapped_column(String(7), nullable=False)
    usuario_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("usuario.id"), nullable=False
    )
    rol: Mapped[str] = mapped_column(String(30), nullable=False)
    comisiones: Mapped[str | None] = mapped_column(Text, nullable=True)
    monto_base: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    monto_plus: Mapped[Decimal] = mapped_column(
        Numeric(12, 2), nullable=False, default=0
    )
    total: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    es_nexo: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False
    )
    excluido_por_factura: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False
    )
    estado: Mapped[str] = mapped_column(
        String(20), nullable=False, default="Abierta"
    )


class Factura(BaseModelMixin, Base):
    __tablename__ = "factura"

    usuario_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("usuario.id"), nullable=False
    )
    cohorte_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("cohorte.id"), nullable=True
    )
    periodo: Mapped[str] = mapped_column(String(7), nullable=False)
    detalle: Mapped[str] = mapped_column(Text, nullable=False)
    referencia_archivo: Mapped[str | None] = mapped_column(
        String(500), nullable=True
    )
    tamano_kb: Mapped[Decimal | None] = mapped_column(
        Numeric(10, 2), nullable=True
    )
    estado: Mapped[str] = mapped_column(
        String(20), nullable=False, default="Pendiente"
    )
    cargada_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC),
    )
    abonada_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
