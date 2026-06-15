import pytest

from app.repositories.base import BaseRepository
from tests.conftest import SampleEntity


@pytest.mark.asyncio
async def test_repo_scope_list(db_session, tenant_a, tenant_b):
    repo_a = BaseRepository(db_session, tenant_a.id, SampleEntity)

    e1 = SampleEntity(name="a-1", tenant_id=tenant_a.id)
    db_session.add(e1)
    await db_session.commit()

    e2 = SampleEntity(name="a-2", tenant_id=tenant_a.id)
    db_session.add(e2)
    await db_session.commit()

    results = await repo_a.list()
    assert len(results) == 2
    names = {r.name for r in results}
    assert names == {"a-1", "a-2"}


@pytest.mark.asyncio
async def test_repo_create_sets_tenant_id(db_session, tenant_a):
    repo = BaseRepository(db_session, tenant_a.id, SampleEntity)

    entity = await repo.create({"name": "created-via-repo"})

    assert entity.tenant_id == tenant_a.id
    assert entity.name == "created-via-repo"


@pytest.mark.asyncio
async def test_repo_get_filters_tenant(db_session, tenant_a, tenant_b):
    repo_a = BaseRepository(db_session, tenant_a.id, SampleEntity)
    repo_b = BaseRepository(db_session, tenant_b.id, SampleEntity)

    entity = SampleEntity(name="tenant-a-data", tenant_id=tenant_a.id)
    db_session.add(entity)
    await db_session.commit()

    found = await repo_a.get(entity.id)
    assert found is not None
    assert found.name == "tenant-a-data"

    not_found = await repo_b.get(entity.id)
    assert not_found is None


@pytest.mark.asyncio
async def test_repo_update_scoped(db_session, tenant_a):
    repo = BaseRepository(db_session, tenant_a.id, SampleEntity)

    entity = await repo.create({"name": "original"})

    updated = await repo.update(entity.id, {"name": "updated"})
    assert updated is not None
    assert updated.name == "updated"

    fetched = await repo.get(entity.id)
    assert fetched is not None
    assert fetched.name == "updated"


@pytest.mark.asyncio
async def test_repo_soft_delete_excludes(db_session, tenant_a):
    repo = BaseRepository(db_session, tenant_a.id, SampleEntity)

    e1 = await repo.create({"name": "keep"})
    e2 = await repo.create({"name": "delete-me"})

    assert len(await repo.list()) == 2

    deleted = await repo.soft_delete(e2.id)
    assert deleted is True

    remaining = await repo.list()
    assert len(remaining) == 1
    assert remaining[0].name == "keep"


@pytest.mark.asyncio
async def test_repo_with_deleted_includes(db_session, tenant_a):
    repo = BaseRepository(db_session, tenant_a.id, SampleEntity)

    entity = await repo.create({"name": "will-delete"})
    await repo.soft_delete(entity.id)

    normal = await repo.list()
    assert len(normal) == 0

    with_deleted = await repo.with_deleted().list()
    assert len(with_deleted) == 1
    assert with_deleted[0].name == "will-delete"


@pytest.mark.asyncio
async def test_repo_only_deleted_returns_deleted(db_session, tenant_a):
    repo = BaseRepository(db_session, tenant_a.id, SampleEntity)

    active = await repo.create({"name": "active"})
    deleted_entity = await repo.create({"name": "deleted"})
    await repo.soft_delete(deleted_entity.id)

    only_deleted = await repo.only_deleted().list()
    assert len(only_deleted) == 1
    assert only_deleted[0].id == deleted_entity.id

    active_result = await repo.get(active.id)
    assert active_result is not None


@pytest.mark.asyncio
async def test_repo_cross_tenant_isolation(db_session, tenant_a, tenant_b):
    repo_a = BaseRepository(db_session, tenant_a.id, SampleEntity)
    repo_b = BaseRepository(db_session, tenant_b.id, SampleEntity)

    await repo_a.create({"name": "a-data"})
    await repo_b.create({"name": "b-data"})

    results_a = await repo_a.list()
    assert len(results_a) == 1
    assert results_a[0].name == "a-data"

    results_b = await repo_b.list()
    assert len(results_b) == 1
    assert results_b[0].name == "b-data"
