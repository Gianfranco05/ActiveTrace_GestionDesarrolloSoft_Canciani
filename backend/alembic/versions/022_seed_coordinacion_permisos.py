"""seed 3 missing coordinacion permissions

Revision ID: 022
Revises: 021_materia_carrera
Create Date: 2026-06-11

Three permissions used in App.tsx route guards (coordinacion:acceso,
monitores:ver, coordinacion:setup) were declared in permissions.py
but never inserted into the permiso table by any previous migration.
This migration adds them idempotently and assigns them to COORDINADOR
and ADMIN roles.
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "022_seed_coordinacion_permisos"
down_revision: Union[str, None] = "021_materia_carrera"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# permission_code → [role names]
PERMISOS: dict[str, list[str]] = {
    "coordinacion:acceso": ["COORDINADOR", "ADMIN"],
    "monitores:ver":       ["COORDINADOR", "ADMIN"],
    "coordinacion:setup":  ["COORDINADOR", "ADMIN"],
}


def upgrade() -> None:
    _seed_permisos(PERMISOS)


def downgrade() -> None:
    codigos = list(PERMISOS.keys())
    placeholders = ", ".join(f":c{i}" for i in range(len(codigos)))
    params = {f"c{i}": c for i, c in enumerate(codigos)}
    conn = op.get_bind()

    binds = [sa.bindparam(f"c{i}", type_=sa.String) for i in range(len(codigos))]

    conn.execute(
        sa.text(
            f"DELETE FROM rol_permiso WHERE permiso_id IN "
            f"(SELECT id FROM permiso WHERE codigo IN ({placeholders}))"
        ).bindparams(*binds),
        params,
    )
    conn.execute(
        sa.text(
            f"DELETE FROM permiso WHERE codigo IN ({placeholders})"
        ).bindparams(*binds),
        params,
    )


def _seed_permisos(permisos: dict[str, list[str]]) -> None:
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

    for permiso_codigo, roles in permisos.items():
        for rol_nombre in roles:
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
