"""016 — add liquidacion, factura, salario_base, salario_plus, grupo_materia tables

Revision ID: 016
Revises: 015_programa_materia_fecha_academica
Create Date: 2026-06-03
"""

from collections.abc import Sequence
from typing import Union

import sqlalchemy as sa
from alembic import op

revision: str = "016_liquidaciones_y_honorarios"
down_revision: Union[str, None] = "015_programa_materia_fecha_academica"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "salario_base",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("tenant_id", sa.Uuid(), nullable=False),
        sa.Column("rol", sa.String(30), nullable=False),
        sa.Column("monto", sa.Numeric(12, 2), nullable=False),
        sa.Column("vig_desde", sa.Date(), nullable=False),
        sa.Column("vig_hasta", sa.Date(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenant.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_salario_base_tenant_id", "salario_base", ["tenant_id"])
    op.create_index(
        "uq_salario_base_rol_active",
        "salario_base", ["tenant_id", "rol"],
        unique=True,
        postgresql_where=sa.text("deleted_at IS NULL"),
    )

    op.create_table(
        "salario_plus",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("tenant_id", sa.Uuid(), nullable=False),
        sa.Column("grupo", sa.String(50), nullable=False),
        sa.Column("rol", sa.String(30), nullable=False),
        sa.Column("descripcion", sa.String(200), nullable=False),
        sa.Column("monto", sa.Numeric(12, 2), nullable=False),
        sa.Column("vig_desde", sa.Date(), nullable=False),
        sa.Column("vig_hasta", sa.Date(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenant.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_salario_plus_tenant_id", "salario_plus", ["tenant_id"])
    op.create_index(
        "uq_salario_plus_grupo_rol_active",
        "salario_plus", ["tenant_id", "grupo", "rol"],
        unique=True,
        postgresql_where=sa.text("deleted_at IS NULL"),
    )

    op.create_table(
        "grupo_materia",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("tenant_id", sa.Uuid(), nullable=False),
        sa.Column("grupo", sa.String(50), nullable=False),
        sa.Column("materia_id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenant.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["materia_id"], ["materia.id"], ondelete="RESTRICT"),
    )
    op.create_index("ix_grupo_materia_tenant_id", "grupo_materia", ["tenant_id"])
    op.create_index(
        "uq_grupo_materia_active",
        "grupo_materia", ["tenant_id", "grupo", "materia_id"],
        unique=True,
        postgresql_where=sa.text("deleted_at IS NULL"),
    )

    op.create_table(
        "liquidacion",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("tenant_id", sa.Uuid(), nullable=False),
        sa.Column("cohorte_id", sa.Uuid(), nullable=False),
        sa.Column("periodo", sa.String(7), nullable=False),
        sa.Column("usuario_id", sa.Uuid(), nullable=False),
        sa.Column("rol", sa.String(30), nullable=False),
        sa.Column("comisiones", sa.Text(), nullable=True),
        sa.Column("monto_base", sa.Numeric(12, 2), nullable=False),
        sa.Column("monto_plus", sa.Numeric(12, 2), nullable=False),
        sa.Column("total", sa.Numeric(12, 2), nullable=False),
        sa.Column("es_nexo", sa.Boolean(), nullable=False),
        sa.Column("excluido_por_factura", sa.Boolean(), nullable=False),
        sa.Column("estado", sa.String(20), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenant.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["cohorte_id"], ["cohorte.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["usuario_id"], ["usuario.id"], ondelete="RESTRICT"),
    )
    op.create_index("ix_liquidacion_tenant_id", "liquidacion", ["tenant_id"])
    op.create_index("ix_liquidacion_cohorte_periodo", "liquidacion", ["cohorte_id", "periodo"])
    op.create_index("ix_liquidacion_usuario_id", "liquidacion", ["usuario_id"])
    op.create_index("ix_liquidacion_estado", "liquidacion", ["estado"])
    op.create_index(
        "uq_liquidacion_periodo_docente_active",
        "liquidacion", ["tenant_id", "cohorte_id", "periodo", "usuario_id"],
        unique=True,
        postgresql_where=sa.text("deleted_at IS NULL"),
    )

    op.create_table(
        "factura",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("tenant_id", sa.Uuid(), nullable=False),
        sa.Column("usuario_id", sa.Uuid(), nullable=False),
        sa.Column("cohorte_id", sa.Uuid(), nullable=True),
        sa.Column("periodo", sa.String(7), nullable=False),
        sa.Column("detalle", sa.Text(), nullable=False),
        sa.Column("referencia_archivo", sa.String(500), nullable=True),
        sa.Column("tamano_kb", sa.Numeric(10, 2), nullable=True),
        sa.Column("estado", sa.String(20), nullable=False),
        sa.Column("cargada_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("abonada_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenant.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["usuario_id"], ["usuario.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["cohorte_id"], ["cohorte.id"], ondelete="RESTRICT"),
    )
    op.create_index("ix_factura_tenant_id", "factura", ["tenant_id"])
    op.create_index("ix_factura_usuario_periodo", "factura", ["usuario_id", "periodo"])
    op.create_index("ix_factura_estado", "factura", ["estado"])

    _seed_permissions()


def downgrade() -> None:
    op.drop_table("factura")
    op.drop_table("liquidacion")
    op.drop_table("grupo_materia")
    op.drop_table("salario_plus")
    op.drop_table("salario_base")


def _seed_permissions() -> None:
    nuevos_permisos = [
        ("liquidaciones:ver", "Ver liquidaciones"),
        ("liquidaciones:calcular", "Calcular liquidaciones"),
        ("liquidaciones:cerrar", "Cerrar liquidaciones"),
        ("liquidaciones:exportar", "Exportar liquidaciones"),
        ("liquidaciones:configurar-salarios", "Configurar grilla salarial"),
    ]
    for codigo, descripcion in nuevos_permisos:
        op.execute(
            sa.text(
                "INSERT INTO permiso (id, codigo, descripcion) "
                "SELECT gen_random_uuid(), :codigo, :descripcion "
                "WHERE NOT EXISTS (SELECT 1 FROM permiso p WHERE p.codigo = :codigo2)"
            ).bindparams(codigo=codigo, descripcion=descripcion, codigo2=codigo),
        )

    mapping = {
        "FINANZAS": [
            "liquidaciones:ver",
            "liquidaciones:calcular",
            "liquidaciones:cerrar",
            "liquidaciones:exportar",
            "liquidaciones:configurar-salarios",
        ],
        "ADMIN": [
            "liquidaciones:ver",
            "liquidaciones:calcular",
            "liquidaciones:cerrar",
            "liquidaciones:exportar",
            "liquidaciones:configurar-salarios",
        ],
    }
    for rol_nombre, permiso_codigos in mapping.items():
        for permiso_codigo in permiso_codigos:
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
                    ")"
                ).bindparams(rol_nombre=rol_nombre, permiso_codigo=permiso_codigo),
            )
