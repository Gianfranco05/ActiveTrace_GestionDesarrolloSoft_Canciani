import uuid
from datetime import date

import pytest

from app.models.carrera import Carrera
from app.repositories.cohorte_repository import CohorteRepository


@pytest.fixture
async def _carrera(db_session, tenant):
    carrera = Carrera(codigo="BASE", nombre="Carrera Base", tenant_id=tenant.id)
    db_session.add(carrera)
    await db_session.commit()
    await db_session.refresh(carrera)
    return carrera


@pytest.mark.asyncio
async def test_create_cohorte(db_session, tenant, _carrera):
    repo = CohorteRepository(db_session, tenant.id)
    cohorte = await repo.create({
        "carrera_id": _carrera.id,
        "nombre": "MAR-2026",
        "anio": 2026,
        "vig_desde": date(2026, 3, 1),
    })

    assert isinstance(cohorte.id, uuid.UUID)
    assert cohorte.tenant_id == tenant.id
    assert cohorte.carrera_id == _carrera.id
    assert cohorte.nombre == "MAR-2026"
    assert cohorte.anio == 2026
    assert cohorte.vig_desde == date(2026, 3, 1)
    assert cohorte.vig_hasta is None
    assert cohorte.estado == "Activa"


@pytest.mark.asyncio
async def test_get_by_carrera_returns_cohortes(db_session, tenant, _carrera):
    repo = CohorteRepository(db_session, tenant.id)
    await repo.create({
        "carrera_id": _carrera.id, "nombre": "C-01",
        "anio": 2025, "vig_desde": date(2025, 1, 1),
    })
    await repo.create({
        "carrera_id": _carrera.id, "nombre": "C-02",
        "anio": 2025, "vig_desde": date(2025, 6, 1),
    })

    results = await repo.get_by_carrera(_carrera.id)
    assert len(results) == 2
    nombres = {r.nombre for r in results}
    assert nombres == {"C-01", "C-02"}


@pytest.mark.asyncio
async def test_get_by_carrera_empty(db_session, tenant, _carrera):
    repo = CohorteRepository(db_session, tenant.id)
    results = await repo.get_by_carrera(_carrera.id)
    assert results == []


@pytest.mark.asyncio
async def test_get_activas_by_carrera(db_session, tenant, _carrera):
    repo = CohorteRepository(db_session, tenant.id)
    c1 = await repo.create({
        "carrera_id": _carrera.id, "nombre": "ACTIVA",
        "anio": 2025, "vig_desde": date(2025, 1, 1),
    })
    await repo.create({
        "carrera_id": _carrera.id, "nombre": "INACTIVA",
        "anio": 2025, "vig_desde": date(2025, 1, 1),
        "estado": "Inactiva",
    })

    activas = await repo.get_activas_by_carrera(_carrera.id)
    assert len(activas) == 1
    assert activas[0].id == c1.id


@pytest.mark.asyncio
async def test_tenant_isolation(db_session, tenant_a, tenant_b):
    c_a = Carrera(codigo="TA", nombre="Tenant A", tenant_id=tenant_a.id)
    c_b = Carrera(codigo="TB", nombre="Tenant B", tenant_id=tenant_b.id)
    db_session.add(c_a)
    db_session.add(c_b)
    await db_session.commit()
    await db_session.refresh(c_a)
    await db_session.refresh(c_b)

    repo_a = CohorteRepository(db_session, tenant_a.id)
    repo_b = CohorteRepository(db_session, tenant_b.id)

    await repo_a.create({
        "carrera_id": c_a.id, "nombre": "A-01",
        "anio": 2025, "vig_desde": date(2025, 1, 1),
    })
    await repo_b.create({
        "carrera_id": c_b.id, "nombre": "B-01",
        "anio": 2025, "vig_desde": date(2025, 1, 1),
    })

    assert len(await repo_a.list()) == 1
    assert len(await repo_b.list()) == 1
