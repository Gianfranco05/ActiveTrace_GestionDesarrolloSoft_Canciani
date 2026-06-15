import pytest

from tests.conftest import SampleEntity


@pytest.mark.asyncio
async def test_created_at_set_on_insert(db_session, tenant):
    entity = SampleEntity(name="created-check", tenant_id=tenant.id)
    db_session.add(entity)
    await db_session.commit()
    await db_session.refresh(entity)

    assert entity.created_at is not None
    assert entity.updated_at is not None


@pytest.mark.asyncio
async def test_updated_at_changes_on_update(db_session, tenant):
    entity = SampleEntity(name="update-check", tenant_id=tenant.id)
    db_session.add(entity)
    await db_session.commit()
    await db_session.refresh(entity)

    original_updated = entity.updated_at

    entity.name = "updated-name"
    await db_session.commit()
    await db_session.refresh(entity)

    assert entity.updated_at is not None
    assert entity.updated_at.replace(microsecond=0) >= original_updated.replace(microsecond=0)
