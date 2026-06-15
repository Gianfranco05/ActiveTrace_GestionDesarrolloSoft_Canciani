"""010 — create comunicacion table

Revision ID: 010
Revises: 009
Create Date: 2026-06-02
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "010"
down_revision: str | None = "009"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "comunicacion",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("tenant_id", sa.Uuid(), nullable=False),
        sa.Column("lote_id", sa.Uuid(), nullable=False),
        sa.Column("enviado_por", sa.Uuid(), nullable=True),
        sa.Column("materia_id", sa.Uuid(), nullable=True),
        sa.Column("entrada_padron_id", sa.Uuid(), nullable=True),
        sa.Column("destinatario", sa.Text(), nullable=False),
        sa.Column("asunto", sa.Text(), nullable=False),
        sa.Column("cuerpo", sa.Text(), nullable=False),
        sa.Column("template_id", sa.Uuid(), nullable=True),
        sa.Column("variables", sa.JSON(), nullable=False, server_default="{}"),
        sa.Column("estado", sa.String(20), nullable=False, server_default="Pendiente"),
        sa.Column("requiere_aprobacion", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("aprobado_por", sa.Uuid(), nullable=True),
        sa.Column("aprobado_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("enviado_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("error_detalle", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_comunicacion")),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenant.id"], name=op.f("fk_comunicacion_tenant_id"), ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["enviado_por"], ["usuario.id"], name=op.f("fk_comunicacion_enviado_por"), ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["materia_id"], ["materia.id"], name=op.f("fk_comunicacion_materia_id"), ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["entrada_padron_id"], ["entrada_padron.id"], name=op.f("fk_comunicacion_entrada_padron_id"), ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["aprobado_por"], ["usuario.id"], name=op.f("fk_comunicacion_aprobado_por"), ondelete="SET NULL"),
    )
    op.create_index(op.f("ix_comunicacion_tenant_estado"), "comunicacion", ["tenant_id", "estado"])
    op.create_index(op.f("ix_comunicacion_lote_id"), "comunicacion", ["lote_id"])
    op.create_index(op.f("ix_comunicacion_tenant_created"), "comunicacion", ["tenant_id", "created_at"])


def downgrade() -> None:
    op.drop_table("comunicacion")
