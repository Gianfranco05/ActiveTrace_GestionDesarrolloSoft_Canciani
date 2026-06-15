"""004 — create audit_log table + append-only trigger

Revision ID: 004
Revises: 003
Create Date: 2026-06-02
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "004"
down_revision: str | None = "003"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "audit_log",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("tenant_id", sa.Uuid(), nullable=False),
        sa.Column(
            "fecha_hora",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column("actor_id", sa.Uuid(), nullable=False),
        sa.Column("impersonado_id", sa.Uuid(), nullable=True),
        sa.Column("materia_id", sa.Uuid(), nullable=True),
        sa.Column("accion", sa.String(50), nullable=False),
        sa.Column("detalle", sa.JSON(), nullable=True),
        sa.Column("filas_afectadas", sa.Integer(), server_default="0", nullable=False),
        sa.Column("ip", sa.String(45), nullable=True),
        sa.Column("user_agent", sa.String(500), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_audit_log")),
        sa.ForeignKeyConstraint(
            ["tenant_id"],
            ["tenant.id"],
            name=op.f("fk_audit_log_tenant_id"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["actor_id"],
            ["auth_user.id"],
            name=op.f("fk_audit_log_actor_id"),
        ),
        sa.ForeignKeyConstraint(
            ["impersonado_id"],
            ["auth_user.id"],
            name=op.f("fk_audit_log_impersonado_id"),
        ),
    )

    op.create_index(
        op.f("ix_audit_log_tenant_fecha"),
        "audit_log",
        ["tenant_id", sa.text("fecha_hora DESC")],
    )
    op.create_index(
        op.f("ix_audit_log_tenant_accion"),
        "audit_log",
        ["tenant_id", "accion"],
    )
    op.create_index(
        op.f("ix_audit_log_tenant_actor"),
        "audit_log",
        ["tenant_id", "actor_id"],
    )

    _create_append_only_trigger()
    _seed_auditoria_permiso()


def downgrade() -> None:
    op.execute("DROP TRIGGER IF EXISTS trg_audit_log_no_update ON audit_log")
    op.execute("DROP TRIGGER IF EXISTS trg_audit_log_no_delete ON audit_log")
    op.execute("DROP FUNCTION IF EXISTS reject_audit_log_mods()")
    op.drop_table("audit_log")


def _create_append_only_trigger() -> None:
    op.execute(
        """
        CREATE OR REPLACE FUNCTION reject_audit_log_mods()
        RETURNS TRIGGER AS $$
        BEGIN
            RAISE EXCEPTION 'audit_log is append-only: UPDATE/DELETE not allowed';
        END;
        $$ LANGUAGE plpgsql;
        """,
    )
    op.execute(
        """
        CREATE TRIGGER trg_audit_log_no_update
            BEFORE UPDATE ON audit_log
            FOR EACH ROW EXECUTE FUNCTION reject_audit_log_mods()
        """,
    )
    op.execute(
        """
        CREATE TRIGGER trg_audit_log_no_delete
            BEFORE DELETE ON audit_log
            FOR EACH ROW EXECUTE FUNCTION reject_audit_log_mods()
        """,
    )


def _seed_auditoria_permiso() -> None:
    op.execute(
        sa.text(
            "INSERT INTO permiso (id, codigo, descripcion) "
            "SELECT gen_random_uuid(), 'auditoria:ver', 'Ver auditoría' "
            "WHERE NOT EXISTS (SELECT 1 FROM permiso p WHERE p.codigo = 'auditoria:ver')",
        ),
    )
