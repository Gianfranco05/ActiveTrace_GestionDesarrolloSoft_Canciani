"""add materia_carrera join table

Revision ID: 021
Revises: 020_materia_grupo_plus
Create Date: 2026-06-09
"""
from typing import Sequence, Union
import uuid

import sqlalchemy as sa
from alembic import op

revision: str = "021_materia_carrera"
down_revision: Union[str, None] = "020_materia_grupo_plus"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "materia_carrera",
        sa.Column("id", sa.Uuid(), primary_key=True, default=uuid.uuid4),
        sa.Column("tenant_id", sa.Uuid(), sa.ForeignKey("tenant.id", ondelete="CASCADE"), nullable=False),
        sa.Column("materia_id", sa.Uuid(), sa.ForeignKey("materia.id", ondelete="CASCADE"), nullable=False),
        sa.Column("carrera_id", sa.Uuid(), sa.ForeignKey("carrera.id", ondelete="CASCADE"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.UniqueConstraint("materia_id", "carrera_id", name="uq_materia_carrera"),
    )


def downgrade() -> None:
    op.drop_table("materia_carrera")
