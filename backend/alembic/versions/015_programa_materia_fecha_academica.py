"""add programa_materia fecha_academica tables

Revision ID: 015
Revises: 014_tarea_comentario_tarea
Create Date: 2026-06-03
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "015_programa_materia_fecha_academica"
down_revision: Union[str, None] = "014_tarea_comentario_tarea"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "programa_materia",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("tenant_id", sa.Uuid(), nullable=False),
        sa.Column("materia_id", sa.Uuid(), nullable=False),
        sa.Column("carrera_id", sa.Uuid(), nullable=False),
        sa.Column("cohorte_id", sa.Uuid(), nullable=False),
        sa.Column("titulo", sa.String(300), nullable=False),
        sa.Column("referencia_archivo", sa.String(500), nullable=False),
        sa.Column("cargado_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["materia_id"], ["materia.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["carrera_id"], ["carrera.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["cohorte_id"], ["cohorte.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenant.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_programa_materia_tenant_id", "programa_materia", ["tenant_id"])
    op.create_index("ix_programa_materia_materia_id", "programa_materia", ["materia_id"])
    op.create_index("ix_programa_materia_carrera_id", "programa_materia", ["carrera_id"])
    op.create_index("ix_programa_materia_cohorte_id", "programa_materia", ["cohorte_id"])

    op.create_table(
        "fecha_academica",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("tenant_id", sa.Uuid(), nullable=False),
        sa.Column("materia_id", sa.Uuid(), nullable=False),
        sa.Column("cohorte_id", sa.Uuid(), nullable=False),
        sa.Column("tipo", sa.String(20), nullable=False),
        sa.Column("numero", sa.Integer(), nullable=False),
        sa.Column("periodo", sa.String(20), nullable=False),
        sa.Column("fecha", sa.Date(), nullable=False),
        sa.Column("titulo", sa.String(200), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["materia_id"], ["materia.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["cohorte_id"], ["cohorte.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenant.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_fecha_academica_tenant_id", "fecha_academica", ["tenant_id"])
    op.create_index("ix_fecha_academica_materia_id", "fecha_academica", ["materia_id"])
    op.create_index("ix_fecha_academica_cohorte_id", "fecha_academica", ["cohorte_id"])


def downgrade() -> None:
    op.drop_table("fecha_academica")
    op.drop_table("programa_materia")
