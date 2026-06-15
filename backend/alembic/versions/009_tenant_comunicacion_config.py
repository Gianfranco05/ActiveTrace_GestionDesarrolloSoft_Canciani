"""009 — add requiere_aprobacion_comunicaciones to tenant, seed perms + audit codes

Revision ID: 009
Revises: 008
Create Date: 2026-06-02
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "009"
down_revision: str | None = "008"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "tenant",
        sa.Column(
            "requiere_aprobacion_comunicaciones",
            sa.Boolean(),
            nullable=False,
            server_default="false",
        ),
    )
    _seed_comunicacion_permisos()


def downgrade() -> None:
    op.drop_column("tenant", "requiere_aprobacion_comunicaciones")


def _seed_comunicacion_permisos() -> None:
    op.execute(
        sa.text(
            "INSERT INTO permiso (id, codigo, descripcion) "
            "SELECT gen_random_uuid(), 'comunicacion:enviar', 'Enviar y cancelar comunicaciones' "
            "WHERE NOT EXISTS (SELECT 1 FROM permiso WHERE codigo = 'comunicacion:enviar')",
        ),
    )
    op.execute(
        sa.text(
            "INSERT INTO permiso (id, codigo, descripcion) "
            "SELECT gen_random_uuid(), 'comunicacion:aprobar', 'Aprobar comunicaciones masivas' "
            "WHERE NOT EXISTS (SELECT 1 FROM permiso WHERE codigo = 'comunicacion:aprobar')",
        ),
    )
    op.execute(
        sa.text(
            "INSERT INTO permiso (id, codigo, descripcion) "
            "SELECT gen_random_uuid(), 'comunicacion:ver', 'Ver comunicaciones' "
            "WHERE NOT EXISTS (SELECT 1 FROM permiso WHERE codigo = 'comunicacion:ver')",
        ),
    )

    _assign_to_role("comunicacion:enviar", ["PROFESOR", "COORDINADOR", "ADMIN"])
    _assign_to_role("comunicacion:aprobar", ["COORDINADOR", "ADMIN"])
    _assign_to_role("comunicacion:ver", ["PROFESOR", "TUTOR", "COORDINADOR", "ADMIN"])


def _assign_to_role(permiso_codigo: str, roles: list[str]) -> None:
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
