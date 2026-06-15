"""001 — create tenant table

Revision ID: 001
Revises:
Create Date: 2026-06-02
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "tenant",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("slug", sa.String(100), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
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
        sa.PrimaryKeyConstraint("id", name=op.f("pk_tenant")),
        sa.UniqueConstraint("name", name=op.f("uq_tenant_name")),
        sa.UniqueConstraint("slug", name=op.f("uq_tenant_slug")),
    )
    op.create_index(op.f("ix_tenant_slug"), "tenant", ["slug"], unique=True)

    op.execute(
        sa.text(
            "INSERT INTO tenant (id, name, slug, is_active) "
            "VALUES (gen_random_uuid(), 'Default Tenant', 'default', true)",
        ),
    )


def downgrade() -> None:
    op.execute(
        sa.text("DELETE FROM tenant WHERE slug = 'default'"),
    )
    op.drop_index(op.f("ix_tenant_slug"), table_name="tenant")
    op.drop_table("tenant")
