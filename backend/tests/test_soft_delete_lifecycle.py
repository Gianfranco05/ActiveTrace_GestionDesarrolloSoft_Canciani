import pytest

from app.repositories.base import BaseRepository
from tests.conftest import SampleEntity


@pytest.mark.asyncio
async def test_soft_delete_lifecycle(db_session, tenant_a):
    repo = BaseRepository(db_session, tenant_a.id, SampleEntity)

    entity = await repo.create({"name": "lifecycle-test"})
    entity_id = entity.id

    list_before = await repo.list()
    assert len(list_before) == 1

    deleted = await repo.soft_delete(entity_id)
    assert deleted is True

    list_after = await repo.list()
    assert len(list_after) == 0

    get_after = await repo.get(entity_id)
    assert get_after is None

    with_deleted_list = await repo.with_deleted().list()
    assert len(with_deleted_list) == 1
    assert with_deleted_list[0].deleted_at is not None

    with_deleted_get = await repo.with_deleted().get(entity_id)
    assert with_deleted_get is not None
    assert with_deleted_get.deleted_at is not None

    only_list = await repo.only_deleted().list()
    assert len(only_list) == 1
    assert only_list[0].id == entity_id


@pytest.mark.asyncio
async def test_soft_delete_active_only(db_session, tenant_a, tenant_b):
    repo_a = BaseRepository(db_session, tenant_a.id, SampleEntity)
    repo_b = BaseRepository(db_session, tenant_b.id, SampleEntity)

    entity_a = await repo_a.create({"name": "a-data"})
    entity_b = await repo_b.create({"name": "b-data"})

    await repo_a.soft_delete(entity_a.id)

    b_list = await repo_b.list()
    assert len(b_list) == 1
    assert b_list[0].name == "b-data"

    a_deleted_list = await repo_a.only_deleted().list()
    assert len(a_deleted_list) == 1
    assert a_deleted_list[0].name == "a-data"
