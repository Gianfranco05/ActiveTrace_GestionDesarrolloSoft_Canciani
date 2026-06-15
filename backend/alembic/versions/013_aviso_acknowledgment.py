"""add_aviso_acknowledgment_tables

Revision ID: 013
Revises: 012
Create Date: 2026-06-03
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "013_aviso_acknowledgment"
down_revision: Union[str, None] = "012_evaluacion_reserva_resultado"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "aviso",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("tenant_id", sa.Uuid(), nullable=False),
        sa.Column("alcance", sa.String(20), nullable=False),
        sa.Column("materia_id", sa.Uuid(), nullable=True),
        sa.Column("cohorte_id", sa.Uuid(), nullable=True),
        sa.Column("rol_destino", sa.String(50), nullable=True),
        sa.Column("severidad", sa.String(20), nullable=False),
        sa.Column("titulo", sa.String(200), nullable=False),
        sa.Column("cuerpo", sa.Text(), nullable=False),
        sa.Column("inicio_en", sa.DateTime(timezone=True), nullable=False),
        sa.Column("fin_en", sa.DateTime(timezone=True), nullable=False),
        sa.Column("orden", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("activo", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("requiere_ack", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenant.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["materia_id"], ["materia.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["cohorte_id"], ["cohorte.id"], ondelete="RESTRICT"),
    )
    op.create_index("ix_aviso_tenant_id", "aviso", ["tenant_id"])
    op.create_index("ix_aviso_activo_vigencia", "aviso", ["activo", "inicio_en", "fin_en"])
    op.create_index("ix_aviso_alcance_materia", "aviso", ["alcance", "materia_id"])
    op.create_index("ix_aviso_alcance_cohorte", "aviso", ["alcance", "cohorte_id"])
    op.create_index("ix_aviso_alcance_rol", "aviso", ["alcance", "rol_destino"])

    op.create_table(
        "acknowledgment_aviso",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("aviso_id", sa.Uuid(), nullable=False),
        sa.Column("usuario_id", sa.Uuid(), nullable=False),
        sa.Column("confirmado_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("aviso_id", "usuario_id", name="uq_acknowledgment_aviso_user"),
        sa.ForeignKeyConstraint(["aviso_id"], ["aviso.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["usuario_id"], ["usuario.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_acknowledgment_aviso_id", "acknowledgment_aviso", ["aviso_id"])


def downgrade() -> None:
    op.drop_table("acknowledgment_aviso")
    op.drop_table("aviso")
