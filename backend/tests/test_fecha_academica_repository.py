import uuid
from datetime import date

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.carrera import Carrera
from app.models.cohorte import Cohorte
from app.models.materia import Materia


async def _seed_fa_estructura(db_session: AsyncSession, tenant_id: uuid.UUID):
    suffix = uuid.uuid4().hex[:8]
    c = Carrera(id=uuid.uuid4(), codigo=f"FA-{suffix}", nombre="Test Carrera", tenant_id=tenant_id)
    db_session.add(c)
    m = Materia(id=uuid.uuid4(), codigo=f"MAT-FA-{suffix}", nombre="Materia FA", tenant_id=tenant_id)
    db_session.add(m)
    co = Cohorte(
        id=uuid.uuid4(), carrera_id=c.id, nombre=f"COH-FA-{suffix}",
        anio=2026, vig_desde=date(2026, 1, 1), tenant_id=tenant_id,
    )
    db_session.add(co)
    await db_session.commit()
    return c.id, m.id, co.id


@pytest.mark.asyncio
async def test_create_fecha(db_session: AsyncSession, tenant):
    from app.repositories.fecha_academica_repository import FechaAcademicaRepository

    carrera_id, materia_id, cohorte_id = await _seed_fa_estructura(db_session, tenant.id)
    repo = FechaAcademicaRepository(db_session, tenant.id)

    result = await repo.create({
        "materia_id": materia_id,
        "cohorte_id": cohorte_id,
        "tipo": "Parcial",
        "numero": 1,
        "periodo": "2026-1",
        "fecha": date(2026, 4, 15),
        "titulo": "Primer Parcial",
    })

    assert result is not None
    assert result.id is not None
    assert result.tenant_id == tenant.id
    assert result.materia_id == materia_id
    assert result.cohorte_id == cohorte_id
    assert result.tipo == "Parcial"
    assert result.numero == 1
    assert result.periodo == "2026-1"
    assert result.fecha == date(2026, 4, 15)
    assert result.titulo == "Primer Parcial"


@pytest.mark.asyncio
async def test_get_by_id_returns_fecha(db_session: AsyncSession, tenant):
    from app.repositories.fecha_academica_repository import FechaAcademicaRepository

    carrera_id, materia_id, cohorte_id = await _seed_fa_estructura(db_session, tenant.id)
    repo = FechaAcademicaRepository(db_session, tenant.id)

    created = await repo.create({
        "materia_id": materia_id, "cohorte_id": cohorte_id,
        "tipo": "TP", "numero": 2, "periodo": "2026-1",
        "fecha": date(2026, 5, 10), "titulo": "TP Integrador",
    })

    found = await repo.get_by_id(created.id, tenant.id)
    assert found is not None
    assert found.tipo == "TP"
    assert found.numero == 2


@pytest.mark.asyncio
async def test_list_by_filters_tipo(db_session: AsyncSession, tenant):
    from app.repositories.fecha_academica_repository import FechaAcademicaRepository

    carrera_id, materia_id, cohorte_id = await _seed_fa_estructura(db_session, tenant.id)
    repo = FechaAcademicaRepository(db_session, tenant.id)

    await repo.create({
        "materia_id": materia_id, "cohorte_id": cohorte_id,
        "tipo": "Parcial", "numero": 1, "periodo": "2026-1",
        "fecha": date(2026, 4, 15), "titulo": "Parcial 1",
    })
    await repo.create({
        "materia_id": materia_id, "cohorte_id": cohorte_id,
        "tipo": "Coloquio", "numero": 1, "periodo": "2026-1",
        "fecha": date(2026, 6, 20), "titulo": "Coloquio 1",
    })

    items, total = await repo.list_by_filters(tenant.id, tipo="Parcial")
    assert total == 1
    assert items[0].tipo == "Parcial"


@pytest.mark.asyncio
async def test_list_by_filters_periodo(db_session: AsyncSession, tenant):
    from app.repositories.fecha_academica_repository import FechaAcademicaRepository

    carrera_id, materia_id, cohorte_id = await _seed_fa_estructura(db_session, tenant.id)
    repo = FechaAcademicaRepository(db_session, tenant.id)

    await repo.create({
        "materia_id": materia_id, "cohorte_id": cohorte_id,
        "tipo": "Parcial", "numero": 1, "periodo": "2026-1",
        "fecha": date(2026, 4, 15), "titulo": "P1",
    })
    await repo.create({
        "materia_id": materia_id, "cohorte_id": cohorte_id,
        "tipo": "Parcial", "numero": 1, "periodo": "2026-2",
        "fecha": date(2026, 9, 15), "titulo": "P1 Q2",
    })

    items, total = await repo.list_by_filters(tenant.id, periodo="2026-1")
    assert total == 1
    assert items[0].periodo == "2026-1"


@pytest.mark.asyncio
async def test_list_combined_filters(db_session: AsyncSession, tenant):
    from app.repositories.fecha_academica_repository import FechaAcademicaRepository

    carrera_id, materia_id, cohorte_id = await _seed_fa_estructura(db_session, tenant.id)
    repo = FechaAcademicaRepository(db_session, tenant.id)

    await repo.create({
        "materia_id": materia_id, "cohorte_id": cohorte_id,
        "tipo": "Parcial", "numero": 1, "periodo": "2026-1",
        "fecha": date(2026, 4, 15), "titulo": "P1",
    })
    await repo.create({
        "materia_id": materia_id, "cohorte_id": cohorte_id,
        "tipo": "Coloquio", "numero": 1, "periodo": "2026-2",
        "fecha": date(2026, 9, 15), "titulo": "Col",
    })

    items, total = await repo.list_by_filters(
        tenant.id, materia_id=materia_id, tipo="Parcial", periodo="2026-1",
    )
    assert total == 1
    assert items[0].tipo == "Parcial"


@pytest.mark.asyncio
async def test_calendario_date_range(db_session: AsyncSession, tenant):
    from app.repositories.fecha_academica_repository import FechaAcademicaRepository

    carrera_id, materia_id, cohorte_id = await _seed_fa_estructura(db_session, tenant.id)
    repo = FechaAcademicaRepository(db_session, tenant.id)

    await repo.create({
        "materia_id": materia_id, "cohorte_id": cohorte_id,
        "tipo": "Parcial", "numero": 1, "periodo": "2026-1",
        "fecha": date(2026, 4, 15), "titulo": "Parcial 1",
    })
    await repo.create({
        "materia_id": materia_id, "cohorte_id": cohorte_id,
        "tipo": "Parcial", "numero": 2, "periodo": "2026-1",
        "fecha": date(2026, 5, 20), "titulo": "Parcial 2",
    })
    await repo.create({
        "materia_id": materia_id, "cohorte_id": cohorte_id,
        "tipo": "Coloquio", "numero": 1, "periodo": "2026-1",
        "fecha": date(2026, 6, 30), "titulo": "Coloquio",
    })

    items = await repo.get_calendario(
        tenant.id, fecha_desde=date(2026, 5, 1), fecha_hasta=date(2026, 6, 30),
    )
    assert len(items) == 2
    assert items[0].fecha == date(2026, 5, 20)
    assert items[1].fecha == date(2026, 6, 30)


@pytest.mark.asyncio
async def test_calendario_empty(db_session: AsyncSession, tenant):
    from app.repositories.fecha_academica_repository import FechaAcademicaRepository

    carrera_id, materia_id, cohorte_id = await _seed_fa_estructura(db_session, tenant.id)
    repo = FechaAcademicaRepository(db_session, tenant.id)

    items = await repo.get_calendario(tenant.id)
    assert items == []


@pytest.mark.asyncio
async def test_calendario_ordered_by_fecha(db_session: AsyncSession, tenant):
    from app.repositories.fecha_academica_repository import FechaAcademicaRepository

    carrera_id, materia_id, cohorte_id = await _seed_fa_estructura(db_session, tenant.id)
    repo = FechaAcademicaRepository(db_session, tenant.id)

    await repo.create({
        "materia_id": materia_id, "cohorte_id": cohorte_id,
        "tipo": "Coloquio", "numero": 1, "periodo": "2026-1",
        "fecha": date(2026, 6, 30), "titulo": "Coloquio",
    })
    await repo.create({
        "materia_id": materia_id, "cohorte_id": cohorte_id,
        "tipo": "Parcial", "numero": 1, "periodo": "2026-1",
        "fecha": date(2026, 4, 15), "titulo": "Parcial 1",
    })
    await repo.create({
        "materia_id": materia_id, "cohorte_id": cohorte_id,
        "tipo": "Parcial", "numero": 2, "periodo": "2026-1",
        "fecha": date(2026, 5, 20), "titulo": "Parcial 2",
    })

    items = await repo.get_calendario(tenant.id)
    assert len(items) == 3
    assert items[0].fecha == date(2026, 4, 15)
    assert items[1].fecha == date(2026, 5, 20)
    assert items[2].fecha == date(2026, 6, 30)


@pytest.mark.asyncio
async def test_update_partial(db_session: AsyncSession, tenant):
    from app.repositories.fecha_academica_repository import FechaAcademicaRepository

    carrera_id, materia_id, cohorte_id = await _seed_fa_estructura(db_session, tenant.id)
    repo = FechaAcademicaRepository(db_session, tenant.id)

    created = await repo.create({
        "materia_id": materia_id, "cohorte_id": cohorte_id,
        "tipo": "Parcial", "numero": 1, "periodo": "2026-1",
        "fecha": date(2026, 4, 15), "titulo": "Original",
    })

    updated = await repo.update(created.id, tenant.id, titulo="Actualizado", fecha=date(2026, 4, 20))
    assert updated is not None
    assert updated.titulo == "Actualizado"
    assert updated.fecha == date(2026, 4, 20)
    assert updated.tipo == "Parcial"
    assert updated.numero == 1


@pytest.mark.asyncio
async def test_tenant_isolation_fa(db_session: AsyncSession, tenant, tenant_b):
    from app.repositories.fecha_academica_repository import FechaAcademicaRepository

    carrera_id_b, materia_id_b, cohorte_id_b = await _seed_fa_estructura(db_session, tenant_b.id)
    repo_b = FechaAcademicaRepository(db_session, tenant_b.id)
    await repo_b.create({
        "materia_id": materia_id_b, "cohorte_id": cohorte_id_b,
        "tipo": "Parcial", "numero": 1, "periodo": "2026-1",
        "fecha": date(2026, 4, 15), "titulo": "Tenant B",
    })

    repo_a = FechaAcademicaRepository(db_session, tenant.id)
    items, total = await repo_a.list_by_filters(tenant.id)
    assert total == 0


@pytest.mark.asyncio
async def test_soft_delete_excluded(db_session: AsyncSession, tenant):
    from app.repositories.fecha_academica_repository import FechaAcademicaRepository

    carrera_id, materia_id, cohorte_id = await _seed_fa_estructura(db_session, tenant.id)
    repo = FechaAcademicaRepository(db_session, tenant.id)

    f1 = await repo.create({
        "materia_id": materia_id, "cohorte_id": cohorte_id,
        "tipo": "Parcial", "numero": 1, "periodo": "2026-1",
        "fecha": date(2026, 4, 15), "titulo": "Keep",
    })
    await repo.create({
        "materia_id": materia_id, "cohorte_id": cohorte_id,
        "tipo": "TP", "numero": 1, "periodo": "2026-1",
        "fecha": date(2026, 5, 10), "titulo": "Delete",
    })

    items, total = await repo.list_by_filters(tenant.id)
    assert total == 2

    await repo.soft_delete(f1.id, tenant.id)
    items2, total2 = await repo.list_by_filters(tenant.id)
    assert total2 == 1
