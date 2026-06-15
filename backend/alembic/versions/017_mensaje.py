"""add_mensaje_table

Revision ID: 017
Revises: 016_liquidaciones_y_honorarios
Create Date: 2026-06-04
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "017_mensaje"
down_revision: Union[str, None] = "016_liquidaciones_y_honorarios"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "mensaje",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("tenant_id", sa.Uuid(), nullable=False),
        sa.Column("sender_id", sa.Uuid(), nullable=False),
        sa.Column("recipient_id", sa.Uuid(), nullable=False),
        sa.Column("parent_id", sa.Uuid(), nullable=True),
        sa.Column("asunto", sa.String(250), nullable=False),
        sa.Column("cuerpo", sa.Text(), nullable=False),
        sa.Column("leido", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("leido_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["sender_id"], ["usuario.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["recipient_id"], ["usuario.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["parent_id"], ["mensaje.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenant.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_mensaje_tenant_id", "mensaje", ["tenant_id"])
    op.create_index("ix_mensaje_recipient_id", "mensaje", ["recipient_id"])
    op.create_index("ix_mensaje_parent_id", "mensaje", ["parent_id"])
    op.create_index("ix_mensaje_created_at", "mensaje", ["created_at"])

    _seed_perfil_mensajeria_permisos()


def downgrade() -> None:
    op.execute(
        sa.text(
            "DELETE FROM rol_permiso WHERE permiso_id IN "
            "(SELECT id FROM permiso WHERE codigo IN ('perfil:editar', 'mensajeria:usar'))"
        )
    )
    op.execute(
        sa.text(
            "DELETE FROM permiso WHERE codigo IN ('perfil:editar', 'mensajeria:usar')"
        )
    )
    op.drop_table("mensaje")


def _seed_perfil_mensajeria_permisos() -> None:
    roles = ["ALUMNO", "TUTOR", "PROFESOR", "COORDINADOR", "NEXO", "ADMIN", "FINANZAS"]
    permisos = ["perfil:editar", "mensajeria:usar"]
    conn = op.get_bind()

    for permiso_codigo in permisos:
        conn.execute(
            sa.text(
                "INSERT INTO permiso (id, codigo) "
                "SELECT gen_random_uuid(), :codigo "
                "WHERE NOT EXISTS (SELECT 1 FROM permiso WHERE codigo = :codigo)"
            ).bindparams(sa.bindparam("codigo", type_=sa.String)),
            {"codigo": permiso_codigo},
        )

    for rol_nombre in roles:
        for permiso_codigo in permisos:
            conn.execute(
                sa.text(
                    "INSERT INTO rol_permiso (id, rol_id, permiso_id) "
                    "SELECT gen_random_uuid(), r.id, p.id "
                    "FROM rol r, permiso p "
                    "WHERE r.nombre = :rol_nombre "
                    "AND p.codigo = :permiso_codigo "
                    "AND NOT EXISTS ("
                    "  SELECT 1 FROM rol_permiso rp "
                    "  WHERE rp.rol_id = r.id AND rp.permiso_id = p.id"
                    ")"
                ).bindparams(
                    sa.bindparam("rol_nombre", type_=sa.String),
                    sa.bindparam("permiso_codigo", type_=sa.String),
                ),
                {"rol_nombre": rol_nombre, "permiso_codigo": permiso_codigo},
            )
