import uuid

import pytest
from sqlalchemy.exc import IntegrityError

from tests.conftest import SampleEntity


@pytest.mark.asyncio
async def test_mixin_has_uuid(db_session, tenant):
    entity = SampleEntity(name="test", tenant_id=tenant.id)
    db_session.add(entity)
    await db_session.commit()
    await db_session.refresh(entity)

    assert isinstance(entity.id, uuid.UUID)


@pytest.mark.asyncio
async def test_mixin_tenant_id_required(db_session):
    entity = SampleEntity(name="no-tenant")
    db_session.add(entity)
    with pytest.raises(IntegrityError):
        await db_session.commit()
    await db_session.rollback()


@pytest.mark.asyncio
async def test_mixin_timestamps_auto_populate(db_session, tenant):
    entity = SampleEntity(name="timestamps", tenant_id=tenant.id)
    db_session.add(entity)
    await db_session.commit()
    await db_session.refresh(entity)

    assert entity.created_at is not None
    assert entity.updated_at is not None


@pytest.mark.asyncio
async def test_mixin_deleted_at_null_by_default(db_session, tenant):
    entity = SampleEntity(name="no-delete", tenant_id=tenant.id)
    db_session.add(entity)
    await db_session.commit()
    await db_session.refresh(entity)

    assert entity.deleted_at is None


@pytest.mark.asyncio
async def test_mixin_soft_delete_marks_timestamp(db_session, tenant):
    entity = SampleEntity(name="to-delete", tenant_id=tenant.id)
    db_session.add(entity)
    await db_session.commit()

    entity.deleted_at = None  # reset for fresh result

    from datetime import datetime, timezone

    now = datetime.now(timezone.utc)
    entity.deleted_at = now
    await db_session.commit()
    await db_session.refresh(entity)

    assert entity.deleted_at is not None
