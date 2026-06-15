"""005 — create carrera, cohorte, materia tables

Revision ID: 005
Revises: 004
Create Date: 2026-06-02
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "005"
down_revision: str | None = "004"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "carrera",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("tenant_id", sa.Uuid(), nullable=False),
        sa.Column("codigo", sa.String(20), nullable=False),
        sa.Column("nombre", sa.String(200), nullable=False),
        sa.Column("estado", sa.String(20), nullable=False, server_default="Activa"),
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
        sa.PrimaryKeyConstraint("id", name=op.f("pk_carrera")),
        sa.ForeignKeyConstraint(
            ["tenant_id"],
            ["tenant.id"],
            name=op.f("fk_carrera_tenant_id"),
            ondelete="CASCADE",
        ),
        sa.UniqueConstraint(
            "tenant_id", "codigo", name=op.f("uq_carrera_codigo"),
        ),
    )
    op.create_index(
        op.f("ix_carrera_tenant_id"), "carrera", ["tenant_id"],
    )
    op.create_index(
        "ix_carrera_codigo_active",
        "carrera",
        ["tenant_id", "codigo"],
        unique=True,
        postgresql_where=sa.text("deleted_at IS NULL"),
    )

    op.create_table(
        "cohorte",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("tenant_id", sa.Uuid(), nullable=False),
        sa.Column("carrera_id", sa.Uuid(), nullable=False),
        sa.Column("nombre", sa.String(50), nullable=False),
        sa.Column("anio", sa.Integer(), nullable=False),
        sa.Column("vig_desde", sa.Date(), nullable=False),
        sa.Column("vig_hasta", sa.Date(), nullable=True),
        sa.Column("estado", sa.String(20), nullable=False, server_default="Activa"),
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
        sa.PrimaryKeyConstraint("id", name=op.f("pk_cohorte")),
        sa.ForeignKeyConstraint(
            ["tenant_id"],
            ["tenant.id"],
            name=op.f("fk_cohorte_tenant_id"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["carrera_id"],
            ["carrera.id"],
            name=op.f("fk_cohorte_carrera_id"),
            ondelete="RESTRICT",
        ),
        sa.UniqueConstraint(
            "tenant_id", "carrera_id", "nombre", name=op.f("uq_cohorte_nombre"),
        ),
    )
    op.create_index(
        op.f("ix_cohorte_tenant_id"), "cohorte", ["tenant_id"],
    )
    op.create_index(
        op.f("ix_cohorte_carrera_id"), "cohorte", ["carrera_id"],
    )
    op.create_index(
        "ix_cohorte_nombre_active",
        "cohorte",
        ["tenant_id", "carrera_id", "nombre"],
        unique=True,
        postgresql_where=sa.text("deleted_at IS NULL"),
    )

    op.create_table(
        "materia",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("tenant_id", sa.Uuid(), nullable=False),
        sa.Column("codigo", sa.String(20), nullable=False),
        sa.Column("nombre", sa.String(200), nullable=False),
        sa.Column("estado", sa.String(20), nullable=False, server_default="Activa"),
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
        sa.PrimaryKeyConstraint("id", name=op.f("pk_materia")),
        sa.ForeignKeyConstraint(
            ["tenant_id"],
            ["tenant.id"],
            name=op.f("fk_materia_tenant_id"),
            ondelete="CASCADE",
        ),
        sa.UniqueConstraint(
            "tenant_id", "codigo", name=op.f("uq_materia_codigo"),
        ),
    )
    op.create_index(
        op.f("ix_materia_tenant_id"), "materia", ["tenant_id"],
    )
    op.create_index(
        "ix_materia_codigo_active",
        "materia",
        ["tenant_id", "codigo"],
        unique=True,
        postgresql_where=sa.text("deleted_at IS NULL"),
    )


def downgrade() -> None:
    op.drop_table("materia")
    op.drop_table("cohorte")
    op.drop_table("carrera")
