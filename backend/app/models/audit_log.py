import uuid
from datetime import UTC, datetime

from sqlalchemy import JSON, DateTime, ForeignKey, Index, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class AuditLog(Base):
    __tablename__ = "audit_log"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("tenant.id", ondelete="CASCADE"),
        nullable=False,
    )
    fecha_hora: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        default=lambda: datetime.now(UTC),
    )
    actor_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("auth_user.id"),
        nullable=False,
    )
    impersonado_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("auth_user.id"),
        nullable=True,
    )
    materia_id: Mapped[uuid.UUID | None] = mapped_column(nullable=True)
    accion: Mapped[str] = mapped_column(String(50), nullable=False)
    detalle: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    filas_afectadas: Mapped[int] = mapped_column(Integer, default=0)
    ip: Mapped[str | None] = mapped_column(String(45), nullable=True)
    user_agent: Mapped[str | None] = mapped_column(String(500), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        default=lambda: datetime.now(UTC),
    )

    __table_args__ = (
        Index("ix_audit_log_tenant_fecha", "tenant_id", fecha_hora.desc()),
        Index("ix_audit_log_tenant_accion", "tenant_id", "accion"),
        Index("ix_audit_log_tenant_actor", "tenant_id", "actor_id"),
    )
