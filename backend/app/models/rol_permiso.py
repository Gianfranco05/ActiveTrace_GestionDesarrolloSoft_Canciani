import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class RolPermiso(Base):
    __tablename__ = "rol_permiso"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4,
    )
    rol_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("rol.id", ondelete="CASCADE"),
        nullable=False,
    )
    permiso_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("permiso.id", ondelete="CASCADE"),
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        default=lambda: datetime.now(timezone.utc),
    )

    __table_args__ = (
        UniqueConstraint("rol_id", "permiso_id", name="uq_rol_permiso"),
    )
