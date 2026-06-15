"""add grupo_plus column to materia table

Revision ID: 020
Revises: 019_admin_permisos_faltantes
Create Date: 2026-06-08

Adds a nullable grupo_plus column to materia and copies existing data
from the grupo_materia join table for backward-compatible migration.
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "020_materia_grupo_plus"
down_revision: Union[str, None] = "019_admin_permisos_faltantes"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "materia",
        sa.Column("grupo_plus", sa.String(50), nullable=True),
    )

    op.execute(
        sa.text(
            "UPDATE materia SET grupo_plus = gm.grupo "
            "FROM grupo_materia gm "
            "WHERE gm.materia_id = materia.id "
            "AND gm.deleted_at IS NULL "
            "AND materia.deleted_at IS NULL"
        )
    )


def downgrade() -> None:
    op.drop_column("materia", "grupo_plus")
