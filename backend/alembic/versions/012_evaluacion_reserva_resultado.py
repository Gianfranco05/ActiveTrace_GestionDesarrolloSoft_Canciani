"""add_evaluacion_reserva_resultado_tables

Revision ID: 012
Revises: 011
Create Date: 2026-06-03
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "012_evaluacion_reserva_resultado"
down_revision: Union[str, None] = "011"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "evaluacion",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("tenant_id", sa.Uuid(), nullable=False),
        sa.Column("materia_id", sa.Uuid(), nullable=False),
        sa.Column("cohorte_id", sa.Uuid(), nullable=False),
        sa.Column("tipo", sa.String(50), nullable=False),
        sa.Column("instancia", sa.String(200), nullable=False),
        sa.Column("cupos_por_dia", sa.JSON(), nullable=False, server_default="[]"),
        sa.Column("alumnos_convocados", sa.JSON(), nullable=False, server_default="[]"),
        sa.Column("activa", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["materia_id"], ["materia.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["cohorte_id"], ["cohorte.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenant.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_evaluacion_tenant_id", "evaluacion", ["tenant_id"])

    op.create_table(
        "reserva_evaluacion",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("tenant_id", sa.Uuid(), nullable=False),
        sa.Column("evaluacion_id", sa.Uuid(), nullable=False),
        sa.Column("alumno_id", sa.Uuid(), nullable=False),
        sa.Column("fecha_hora", sa.DateTime(timezone=True), nullable=False),
        sa.Column("estado", sa.String(20), nullable=False, server_default="Activa"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["evaluacion_id"], ["evaluacion.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["alumno_id"], ["usuario.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenant.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_reserva_evaluacion_tenant_id", "reserva_evaluacion", ["tenant_id"])

    op.create_table(
        "resultado_evaluacion",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("tenant_id", sa.Uuid(), nullable=False),
        sa.Column("evaluacion_id", sa.Uuid(), nullable=False),
        sa.Column("alumno_id", sa.Uuid(), nullable=False),
        sa.Column("nota_final", sa.String(50), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("evaluacion_id", "alumno_id", name="uq_resultado_evaluacion_alumno"),
        sa.ForeignKeyConstraint(["evaluacion_id"], ["evaluacion.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["alumno_id"], ["usuario.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenant.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_resultado_evaluacion_tenant_id", "resultado_evaluacion", ["tenant_id"])


def downgrade() -> None:
    op.drop_table("resultado_evaluacion")
    op.drop_table("reserva_evaluacion")
    op.drop_table("evaluacion")
