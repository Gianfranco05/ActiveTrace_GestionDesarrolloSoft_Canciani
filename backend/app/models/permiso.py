import uuid
from datetime import UTC, datetime

from sqlalchemy import DateTime, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class Permiso(Base):
    __tablename__ = "permiso"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4,
    )
    codigo: Mapped[str] = mapped_column(
        String(80), nullable=False,
    )
    descripcion: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        default=lambda: datetime.now(UTC),
    )

    __table_args__ = (
        UniqueConstraint("codigo", name="uq_permiso_codigo"),
    )
