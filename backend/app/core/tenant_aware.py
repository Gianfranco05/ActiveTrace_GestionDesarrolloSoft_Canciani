"""Tenant-aware ORM helpers — enforce row-level tenant isolation."""
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession


async def get_tenant_scoped(session: AsyncSession, model, id_value: uuid.UUID, tenant_id: uuid.UUID):
    """Fetch a tenant-scoped entity by ID, enforcing tenant isolation.

    Equivalent to session.get(Model, id) but guarantees tenant_id matches.
    Returns None if not found or if tenant_id doesn't match.
    """
    stmt = select(model).where(
        model.id == id_value,
        model.tenant_id == tenant_id,
    )
    result = await session.execute(stmt)
    return result.scalar_one_or_none()
