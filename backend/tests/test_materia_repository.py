import uuid

import pytest

from app.repositories.materia_repository import MateriaRepository


@pytest.mark.asyncio
async def test_create_materia(db_session, tenant):
    repo = MateriaRepository(db_session, tenant.id)
    materia = await repo.create({"codigo": "MATE_I", "nombre": "Matemática I"})

    assert isinstance(materia.id, uuid.UUID)
    assert materia.tenant_id == tenant.id
    assert materia.codigo == "MATE_I"
    assert materia.nombre == "Matemática I"
    assert materia.estado == "Activa"


@pytest.mark.asyncio
async def test_get_by_codigo_found(db_session, tenant):
    repo = MateriaRepository(db_session, tenant.id)
    await repo.create({"codigo": "FISICA", "nombre": "Física"})

    found = await repo.get_by_codigo("FISICA")
    assert found is not None
    assert found.codigo == "FISICA"


@pytest.mark.asyncio
async def test_get_by_codigo_not_found(db_session, tenant):
    repo = MateriaRepository(db_session, tenant.id)
    found = await repo.get_by_codigo("NO_EXISTE")
    assert found is None


@pytest.mark.asyncio
async def test_list_excludes_soft_deleted(db_session, tenant):
    repo = MateriaRepository(db_session, tenant.id)
    m1 = await repo.create({"codigo": "KEEP", "nombre": "Keep"})
    await repo.create({"codigo": "DEL", "nombre": "Delete"})

    assert len(await repo.list()) == 2
    await repo.soft_delete(m1.id)

    remaining = await repo.list()
    assert len(remaining) == 1
    assert remaining[0].codigo == "DEL"


@pytest.mark.asyncio
async def test_tenant_isolation(db_session, tenant_a, tenant_b):
    repo_a = MateriaRepository(db_session, tenant_a.id)
    repo_b = MateriaRepository(db_session, tenant_b.id)

    await repo_a.create({"codigo": "A-01", "nombre": "Materia A"})
    await repo_b.create({"codigo": "B-01", "nombre": "Materia B"})

    assert len(await repo_a.list()) == 1
    assert len(await repo_b.list()) == 1
