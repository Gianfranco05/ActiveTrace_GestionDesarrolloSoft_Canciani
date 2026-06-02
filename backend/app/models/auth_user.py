import uuid
from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, ForeignKey, Index, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import BaseModelMixin


class AuthUser(BaseModelMixin, Base):
    __tablename__ = "auth_user"

    email: Mapped[str] = mapped_column(String(255), nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    is_2fa_enabled: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    otp_secret: Mapped[str | None] = mapped_column(String(255), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    __table_args__ = (
        UniqueConstraint("tenant_id", "email", name="uq_auth_user_email"),
        Index(
            "ix_auth_user_email_active",
            "tenant_id",
            "email",
            postgresql_where=BaseModelMixin.deleted_at.is_(None),
        ),
    )

    # One-to-one relationship to Usuario profile (defined in usuarios change)
    # back_populates kept in sync with Usuario.auth_user
    usuario = relationship("Usuario", back_populates="auth_user", uselist=False)


class RefreshToken(Base):
    __tablename__ = "refresh_token"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    token_hash: Mapped[str] = mapped_column(
        String(128), unique=True, nullable=False, index=True,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("auth_user.id", ondelete="CASCADE"), nullable=False,
    )
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("tenant.id", ondelete="CASCADE"), nullable=False,
    )
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False,
    )
    is_used: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        default=lambda: datetime.now(timezone.utc),
    )


class ResetToken(Base):
    __tablename__ = "reset_token"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("auth_user.id", ondelete="CASCADE"), nullable=False,
    )
    token_hash: Mapped[str] = mapped_column(
        String(128), unique=True, nullable=False, index=True,
    )
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False,
    )
    is_used: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        default=lambda: datetime.now(timezone.utc),
    )
