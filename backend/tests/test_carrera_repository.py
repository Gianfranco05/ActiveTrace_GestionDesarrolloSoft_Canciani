import uuid

import pytest

from app.repositories.carrera_repository import CarreraRepository


@pytest.mark.asyncio
async def test_create_carrera(db_session, tenant):
    repo = CarreraRepository(db_session, tenant.id)
    carrera = await repo.create({"codigo": "PROG-2025", "nombre": "Programación 2025"})

    assert isinstance(carrera.id, uuid.UUID)
    assert carrera.tenant_id == tenant.id
    assert carrera.codigo == "PROG-2025"
    assert carrera.nombre == "Programación 2025"
    assert carrera.estado == "Activa"


@pytest.mark.asyncio
async def test_get_by_codigo_found(db_session, tenant):
    repo = CarreraRepository(db_session, tenant.id)
    await repo.create({"codigo": "MATE", "nombre": "Matemática"})

    found = await repo.get_by_codigo("MATE")
    assert found is not None
    assert found.codigo == "MATE"
    assert found.nombre == "Matemática"


@pytest.mark.asyncio
async def test_get_by_codigo_not_found(db_session, tenant):
    repo = CarreraRepository(db_session, tenant.id)
    found = await repo.get_by_codigo("NO_EXISTE")
    assert found is None


@pytest.mark.asyncio
async def test_list_excludes_soft_deleted(db_session, tenant):
    repo = CarreraRepository(db_session, tenant.id)
    c1 = await repo.create({"codigo": "KEEP", "nombre": "Keep"})
    await repo.create({"codigo": "DELETE", "nombre": "Delete Me"})

    assert len(await repo.list()) == 2

    await repo.soft_delete(c1.id)
    remaining = await repo.list()
    assert len(remaining) == 1
    assert remaining[0].codigo == "DELETE"


@pytest.mark.asyncio
async def test_tenant_isolation(db_session, tenant_a, tenant_b):
    repo_a = CarreraRepository(db_session, tenant_a.id)
    repo_b = CarreraRepository(db_session, tenant_b.id)

    await repo_a.create({"codigo": "A-001", "nombre": "Carrera A"})
    await repo_b.create({"codigo": "B-001", "nombre": "Carrera B"})

    results_a = await repo_a.list()
    assert len(results_a) == 1
    assert results_a[0].codigo == "A-001"

    results_b = await repo_b.list()
    assert len(results_b) == 1
    assert results_b[0].codigo == "B-001"
