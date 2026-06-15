"""011 — create slot_encuentro, instancia_encuentro, guardia tables + seed permisos

Revision ID: 011
Revises: 010
Create Date: 2026-06-03
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "011"
down_revision: str | None = "010"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _seed_encuentros_permisos() -> None:
    conn = op.get_bind()

    result = conn.execute(
        sa.text("SELECT id FROM permiso WHERE codigo = :codigo"),
        {"codigo": "encuentros:gestionar"},
    )
    if result.fetchone() is None:
        conn.execute(
            sa.text("INSERT INTO permiso (id, codigo, descripcion, created_at) VALUES (gen_random_uuid(), :codigo, NULL, now())"),
            {"codigo": "encuentros:gestionar"},
        )

    roles = conn.execute(
        sa.text("SELECT id FROM rol WHERE nombre IN ('PROFESOR', 'COORDINADOR', 'ADMIN')")
    ).fetchall()
    permiso_row = conn.execute(
        sa.text("SELECT id FROM permiso WHERE codigo = :codigo"),
        {"codigo": "encuentros:gestionar"},
    ).fetchone()
    if permiso_row is None:
        return

    permiso_id = permiso_row[0]
    for rol_row in roles:
        rol_id = rol_row[0]
        existing = conn.execute(
            sa.text("SELECT 1 FROM rol_permiso WHERE rol_id = :rol_id AND permiso_id = :permiso_id"),
            {"rol_id": rol_id, "permiso_id": permiso_id},
        ).fetchone()
        if existing is None:
            conn.execute(
                sa.text("INSERT INTO rol_permiso (rol_id, permiso_id) VALUES (:rol_id, :permiso_id)"),
                {"rol_id": rol_id, "permiso_id": permiso_id},
            )


def upgrade() -> None:
    op.create_table(
        "slot_encuentro",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("tenant_id", sa.Uuid(), nullable=False),
        sa.Column("asignacion_id", sa.Uuid(), nullable=False),
        sa.Column("materia_id", sa.Uuid(), nullable=False),
        sa.Column("titulo", sa.String(200), nullable=False),
        sa.Column("hora", sa.Time(), nullable=False),
        sa.Column("dia_semana", sa.String(10), nullable=True),
        sa.Column("fecha_inicio", sa.Date(), nullable=True),
        sa.Column("cant_semanas", sa.Integer(), nullable=True),
        sa.Column("fecha_unica", sa.Date(), nullable=True),
        sa.Column("meet_url", sa.String(500), nullable=True),
        sa.Column("vig_desde", sa.Date(), nullable=True),
        sa.Column("vig_hasta", sa.Date(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_slot_encuentro")),
        sa.ForeignKeyConstraint(
            ["tenant_id"], ["tenant.id"],
            name=op.f("fk_slot_encuentro_tenant_id"), ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["asignacion_id"], ["asignacion.id"],
            name=op.f("fk_slot_encuentro_asignacion_id"), ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["materia_id"], ["materia.id"],
            name=op.f("fk_slot_encuentro_materia_id"), ondelete="RESTRICT",
        ),
    )
    op.create_index("ix_slot_encuentro_materia", "slot_encuentro", ["tenant_id", "materia_id"])
    op.create_index("ix_slot_encuentro_asignacion", "slot_encuentro", ["tenant_id", "asignacion_id"])

    op.create_table(
        "instancia_encuentro",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("tenant_id", sa.Uuid(), nullable=False),
        sa.Column("slot_id", sa.Uuid(), nullable=True),
        sa.Column("materia_id", sa.Uuid(), nullable=False),
        sa.Column("asignacion_id", sa.Uuid(), nullable=False),
        sa.Column("fecha", sa.Date(), nullable=False),
        sa.Column("hora", sa.Time(), nullable=False),
        sa.Column("titulo", sa.String(200), nullable=False),
        sa.Column("estado", sa.String(20), nullable=False, server_default="Programado"),
        sa.Column("meet_url", sa.String(500), nullable=True),
        sa.Column("video_url", sa.String(500), nullable=True),
        sa.Column("comentario", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_instancia_encuentro")),
        sa.ForeignKeyConstraint(
            ["tenant_id"], ["tenant.id"],
            name=op.f("fk_instancia_encuentro_tenant_id"), ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["slot_id"], ["slot_encuentro.id"],
            name=op.f("fk_instancia_encuentro_slot_id"), ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["materia_id"], ["materia.id"],
            name=op.f("fk_instancia_encuentro_materia_id"), ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["asignacion_id"], ["asignacion.id"],
            name=op.f("fk_instancia_encuentro_asignacion_id"), ondelete="RESTRICT",
        ),
    )
    op.create_index("ix_instancia_encuentro_slot", "instancia_encuentro", ["tenant_id", "slot_id"])
    op.create_index("ix_instancia_encuentro_materia", "instancia_encuentro", ["tenant_id", "materia_id"])
    op.create_index("ix_instancia_encuentro_estado", "instancia_encuentro", ["tenant_id", "estado"])
    op.create_index("ix_instancia_encuentro_fecha", "instancia_encuentro", ["fecha"])

    op.create_table(
        "guardia",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("tenant_id", sa.Uuid(), nullable=False),
        sa.Column("asignacion_id", sa.Uuid(), nullable=False),
        sa.Column("materia_id", sa.Uuid(), nullable=False),
        sa.Column("carrera_id", sa.Uuid(), nullable=False),
        sa.Column("cohorte_id", sa.Uuid(), nullable=False),
        sa.Column("dia", sa.String(10), nullable=False),
        sa.Column("horario", sa.String(50), nullable=False),
        sa.Column("estado", sa.String(20), nullable=False, server_default="Pendiente"),
        sa.Column("comentarios", sa.Text(), nullable=True),
        sa.Column("creada_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_guardia")),
        sa.ForeignKeyConstraint(
            ["tenant_id"], ["tenant.id"],
            name=op.f("fk_guardia_tenant_id"), ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["asignacion_id"], ["asignacion.id"],
            name=op.f("fk_guardia_asignacion_id"), ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["materia_id"], ["materia.id"],
            name=op.f("fk_guardia_materia_id"), ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["carrera_id"], ["carrera.id"],
            name=op.f("fk_guardia_carrera_id"), ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["cohorte_id"], ["cohorte.id"],
            name=op.f("fk_guardia_cohorte_id"), ondelete="RESTRICT",
        ),
    )
    op.create_index("ix_guardia_tenant_materia", "guardia", ["tenant_id", "materia_id"])
    op.create_index("ix_guardia_tenant_estado", "guardia", ["tenant_id", "estado"])
    op.create_index("ix_guardia_tenant_dia", "guardia", ["tenant_id", "dia"])
    op.create_index("ix_guardia_creada_at", "guardia", ["creada_at"])

    _seed_encuentros_permisos()


def downgrade() -> None:
    conn = op.get_bind()

    permiso_row = conn.execute(
        sa.text("SELECT id FROM permiso WHERE codigo = :codigo"),
        {"codigo": "encuentros:gestionar"},
    ).fetchone()
    if permiso_row is not None:
        permiso_id = permiso_row[0]
        conn.execute(
            sa.text("DELETE FROM rol_permiso WHERE permiso_id = :pid"),
            {"pid": permiso_id},
        )
        conn.execute(
            sa.text("DELETE FROM permiso WHERE id = :pid"),
            {"pid": permiso_id},
        )

    op.drop_table("guardia")
    op.drop_table("instancia_encuentro")
    op.drop_table("slot_encuentro")
