from sqlalchemy import Index, String, UniqueConstraint, text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.base import BaseModelMixin


class Materia(BaseModelMixin, Base):
    __tablename__ = "materia"

    codigo: Mapped[str] = mapped_column(String(20), nullable=False)
    nombre: Mapped[str] = mapped_column(String(200), nullable=False)
    estado: Mapped[str] = mapped_column(String(20), nullable=False, default="Activa")
    grupo_plus: Mapped[str | None] = mapped_column(String(50), nullable=True, default=None)

    __table_args__ = (
        UniqueConstraint("tenant_id", "codigo", name="uq_materia_codigo"),
        Index(
            "ix_materia_codigo_active",
            "tenant_id",
            "codigo",
            unique=True,
            postgresql_where=text("deleted_at IS NULL"),
        ),
    )
