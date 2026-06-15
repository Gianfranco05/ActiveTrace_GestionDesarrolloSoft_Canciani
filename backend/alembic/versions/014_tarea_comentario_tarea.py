"""add_tarea_comentario_tarea_tables

Revision ID: 014
Revises: 013_aviso_acknowledgment
Create Date: 2026-06-03
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "014_tarea_comentario_tarea"
down_revision: Union[str, None] = "013_aviso_acknowledgment"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "tarea",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("tenant_id", sa.Uuid(), nullable=False),
        sa.Column("materia_id", sa.Uuid(), nullable=True),
        sa.Column("asignado_a", sa.Uuid(), nullable=False),
        sa.Column("asignado_por", sa.Uuid(), nullable=False),
        sa.Column("estado", sa.String(20), nullable=False, server_default="Pendiente"),
        sa.Column("descripcion", sa.Text(), nullable=False),
        sa.Column("contexto_id", sa.Uuid(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["materia_id"], ["materia.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["asignado_a"], ["usuario.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["asignado_por"], ["usuario.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenant.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_tarea_tenant_id", "tarea", ["tenant_id"])
    op.create_index("ix_tarea_estado", "tarea", ["tenant_id", "estado"])
    op.create_index("ix_tarea_asignado_a", "tarea", ["tenant_id", "asignado_a"])
    op.create_index("ix_tarea_asignado_por", "tarea", ["tenant_id", "asignado_por"])

    op.create_table(
        "comentario_tarea",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("tenant_id", sa.Uuid(), nullable=False),
        sa.Column("tarea_id", sa.Uuid(), nullable=False),
        sa.Column("autor_id", sa.Uuid(), nullable=False),
        sa.Column("texto", sa.Text(), nullable=False),
        sa.Column("creado_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["tarea_id"], ["tarea.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["autor_id"], ["usuario.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenant.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_comentario_tarea_tenant_id", "comentario_tarea", ["tenant_id"])
    op.create_index("ix_comentario_tarea_tarea_id", "comentario_tarea", ["tarea_id"])

    _seed_tareas_permisos()


def downgrade() -> None:
    op.execute(
        sa.text(
            "DELETE FROM rol_permiso WHERE permiso_id IN "
            "(SELECT id FROM permiso WHERE codigo = 'tareas:gestionar') "
            "AND rol_id IN (SELECT id FROM rol WHERE nombre = 'TUTOR')"
        )
    )
    op.drop_table("comentario_tarea")
    op.drop_table("tarea")


def _seed_tareas_permisos() -> None:
    op.execute(
        sa.text(
            "INSERT INTO rol_permiso (id, rol_id, permiso_id) "
            "SELECT gen_random_uuid(), r.id, p.id "
            "FROM rol r, permiso p "
            "WHERE r.nombre = 'TUTOR' "
            "AND p.codigo = 'tareas:gestionar' "
            "AND NOT EXISTS ("
            "  SELECT 1 FROM rol_permiso rp "
            "  WHERE rp.rol_id = r.id AND rp.permiso_id = p.id"
            ")"
        ),
    )
