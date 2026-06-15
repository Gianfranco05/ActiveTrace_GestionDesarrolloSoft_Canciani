"""assign 5 missing permissions to ADMIN role

Revision ID: 019
Revises: 018_seed_permisos_faltantes
Create Date: 2026-06-08

Five permissions exist in the DB but are only assigned to specific roles
(ALUMNO or FINANZAS). ADMIN should have them all for full tenant control.
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "019_admin_permisos_faltantes"
down_revision: Union[str, None] = "018_seed_permisos_faltantes"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# Permissions ADMIN currently lacks
PERMISOS_PARA_ADMIN = [
    ("estado_academico:ver",      "ALUMNO → solo lo tenía ALUMNO"),
    ("evaluacion:reservar",       "ALUMNO → solo lo tenía ALUMNO"),
    ("facturas:gestionar",        "FINANZAS → solo lo tenía FINANZAS"),
    ("liquidaciones:calcular_cerrar", "FINANZAS → solo lo tenía FINANZAS"),
    ("liquidaciones:operar_grilla",   "FINANZAS → solo lo tenía FINANZAS"),
]


def upgrade() -> None:
    conn = op.get_bind()
    for permiso_codigo, _nota in PERMISOS_PARA_ADMIN:
        conn.execute(
            sa.text(
                "INSERT INTO rol_permiso (id, rol_id, permiso_id) "
                "SELECT gen_random_uuid(), r.id, p.id "
                "FROM rol r, permiso p "
                "WHERE r.nombre = 'ADMIN' "
                "AND p.codigo = :permiso_codigo "
                "AND NOT EXISTS ("
                "  SELECT 1 FROM rol_permiso rp "
                "  WHERE rp.rol_id = r.id AND rp.permiso_id = p.id"
                ")"
            ).bindparams(sa.bindparam("permiso_codigo", type_=sa.String)),
            {"permiso_codigo": permiso_codigo},
        )


def downgrade() -> None:
    codigos = [p[0] for p in PERMISOS_PARA_ADMIN]
    placeholders = ", ".join(f":c{i}" for i in range(len(codigos)))
    params = {f"c{i}": c for i, c in enumerate(codigos)}
    conn = op.get_bind()

    binds = [sa.bindparam(f"c{i}", type_=sa.String) for i in range(len(codigos))]

    conn.execute(
        sa.text(
            f"DELETE FROM rol_permiso WHERE permiso_id IN "
            f"(SELECT id FROM permiso WHERE codigo IN ({placeholders})) "
            f"AND rol_id IN (SELECT id FROM rol WHERE nombre = 'ADMIN')"
        ).bindparams(*binds),
        params,
    )
