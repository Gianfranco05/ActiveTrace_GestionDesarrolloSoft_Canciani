"""002 — create auth_user, refresh_token, reset_token tables

Revision ID: 002
Revises: 001
Create Date: 2026-06-02
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "002"
down_revision: str | None = "001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "auth_user",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("tenant_id", sa.Uuid(), nullable=False),
        sa.Column("email", sa.String(255), nullable=False),
        sa.Column("password_hash", sa.String(255), nullable=False),
        sa.Column(
            "is_2fa_enabled", sa.Boolean(),
            nullable=False, server_default=sa.text("false"),
        ),
        sa.Column("otp_secret", sa.String(255), nullable=True),
        sa.Column(
            "is_active", sa.Boolean(),
            nullable=False, server_default=sa.text("true"),
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "deleted_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_auth_user")),
        sa.ForeignKeyConstraint(
            ["tenant_id"],
            ["tenant.id"],
            name=op.f("fk_auth_user_tenant_id"),
            ondelete="CASCADE",
        ),
        sa.UniqueConstraint(
            "tenant_id", "email", name=op.f("uq_auth_user_email"),
        ),
    )
    op.create_index(
        op.f("ix_auth_user_tenant_id"), "auth_user", ["tenant_id"],
    )
    op.create_index(
        "ix_auth_user_email_active", "auth_user", ["tenant_id", "email"],
        postgresql_where=sa.text("deleted_at IS NULL"),
    )

    op.create_table(
        "refresh_token",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("token_hash", sa.String(128), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("tenant_id", sa.Uuid(), nullable=False),
        sa.Column(
            "expires_at", sa.DateTime(timezone=True), nullable=False,
        ),
        sa.Column(
            "is_used", sa.Boolean(),
            nullable=False, server_default=sa.text("false"),
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_refresh_token")),
        sa.ForeignKeyConstraint(
            ["user_id"], ["auth_user.id"],
            name=op.f("fk_refresh_token_user_id"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id"], ["tenant.id"],
            name=op.f("fk_refresh_token_tenant_id"),
            ondelete="CASCADE",
        ),
        sa.UniqueConstraint(
            "token_hash", name=op.f("uq_refresh_token_token_hash"),
        ),
    )
    op.create_index(
        op.f("ix_refresh_token_token_hash"),
        "refresh_token", ["token_hash"],
    )

    op.create_table(
        "reset_token",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("token_hash", sa.String(128), nullable=False),
        sa.Column(
            "expires_at", sa.DateTime(timezone=True), nullable=False,
        ),
        sa.Column(
            "is_used", sa.Boolean(),
            nullable=False, server_default=sa.text("false"),
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_reset_token")),
        sa.ForeignKeyConstraint(
            ["user_id"], ["auth_user.id"],
            name=op.f("fk_reset_token_user_id"),
            ondelete="CASCADE",
        ),
        sa.UniqueConstraint(
            "token_hash", name=op.f("uq_reset_token_token_hash"),
        ),
    )
    op.create_index(
        op.f("ix_reset_token_token_hash"),
        "reset_token", ["token_hash"],
    )


def downgrade() -> None:
    op.drop_table("reset_token")
    op.drop_table("refresh_token")
    op.drop_table("auth_user")
