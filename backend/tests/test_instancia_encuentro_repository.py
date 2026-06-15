"""TDD: InstanciaEncuentro repository tests."""

import uuid
from datetime import date, time

import pytest

from app.models.instancia_encuentro import InstanciaEncuentro
from app.repositories.instancia_encuentro_repository import InstanciaEncuentroRepository
from tests.helpers_encuentros import create_asignacion_chain


async def _make_instancia(db_session, tenant, asignacion_id, materia_id, **kwargs):
    defaults = dict(
        tenant_id=tenant.id,
        asignacion_id=asignacion_id,
        materia_id=materia_id,
        fecha=date(2026, 6, 8),
        hora=time(14, 0),
        titulo="Clase 1",
    )
    defaults.update(kwargs)
    instancia = InstanciaEncuentro(**defaults)
    db_session.add(instancia)
    await db_session.commit()
    await db_session.refresh(instancia)
    return instancia


@pytest.mark.asyncio
async def test_create_instancia_returns_instancia_with_id(db_session, tenant):
    a, m, _, _ = await create_asignacion_chain(db_session, tenant)
    repo = InstanciaEncuentroRepository(db_session, tenant.id)
    instancia = InstanciaEncuentro(
        tenant_id=tenant.id, materia_id=m.id, asignacion_id=a.id,
        fecha=date(2026, 6, 8), hora=time(14, 0), titulo="Test",
    )
    await repo.create(instancia)
    await db_session.commit()
    assert instancia.id is not None


@pytest.mark.asyncio
async def test_bulk_create_creates_all(db_session, tenant):
    a, m, _, _ = await create_asignacion_chain(db_session, tenant)
    repo = InstanciaEncuentroRepository(db_session, tenant.id)
    instancias = [
        InstanciaEncuentro(
            tenant_id=tenant.id, materia_id=m.id, asignacion_id=a.id,
            fecha=date(2026, 6, 8 + i), hora=time(14, 0), titulo=f"C{i}",
        )
        for i in range(3)
    ]
    result = await repo.bulk_create(instancias)
    await db_session.commit()
    assert len(result) == 3


@pytest.mark.asyncio
async def test_update_partial_fields(db_session, tenant):
    a, m, _, _ = await create_asignacion_chain(db_session, tenant)
    instancia = await _make_instancia(db_session, tenant, a.id, m.id)
    await db_session.commit()

    repo = InstanciaEncuentroRepository(db_session, tenant.id)
    updated = await repo.update(
        instancia.id, tenant.id,
        estado="Realizado", video_url="https://v.test/1",
    )
    await db_session.commit()
    assert updated.estado == "Realizado"


@pytest.mark.asyncio
async def test_list_by_estado_filter(db_session, tenant):
    a, m, _, _ = await create_asignacion_chain(db_session, tenant)
    await _make_instancia(db_session, tenant, a.id, m.id, titulo="I1", estado="Programado")
    await _make_instancia(db_session, tenant, a.id, m.id, titulo="I2", estado="Realizado")

    repo = InstanciaEncuentroRepository(db_session, tenant.id)
    items, total = await repo.list_by_filters(tenant.id, estado="Programado")
    assert total >= 1
    assert any(i.titulo == "I1" for i in items)


@pytest.mark.asyncio
async def test_list_by_slot_returns_sorted(db_session, tenant):
    a, m, _, _ = await create_asignacion_chain(db_session, tenant)
    from app.models.slot_encuentro import SlotEncuentro
    from datetime import date as dt_date, time as dt_time
    slot = SlotEncuentro(
        tenant_id=tenant.id, asignacion_id=a.id, materia_id=m.id,
        titulo="Slot", hora=dt_time(14, 0),
    )
    db_session.add(slot)
    await db_session.flush()

    await _make_instancia(db_session, tenant, a.id, m.id, slot_id=slot.id,
                          fecha=dt_date(2026, 6, 15), titulo="Later")
    await _make_instancia(db_session, tenant, a.id, m.id, slot_id=slot.id,
                          fecha=dt_date(2026, 6, 8), titulo="Earlier")

    repo = InstanciaEncuentroRepository(db_session, tenant.id)
    items = await repo.list_by_slot(slot.id, tenant.id)
    assert len(items) >= 2
    assert items[0].fecha <= items[1].fecha


@pytest.mark.asyncio
async def test_tenant_isolation(db_session, tenant):
    a, m, _, _ = await create_asignacion_chain(db_session, tenant)
    instancia = await _make_instancia(db_session, tenant, a.id, m.id)
    await db_session.commit()

    repo = InstanciaEncuentroRepository(db_session, tenant.id)
    found = await repo.get_by_id(instancia.id, uuid.uuid4())
    assert found is None
