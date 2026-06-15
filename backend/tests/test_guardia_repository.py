"""TDD: Guardia repository tests."""

import uuid

import pytest

from app.models.guardia import Guardia
from app.repositories.guardia_repository import GuardiaRepository
from tests.helpers_encuentros import create_asignacion_chain


async def _make_guardia(db_session, tenant, asignacion_id, materia_id, carrera_id, cohorte_id, **kwargs):
    defaults = dict(
        tenant_id=tenant.id,
        asignacion_id=asignacion_id,
        materia_id=materia_id,
        carrera_id=carrera_id,
        cohorte_id=cohorte_id,
        dia="Lunes",
        horario="14:00–14:45",
    )
    defaults.update(kwargs)
    g = Guardia(**defaults)
    db_session.add(g)
    await db_session.commit()
    await db_session.refresh(g)
    return g


@pytest.mark.asyncio
async def test_create_guardia_returns_guardia_with_id(db_session, tenant):
    a, m, c, coh = await create_asignacion_chain(db_session, tenant)
    repo = GuardiaRepository(db_session, tenant.id)
    g = Guardia(
        tenant_id=tenant.id, asignacion_id=a.id, materia_id=m.id,
        carrera_id=c.id, cohorte_id=coh.id, dia="Lunes", horario="14:00–14:45",
    )
    await repo.create(g)
    await db_session.commit()
    assert g.id is not None


@pytest.mark.asyncio
async def test_update_partial(db_session, tenant):
    a, m, c, coh = await create_asignacion_chain(db_session, tenant)
    g = await _make_guardia(db_session, tenant, a.id, m.id, c.id, coh.id)
    await db_session.commit()

    repo = GuardiaRepository(db_session, tenant.id)
    updated = await repo.update(g.id, tenant.id, estado="Realizada")
    await db_session.commit()
    assert updated.estado == "Realizada"


@pytest.mark.asyncio
async def test_list_filtered_by_materia(db_session, tenant):
    a1, m1, c1, coh1 = await create_asignacion_chain(db_session, tenant)
    a2, m2, c2, coh2 = await create_asignacion_chain(db_session, tenant)
    await _make_guardia(db_session, tenant, a1.id, m1.id, c1.id, coh1.id, dia="Lunes")
    await _make_guardia(db_session, tenant, a2.id, m2.id, c2.id, coh2.id, dia="Martes")

    repo = GuardiaRepository(db_session, tenant.id)
    items, total = await repo.list_by_filters(tenant.id, materia_id=m1.id)
    assert total == 1


@pytest.mark.asyncio
async def test_list_filtered_by_estado(db_session, tenant):
    a, m, c, coh = await create_asignacion_chain(db_session, tenant)
    await _make_guardia(db_session, tenant, a.id, m.id, c.id, coh.id, estado="Pendiente")
    await _make_guardia(db_session, tenant, a.id, m.id, c.id, coh.id, estado="Realizada")

    repo = GuardiaRepository(db_session, tenant.id)
    items, total = await repo.list_by_filters(tenant.id, estado="Pendiente")
    assert total == 1


@pytest.mark.asyncio
async def test_list_filtered_by_dia(db_session, tenant):
    a, m, c, coh = await create_asignacion_chain(db_session, tenant)
    await _make_guardia(db_session, tenant, a.id, m.id, c.id, coh.id, dia="Lunes")
    await _make_guardia(db_session, tenant, a.id, m.id, c.id, coh.id, dia="Martes")

    repo = GuardiaRepository(db_session, tenant.id)
    items, total = await repo.list_by_filters(tenant.id, dia="Martes")
    assert total == 1


@pytest.mark.asyncio
async def test_list_for_export_returns_all_matching(db_session, tenant):
    a, m, c, coh = await create_asignacion_chain(db_session, tenant)
    await _make_guardia(db_session, tenant, a.id, m.id, c.id, coh.id, dia="Lunes")
    await _make_guardia(db_session, tenant, a.id, m.id, c.id, coh.id, dia="Martes")

    repo = GuardiaRepository(db_session, tenant.id)
    items = await repo.list_for_export(tenant.id)
    assert len(items) == 2


@pytest.mark.asyncio
async def test_tutor_scope_only_own(db_session, tenant):
    a1, m1, c1, coh1 = await create_asignacion_chain(db_session, tenant)
    a2, m2, c2, coh2 = await create_asignacion_chain(db_session, tenant)
    await _make_guardia(db_session, tenant, a1.id, m1.id, c1.id, coh1.id, dia="Lunes")
    await _make_guardia(db_session, tenant, a2.id, m2.id, c2.id, coh2.id, dia="Martes")

    repo = GuardiaRepository(db_session, tenant.id)
    items, total = await repo.list_by_filters(tenant.id, asignacion_id=a1.id)
    assert total == 1
