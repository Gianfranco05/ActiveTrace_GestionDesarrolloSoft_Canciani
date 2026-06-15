from sqlalchemy import Index, String, UniqueConstraint, text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.base import BaseModelMixin


class Carrera(BaseModelMixin, Base):
    __tablename__ = "carrera"

    codigo: Mapped[str] = mapped_column(String(20), nullable=False)
    nombre: Mapped[str] = mapped_column(String(200), nullable=False)
    estado: Mapped[str] = mapped_column(String(20), nullable=False, default="Activa")

    __table_args__ = (
        UniqueConstraint("tenant_id", "codigo", name="uq_carrera_codigo"),
        Index(
            "ix_carrera_codigo_active",
            "tenant_id",
            "codigo",
            unique=True,
            postgresql_where=text("deleted_at IS NULL"),
        ),
    )
