"""006 — create usuario and asignacion tables

Revision ID: 006
Revises: 005
Create Date: 2026-06-02
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "006"
down_revision: str | None = "005"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "usuario",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("tenant_id", sa.Uuid(), nullable=False),
        sa.Column("nombre", sa.String(120), nullable=False),
        sa.Column("apellidos", sa.String(120), nullable=False),
        sa.Column("dni", sa.Text(), nullable=True),
        sa.Column("cuil", sa.Text(), nullable=True),
        sa.Column("cbu", sa.Text(), nullable=True),
        sa.Column("alias_cbu", sa.Text(), nullable=True),
        sa.Column("banco", sa.String(100), nullable=True),
        sa.Column("regional", sa.String(100), nullable=True),
        sa.Column("legajo", sa.String(50), nullable=True),
        sa.Column("legajo_profesional", sa.String(50), nullable=True),
        sa.Column("facturador", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("estado", sa.String(20), nullable=False, server_default="Activo"),
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
        sa.PrimaryKeyConstraint("id", name=op.f("pk_usuario")),
        sa.ForeignKeyConstraint(
            ["id"],
            ["auth_user.id"],
            name=op.f("fk_usuario_id"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id"],
            ["tenant.id"],
            name=op.f("fk_usuario_tenant_id"),
            ondelete="CASCADE",
        ),
    )
    op.create_index(
        op.f("ix_usuario_tenant_id"), "usuario", ["tenant_id"],
    )

    op.create_table(
        "asignacion",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("tenant_id", sa.Uuid(), nullable=False),
        sa.Column("usuario_id", sa.Uuid(), nullable=False),
        sa.Column("rol_id", sa.Uuid(), nullable=False),
        sa.Column("materia_id", sa.Uuid(), nullable=True),
        sa.Column("carrera_id", sa.Uuid(), nullable=True),
        sa.Column("cohorte_id", sa.Uuid(), nullable=True),
        sa.Column("comisiones", sa.Text(), nullable=True),
        sa.Column("responsable_id", sa.Uuid(), nullable=True),
        sa.Column("vig_desde", sa.DateTime(timezone=True), nullable=False),
        sa.Column("vig_hasta", sa.DateTime(timezone=True), nullable=True),
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
        sa.PrimaryKeyConstraint("id", name=op.f("pk_asignacion")),
        sa.ForeignKeyConstraint(
            ["tenant_id"],
            ["tenant.id"],
            name=op.f("fk_asignacion_tenant_id"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["usuario_id"],
            ["usuario.id"],
            name=op.f("fk_asignacion_usuario_id"),
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["rol_id"],
            ["rol.id"],
            name=op.f("fk_asignacion_rol_id"),
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["materia_id"],
            ["materia.id"],
            name=op.f("fk_asignacion_materia_id"),
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["carrera_id"],
            ["carrera.id"],
            name=op.f("fk_asignacion_carrera_id"),
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["cohorte_id"],
            ["cohorte.id"],
            name=op.f("fk_asignacion_cohorte_id"),
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["responsable_id"],
            ["asignacion.id"],
            name=op.f("fk_asignacion_responsable_id"),
            ondelete="SET NULL",
        ),
        sa.UniqueConstraint(
            "usuario_id", "rol_id", "materia_id", "carrera_id", "cohorte_id",
            name=op.f("uq_asignacion_context"),
        ),
    )
    op.create_index(
        op.f("ix_asignacion_tenant_id"), "asignacion", ["tenant_id"],
    )
    op.create_index(
        op.f("ix_asignacion_usuario_id"), "asignacion", ["usuario_id"],
    )
    op.create_index(
        op.f("ix_asignacion_rol_id"), "asignacion", ["rol_id"],
    )
    op.create_index(
        op.f("ix_asignacion_materia_id"), "asignacion", ["materia_id"],
    )
    op.create_index(
        op.f("ix_asignacion_carrera_id"), "asignacion", ["carrera_id"],
    )
    op.create_index(
        op.f("ix_asignacion_cohorte_id"), "asignacion", ["cohorte_id"],
    )
    op.create_index(
        op.f("ix_asignacion_responsable_id"), "asignacion", ["responsable_id"],
    )
    op.create_index(
        "ix_asignacion_context_active",
        "asignacion",
        ["usuario_id", "rol_id", "materia_id", "carrera_id", "cohorte_id"],
        unique=True,
        postgresql_where=sa.text("deleted_at IS NULL"),
    )


def downgrade() -> None:
    op.drop_table("asignacion")
    op.drop_table("usuario")
