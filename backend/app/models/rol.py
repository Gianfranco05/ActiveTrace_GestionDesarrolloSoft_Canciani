from sqlalchemy import Index, String, Text, UniqueConstraint, text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.base import BaseModelMixin


class Rol(BaseModelMixin, Base):
    __tablename__ = "rol"

    nombre: Mapped[str] = mapped_column(String(50), nullable=False)
    descripcion: Mapped[str | None] = mapped_column(Text, nullable=True)

    __table_args__ = (
        UniqueConstraint("tenant_id", "nombre", name="uq_rol_nombre"),
        Index(
            "ix_rol_nombre_active",
            "tenant_id",
            "nombre",
            postgresql_where=text("deleted_at IS NULL"),
        ),
    )
