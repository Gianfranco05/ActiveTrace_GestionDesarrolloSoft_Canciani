import pytest

from app.repositories.base import BaseRepository
from tests.conftest import SampleEntity


@pytest.mark.asyncio
async def test_multi_tenant_get_isolation(db_session, tenant_a, tenant_b):
    repo_a = BaseRepository(db_session, tenant_a.id, SampleEntity)
    repo_b = BaseRepository(db_session, tenant_b.id, SampleEntity)

    entity_a = await repo_a.create({"name": "a-only"})
    entity_b = await repo_b.create({"name": "b-only"})

    assert await repo_a.get(entity_b.id) is None
    assert await repo_b.get(entity_a.id) is None


@pytest.mark.asyncio
async def test_multi_tenant_list_isolation(db_session, tenant_a, tenant_b):
    repo_a = BaseRepository(db_session, tenant_a.id, SampleEntity)
    repo_b = BaseRepository(db_session, tenant_b.id, SampleEntity)

    await repo_a.create({"name": "a-data"})
    await repo_b.create({"name": "b-data"})

    a_results = await repo_a.list()
    b_results = await repo_b.list()

    assert all(r.name == "a-data" for r in a_results)
    assert all(r.name == "b-data" for r in b_results)
    assert len(a_results) == 1
    assert len(b_results) == 1


@pytest.mark.asyncio
async def test_multi_tenant_update_scope(db_session, tenant_a, tenant_b):
    repo_a = BaseRepository(db_session, tenant_a.id, SampleEntity)
    repo_b = BaseRepository(db_session, tenant_b.id, SampleEntity)

    entity_a = await repo_a.create({"name": "original-a"})

    updated_by_b = await repo_b.update(entity_a.id, {"name": "hacked-by-b"})
    assert updated_by_b is None

    still_a = await repo_a.get(entity_a.id)
    assert still_a is not None
    assert still_a.name == "original-a"
