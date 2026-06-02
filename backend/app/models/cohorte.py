import uuid
from datetime import date

from sqlalchemy import Date, ForeignKey, Index, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.base import BaseModelMixin


class Cohorte(BaseModelMixin, Base):
    __tablename__ = "cohorte"

    carrera_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("carrera.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    nombre: Mapped[str] = mapped_column(String(50), nullable=False)
    anio: Mapped[int] = mapped_column(Integer, nullable=False)
    vig_desde: Mapped[date] = mapped_column(Date, nullable=False)
    vig_hasta: Mapped[date | None] = mapped_column(Date, nullable=True)
    estado: Mapped[str] = mapped_column(String(20), nullable=False, default="Activa")

    __table_args__ = (
        UniqueConstraint(
            "tenant_id", "carrera_id", "nombre", name="uq_cohorte_nombre",
        ),
        Index(
            "ix_cohorte_nombre_active",
            "tenant_id",
            "carrera_id",
            "nombre",
            unique=True,
            postgresql_where=BaseModelMixin.deleted_at.is_(None),
        ),
    )
