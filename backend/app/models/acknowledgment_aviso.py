from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class AcknowledgmentAviso(Base):
    __tablename__ = "acknowledgment_aviso"
    __table_args__ = (
        UniqueConstraint("aviso_id", "usuario_id", name="uq_acknowledgment_aviso_user"),
    )

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    aviso_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("aviso.id", ondelete="CASCADE"), nullable=False,
    )
    usuario_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("usuario.id", ondelete="CASCADE"), nullable=False,
    )
    confirmado_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(),
    )
