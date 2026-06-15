import pytest
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from tests.conftest import SampleEntity


@pytest.mark.asyncio
async def test_db_connection_smoke(db_session: AsyncSession):
    result = await db_session.execute(text("SELECT 1"))
    value = result.scalar_one()
    assert value == 1


@pytest.mark.asyncio
async def test_session_recovers_after_error(db_session: AsyncSession, tenant):
    entity = SampleEntity(name="will-fail")
    db_session.add(entity)
    with pytest.raises(IntegrityError):
        await db_session.commit()
    await db_session.rollback()

    entity_ok = SampleEntity(name="after-error", tenant_id=tenant.id)
    db_session.add(entity_ok)
    await db_session.commit()

    assert entity_ok.id is not None
