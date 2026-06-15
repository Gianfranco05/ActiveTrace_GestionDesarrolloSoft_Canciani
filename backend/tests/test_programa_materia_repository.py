import uuid
from datetime import date

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.carrera import Carrera
from app.models.cohorte import Cohorte
from app.models.materia import Materia


async def _seed_estructura(db_session: AsyncSession, tenant_id: uuid.UUID):
    suffix = uuid.uuid4().hex[:8]
    c = Carrera(id=uuid.uuid4(), codigo=f"TEST-{suffix}", nombre="Test Carrera", tenant_id=tenant_id)
    db_session.add(c)
    m = Materia(id=uuid.uuid4(), codigo=f"MAT-{suffix}", nombre="Materia 1", tenant_id=tenant_id)
    db_session.add(m)
    co = Cohorte(
        id=uuid.uuid4(), carrera_id=c.id, nombre=f"COH-{suffix}",
        anio=2026, vig_desde=date(2026, 1, 1), tenant_id=tenant_id,
    )
    db_session.add(co)
    await db_session.commit()
    return c.id, m.id, co.id


@pytest.mark.asyncio
async def test_create_programa(db_session: AsyncSession, tenant):
    from app.repositories.programa_materia_repository import ProgramaMateriaRepository

    carrera_id, materia_id, cohorte_id = await _seed_estructura(db_session, tenant.id)
    repo = ProgramaMateriaRepository(db_session, tenant.id)

    result = await repo.create({
        "materia_id": materia_id,
        "carrera_id": carrera_id,
        "cohorte_id": cohorte_id,
        "titulo": "Programa Analitico 2026",
        "referencia_archivo": "s3://bucket/prog/abc123.pdf",
    })

    assert result is not None
    assert result.id is not None
    assert result.tenant_id == tenant.id
    assert result.materia_id == materia_id
    assert result.carrera_id == carrera_id
    assert result.cohorte_id == cohorte_id
    assert result.titulo == "Programa Analitico 2026"
    assert result.referencia_archivo == "s3://bucket/prog/abc123.pdf"
    assert result.cargado_at is not None


@pytest.mark.asyncio
async def test_get_by_id_returns_programa(db_session: AsyncSession, tenant):
    from app.repositories.programa_materia_repository import ProgramaMateriaRepository

    carrera_id, materia_id, cohorte_id = await _seed_estructura(db_session, tenant.id)
    repo = ProgramaMateriaRepository(db_session, tenant.id)

    created = await repo.create({
        "materia_id": materia_id,
        "carrera_id": carrera_id,
        "cohorte_id": cohorte_id,
        "titulo": "Programa Test",
        "referencia_archivo": "s3://bucket/test.pdf",
    })

    found = await repo.get_by_id(created.id, tenant.id)
    assert found is not None
    assert found.id == created.id
    assert found.titulo == "Programa Test"


@pytest.mark.asyncio
async def test_get_by_id_returns_none_for_wrong_id(db_session: AsyncSession, tenant):
    from app.repositories.programa_materia_repository import ProgramaMateriaRepository

    repo = ProgramaMateriaRepository(db_session, tenant.id)
    result = await repo.get_by_id(uuid.uuid4(), tenant.id)
    assert result is None


@pytest.mark.asyncio
async def test_list_by_filters_returns_all(db_session: AsyncSession, tenant):
    from app.repositories.programa_materia_repository import ProgramaMateriaRepository

    carrera_id, materia_id, cohorte_id = await _seed_estructura(db_session, tenant.id)
    repo = ProgramaMateriaRepository(db_session, tenant.id)

    await repo.create({
        "materia_id": materia_id, "carrera_id": carrera_id,
        "cohorte_id": cohorte_id, "titulo": "Prog 1", "referencia_archivo": "r1",
    })
    await repo.create({
        "materia_id": materia_id, "carrera_id": carrera_id,
        "cohorte_id": cohorte_id, "titulo": "Prog 2", "referencia_archivo": "r2",
    })

    items, total = await repo.list_by_filters(tenant.id)
    assert total >= 2
    assert len(items) >= 2


@pytest.mark.asyncio
async def test_list_by_filters_by_materia(db_session: AsyncSession, tenant):
    from app.repositories.programa_materia_repository import ProgramaMateriaRepository

    carrera_id, materia_id, cohorte_id = await _seed_estructura(db_session, tenant.id)
    m2 = Materia(id=uuid.uuid4(), codigo=f"MAT2-{uuid.uuid4().hex[:8]}", nombre="Materia 2", tenant_id=tenant.id)
    db_session.add(m2)
    await db_session.commit()

    repo = ProgramaMateriaRepository(db_session, tenant.id)
    await repo.create({
        "materia_id": materia_id, "carrera_id": carrera_id,
        "cohorte_id": cohorte_id, "titulo": "Prog MAT1", "referencia_archivo": "r1",
    })
    await repo.create({
        "materia_id": m2.id, "carrera_id": carrera_id,
        "cohorte_id": cohorte_id, "titulo": "Prog MAT2", "referencia_archivo": "r2",
    })

    items, total = await repo.list_by_filters(tenant.id, materia_id=materia_id)
    assert total == 1
    assert items[0].titulo == "Prog MAT1"


@pytest.mark.asyncio
async def test_list_by_filters_empty(db_session: AsyncSession, tenant):
    from app.repositories.programa_materia_repository import ProgramaMateriaRepository

    repo = ProgramaMateriaRepository(db_session, tenant.id)
    items, total = await repo.list_by_filters(tenant.id)
    assert total == 0
    assert items == []


@pytest.mark.asyncio
async def test_soft_delete_programa(db_session: AsyncSession, tenant):
    from app.repositories.programa_materia_repository import ProgramaMateriaRepository

    carrera_id, materia_id, cohorte_id = await _seed_estructura(db_session, tenant.id)
    repo = ProgramaMateriaRepository(db_session, tenant.id)

    created = await repo.create({
        "materia_id": materia_id, "carrera_id": carrera_id,
        "cohorte_id": cohorte_id, "titulo": "To Delete", "referencia_archivo": "r",
    })

    deleted = await repo.soft_delete(created.id, tenant.id)
    assert deleted is True

    found = await repo.get_by_id(created.id, tenant.id)
    assert found is None


@pytest.mark.asyncio
async def test_list_excludes_soft_deleted(db_session: AsyncSession, tenant):
    from app.repositories.programa_materia_repository import ProgramaMateriaRepository

    carrera_id, materia_id, cohorte_id = await _seed_estructura(db_session, tenant.id)
    repo = ProgramaMateriaRepository(db_session, tenant.id)

    p1 = await repo.create({
        "materia_id": materia_id, "carrera_id": carrera_id,
        "cohorte_id": cohorte_id, "titulo": "Keep", "referencia_archivo": "r1",
    })
    await repo.create({
        "materia_id": materia_id, "carrera_id": carrera_id,
        "cohorte_id": cohorte_id, "titulo": "Delete Me", "referencia_archivo": "r2",
    })

    items, total = await repo.list_by_filters(tenant.id)
    assert total == 2

    await repo.soft_delete(p1.id, tenant.id)
    items2, total2 = await repo.list_by_filters(tenant.id)
    assert total2 == 1
    assert items2[0].titulo == "Delete Me"


@pytest.mark.asyncio
async def test_tenant_isolation(db_session: AsyncSession, tenant, tenant_b):
    from app.repositories.programa_materia_repository import ProgramaMateriaRepository

    carrera_id_b, materia_id_b, cohorte_id_b = await _seed_estructura(db_session, tenant_b.id)
    repo_b = ProgramaMateriaRepository(db_session, tenant_b.id)
    await repo_b.create({
        "materia_id": materia_id_b, "carrera_id": carrera_id_b,
        "cohorte_id": cohorte_id_b, "titulo": "Tenant B Program", "referencia_archivo": "rb",
    })

    repo_a = ProgramaMateriaRepository(db_session, tenant.id)
    items, total = await repo_a.list_by_filters(tenant.id)
    assert total == 0


@pytest.mark.asyncio
async def test_get_by_id_returns_none_for_other_tenant(db_session: AsyncSession, tenant, tenant_b):
    from app.repositories.programa_materia_repository import ProgramaMateriaRepository

    carrera_id_b, materia_id_b, cohorte_id_b = await _seed_estructura(db_session, tenant_b.id)
    repo_b = ProgramaMateriaRepository(db_session, tenant_b.id)
    created = await repo_b.create({
        "materia_id": materia_id_b, "carrera_id": carrera_id_b,
        "cohorte_id": cohorte_id_b, "titulo": "Other Tenant", "referencia_archivo": "rb",
    })

    repo_a = ProgramaMateriaRepository(db_session, tenant.id)
    found = await repo_a.get_by_id(created.id, tenant.id)
    assert found is None


@pytest.mark.asyncio
async def test_pagination(db_session: AsyncSession, tenant):
    from app.repositories.programa_materia_repository import ProgramaMateriaRepository

    carrera_id, materia_id, cohorte_id = await _seed_estructura(db_session, tenant.id)
    repo = ProgramaMateriaRepository(db_session, tenant.id)

    for i in range(5):
        await repo.create({
            "materia_id": materia_id, "carrera_id": carrera_id,
            "cohorte_id": cohorte_id, "titulo": f"Prog {i}",
            "referencia_archivo": f"r{i}",
        })

    items, total = await repo.list_by_filters(tenant.id, offset=0, limit=2)
    assert len(items) == 2
    assert total == 5

    items2, total2 = await repo.list_by_filters(tenant.id, offset=2, limit=2)
    assert len(items2) == 2
    assert total2 == 5

    items3, total3 = await repo.list_by_filters(tenant.id, offset=4, limit=2)
    assert len(items3) == 1
    assert total3 == 5
