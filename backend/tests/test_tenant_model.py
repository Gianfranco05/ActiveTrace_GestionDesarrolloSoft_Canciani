import uuid

import pytest
from sqlalchemy.exc import IntegrityError

from app.models.tenant import Tenant



@pytest.mark.asyncio
async def test_create_tenant(db_session):
    tenant = Tenant(name="Test Inc.", slug="test-inc")
    db_session.add(tenant)
    await db_session.commit()
    await db_session.refresh(tenant)

    assert isinstance(tenant.id, uuid.UUID)
    assert tenant.name == "Test Inc."
    assert tenant.slug == "test-inc"
    assert tenant.is_active is True


@pytest.mark.asyncio
async def test_tenant_slug_uniqueness(db_session):
    t1 = Tenant(name="First", slug="same-slug")
    db_session.add(t1)
    await db_session.commit()

    t2 = Tenant(name="Second", slug="same-slug")
    db_session.add(t2)
    with pytest.raises(IntegrityError):
        await db_session.commit()
    await db_session.rollback()


@pytest.mark.asyncio
async def test_tenant_name_uniqueness(db_session):
    t1 = Tenant(name="Unique Name", slug="unique-slug-1")
    db_session.add(t1)
    await db_session.commit()

    t2 = Tenant(name="Unique Name", slug="unique-slug-2")
    db_session.add(t2)
    with pytest.raises(IntegrityError):
        await db_session.commit()
    await db_session.rollback()
