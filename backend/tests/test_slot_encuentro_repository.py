"""TDD: SlotEncuentro repository tests."""

import uuid
from datetime import date, time

import pytest

from app.models.slot_encuentro import SlotEncuentro
from app.repositories.slot_encuentro_repository import SlotEncuentroRepository
from tests.helpers_encuentros import create_asignacion_chain


async def _make_slot(db_session, tenant, asignacion_id, materia_id, **kwargs):
    defaults = dict(
        tenant_id=tenant.id,
        asignacion_id=asignacion_id,
        materia_id=materia_id,
        titulo="Clase Test",
        hora=time(14, 0),
        dia_semana="Lunes",
        fecha_inicio=date(2026, 6, 8),
        cant_semanas=4,
    )
    defaults.update(kwargs)
    slot = SlotEncuentro(**defaults)
    db_session.add(slot)
    await db_session.commit()
    await db_session.refresh(slot)
    return slot


@pytest.mark.asyncio
async def test_create_slot_returns_slot_with_id(db_session, tenant):
    a, m, _, _ = await create_asignacion_chain(db_session, tenant)
    repo = SlotEncuentroRepository(db_session, tenant.id)
    slot = SlotEncuentro(
        tenant_id=tenant.id,
        asignacion_id=a.id,
        materia_id=m.id,
        titulo="Test",
        hora=time(14, 0),
        dia_semana="Lunes",
        fecha_inicio=date(2026, 6, 8),
        cant_semanas=4,
    )
    result = await repo.create(slot)
    await db_session.commit()
    assert result.id is not None


@pytest.mark.asyncio
async def test_get_by_id_returns_slot(db_session, tenant):
    a, m, _, _ = await create_asignacion_chain(db_session, tenant)
    slot = await _make_slot(db_session, tenant, a.id, m.id)
    await db_session.commit()

    repo = SlotEncuentroRepository(db_session, tenant.id)
    found = await repo.get_by_id(slot.id, tenant.id)
    assert found is not None
    assert found.id == slot.id


@pytest.mark.asyncio
async def test_get_by_id_tenant_isolation(db_session, tenant):
    a, m, _, _ = await create_asignacion_chain(db_session, tenant)
    slot = await _make_slot(db_session, tenant, a.id, m.id)
    await db_session.commit()

    repo = SlotEncuentroRepository(db_session, tenant.id)
    found = await repo.get_by_id(slot.id, uuid.uuid4())
    assert found is None


@pytest.mark.asyncio
async def test_list_by_materia_returns_filtered(db_session, tenant):
    a, m, _, _ = await create_asignacion_chain(db_session, tenant)
    await _make_slot(db_session, tenant, a.id, m.id, titulo="S1")
    await _make_slot(db_session, tenant, a.id, m.id, titulo="S2")

    repo = SlotEncuentroRepository(db_session, tenant.id)
    items, total = await repo.list_by_materia(m.id, tenant.id)
    assert total == 2
    assert len(items) == 2


@pytest.mark.asyncio
async def test_list_by_asignacion_scope_profesor(db_session, tenant):
    a1, m1, _, _ = await create_asignacion_chain(db_session, tenant)
    a2, m2, _, _ = await create_asignacion_chain(db_session, tenant)
    await _make_slot(db_session, tenant, a1.id, m1.id, titulo="S1")
    await _make_slot(db_session, tenant, a2.id, m2.id, titulo="S2")

    repo = SlotEncuentroRepository(db_session, tenant.id)
    items = await repo.list_by_asignacion(a1.id, tenant.id)
    assert len(items) == 1


@pytest.mark.asyncio
async def test_soft_delete_sets_timestamp(db_session, tenant):
    a, m, _, _ = await create_asignacion_chain(db_session, tenant)
    slot = await _make_slot(db_session, tenant, a.id, m.id)
    await db_session.commit()

    repo = SlotEncuentroRepository(db_session, tenant.id)
    result = await repo.soft_delete(slot.id, tenant.id)
    await db_session.commit()
    assert result is True
    found = await repo.get_by_id(slot.id, tenant.id)
    assert found is None


@pytest.mark.asyncio
async def test_soft_delete_idempotent(db_session, tenant):
    a, m, _, _ = await create_asignacion_chain(db_session, tenant)
    slot = await _make_slot(db_session, tenant, a.id, m.id)
    await db_session.commit()

    repo = SlotEncuentroRepository(db_session, tenant.id)
    result1 = await repo.soft_delete(slot.id, tenant.id)
    await db_session.commit()
    result2 = await repo.soft_delete(slot.id, tenant.id)
    assert result1 is True
    assert result2 is False
