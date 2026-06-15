"""007 — create version_padron and entrada_padron tables

Revision ID: 007
Revises: 006
Create Date: 2026-06-02
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "007"
down_revision: str | None = "006"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "version_padron",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("tenant_id", sa.Uuid(), nullable=False),
        sa.Column("materia_id", sa.Uuid(), nullable=True),
        sa.Column("cohorte_id", sa.Uuid(), nullable=True),
        sa.Column("cargado_por", sa.Uuid(), nullable=True),
        sa.Column("cargado_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("activa", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_version_padron")),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenant.id"], name=op.f("fk_version_padron_tenant_id"), ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["materia_id"], ["materia.id"], name=op.f("fk_version_padron_materia_id"), ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["cohorte_id"], ["cohorte.id"], name=op.f("fk_version_padron_cohorte_id"), ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["cargado_por"], ["usuario.id"], name=op.f("fk_version_padron_cargado_por"), ondelete="SET NULL"),
    )
    op.create_index(op.f("ix_version_padron_tenant_id"), "version_padron", ["tenant_id"])
    op.create_index(op.f("ix_version_padron_materia_id"), "version_padron", ["materia_id"])
    op.create_index(op.f("ix_version_padron_cohorte_id"), "version_padron", ["cohorte_id"])

    op.create_table(
        "entrada_padron",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("tenant_id", sa.Uuid(), nullable=False),
        sa.Column("version_id", sa.Uuid(), nullable=False),
        sa.Column("usuario_id", sa.Uuid(), nullable=True),
        sa.Column("nombre", sa.String(120), nullable=False),
        sa.Column("apellidos", sa.String(120), nullable=False),
        sa.Column("email", sa.Text(), nullable=True),
        sa.Column("comision", sa.String(80), nullable=True),
        sa.Column("regional", sa.String(80), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_entrada_padron")),
        sa.ForeignKeyConstraint(["version_id"], ["version_padron.id"], name=op.f("fk_entrada_padron_version_id"), ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenant.id"], name=op.f("fk_entrada_padron_tenant_id"), ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["usuario_id"], ["usuario.id"], name=op.f("fk_entrada_padron_usuario_id"), ondelete="SET NULL"),
    )
    op.create_index(op.f("ix_entrada_padron_version_id"), "entrada_padron", ["version_id"])


def downgrade() -> None:
    op.drop_table("entrada_padron")
    op.drop_table("version_padron")
