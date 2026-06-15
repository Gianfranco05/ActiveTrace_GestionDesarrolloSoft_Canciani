"""008 — create calificacion and umbral_materia tables + seed permissions

Revision ID: 008
Revises: 007
Create Date: 2026-06-02
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "008"
down_revision: str | None = "007"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "calificacion",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("tenant_id", sa.Uuid(), nullable=False),
        sa.Column("materia_id", sa.Uuid(), nullable=False),
        sa.Column("cohorte_id", sa.Uuid(), nullable=False),
        sa.Column("entrada_padron_id", sa.Uuid(), nullable=False),
        sa.Column("actividad", sa.String(200), nullable=False),
        sa.Column("tipo", sa.String(20), nullable=False),
        sa.Column("nota_numerica", sa.Numeric(5, 2), nullable=True),
        sa.Column("nota_textual", sa.Text(), nullable=True),
        sa.Column("aprobado", sa.Boolean(), nullable=False),
        sa.Column("origen", sa.String(20), nullable=False, server_default="Importado"),
        sa.Column("cargado_por", sa.Uuid(), nullable=False),
        sa.Column("importado_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_calificacion")),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenant.id"], name=op.f("fk_calificacion_tenant_id"), ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["materia_id"], ["materia.id"], name=op.f("fk_calificacion_materia_id"), ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["cohorte_id"], ["cohorte.id"], name=op.f("fk_calificacion_cohorte_id"), ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["entrada_padron_id"], ["entrada_padron.id"], name=op.f("fk_calificacion_entrada_padron_id"), ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["cargado_por"], ["usuario.id"], name=op.f("fk_calificacion_cargado_por"), ondelete="RESTRICT"),
    )
    op.create_index(op.f("ix_calificacion_tenant_id"), "calificacion", ["tenant_id"])
    op.create_index(op.f("ix_calificacion_materia_cohorte"), "calificacion", ["materia_id", "cohorte_id"])
    op.create_index(op.f("ix_calificacion_entrada_padron_id"), "calificacion", ["entrada_padron_id"])
    op.create_index(op.f("ix_calificacion_cargado_por"), "calificacion", ["cargado_por"])

    op.create_table(
        "umbral_materia",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("tenant_id", sa.Uuid(), nullable=False),
        sa.Column("materia_id", sa.Uuid(), nullable=False),
        sa.Column("asignacion_id", sa.Uuid(), nullable=True),
        sa.Column("umbral_pct", sa.Integer(), nullable=False, server_default="60"),
        sa.Column("valores_aprobatorios", sa.JSON(), nullable=False, server_default='[]'),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_umbral_materia")),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenant.id"], name=op.f("fk_umbral_materia_tenant_id"), ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["materia_id"], ["materia.id"], name=op.f("fk_umbral_materia_materia_id"), ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["asignacion_id"], ["asignacion.id"], name=op.f("fk_umbral_materia_asignacion_id"), ondelete="SET NULL"),
    )
    op.create_index(op.f("ix_umbral_materia_tenant_id"), "umbral_materia", ["tenant_id"])
    op.create_index(op.f("ix_umbral_materia_materia_id"), "umbral_materia", ["materia_id"])
    op.create_unique_constraint(
        "uq_umbral_materia",
        "umbral_materia",
        ["tenant_id", "materia_id", "asignacion_id"],
    )

    _seed_calificaciones_permisos()


def downgrade() -> None:
    op.drop_table("umbral_materia")
    op.drop_table("calificacion")


def _seed_calificaciones_permisos() -> None:
    op.execute(
        sa.text(
            "INSERT INTO permiso (id, codigo, descripcion) "
            "SELECT gen_random_uuid(), 'calificaciones:cargar', 'Cargar calificaciones y gestionar umbral' "
            "WHERE NOT EXISTS (SELECT 1 FROM permiso p WHERE p.codigo = 'calificaciones:cargar')",
        ),
    )
    op.execute(
        sa.text(
            "INSERT INTO permiso (id, codigo, descripcion) "
            "SELECT gen_random_uuid(), 'calificaciones:ver', 'Ver calificaciones y umbral' "
            "WHERE NOT EXISTS (SELECT 1 FROM permiso p WHERE p.codigo = 'calificaciones:ver')",
        ),
    )

    _assign_permiso_to_roles("calificaciones:cargar", ["PROFESOR", "COORDINADOR", "ADMIN"])
    _assign_permiso_to_roles("calificaciones:ver", ["PROFESOR", "COORDINADOR", "ADMIN"])


def _assign_permiso_to_roles(permiso_codigo: str, roles: list[str]) -> None:
    for rol_nombre in roles:
        op.execute(
            sa.text(
                "INSERT INTO rol_permiso (id, rol_id, permiso_id) "
                "SELECT gen_random_uuid(), r.id, p.id "
                "FROM rol r, permiso p "
                "WHERE r.nombre = :rol_nombre "
                "AND p.codigo = :permiso_codigo "
                "AND NOT EXISTS ("
                "  SELECT 1 FROM rol_permiso rp "
                "  WHERE rp.rol_id = r.id AND rp.permiso_id = p.id"
                ")",
            ).bindparams(rol_nombre=rol_nombre, permiso_codigo=permiso_codigo),
        )
