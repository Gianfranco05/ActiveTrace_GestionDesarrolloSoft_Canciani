"""TDD: UmbralRepository tests."""

import uuid
from datetime import datetime, timezone

import pytest

from app.models.calificacion import UmbralMateria
from app.models.materia import Materia
from app.repositories.umbral_repository import UmbralRepository


@pytest.fixture
async def materia(db_session, tenant):
    m = Materia(codigo="UMB-MAT", nombre="Umbral Test", tenant_id=tenant.id)
    db_session.add(m)
    await db_session.commit()
    await db_session.refresh(m)
    return m


@pytest.mark.asyncio
async def test_get_by_materia_returns_umbral(db_session, tenant, materia):
    """RED 4.1: get_by_materia returns UmbralMateria when one exists."""
    um = UmbralMateria(tenant_id=tenant.id, materia_id=materia.id)
    um.valores_aprobatorios = ["Satisfactorio"]
    db_session.add(um)
    await db_session.commit()

    repo = UmbralRepository(db_session, tenant.id)
    result = await repo.get_by_materia(materia.id)

    assert result is not None
    assert result.materia_id == materia.id
    assert result.umbral_pct == 60


@pytest.mark.asyncio
async def test_get_by_materia_returns_none(db_session, tenant):
    """TRIANGULATE 4.4: get_by_materia returns None when no config."""
    repo = UmbralRepository(db_session, tenant.id)
    result = await repo.get_by_materia(uuid.uuid4())
    assert result is None


@pytest.mark.asyncio
async def test_upsert_creates_new(db_session, tenant, materia):
    """TRIANGULATE 4.4: upsert creates new UmbralMateria."""
    repo = UmbralRepository(db_session, tenant.id)
    result = await repo.upsert(
        materia_id=materia.id,
        data={"umbral_pct": 75, "valores_aprobatorios": ["Aprobado"]},
    )
    assert result is not None
    assert result.umbral_pct == 75
    assert result.materia_id == materia.id


@pytest.mark.asyncio
async def test_upsert_updates_existing(db_session, tenant, materia):
    """TRIANGULATE 4.4: upsert updates existing UmbralMateria."""
    um = UmbralMateria(tenant_id=tenant.id, materia_id=materia.id, umbral_pct=50)
    um.valores_aprobatorios = ["Satisfactorio"]
    db_session.add(um)
    await db_session.commit()

    repo = UmbralRepository(db_session, tenant.id)
    result = await repo.upsert(
        materia_id=materia.id,
        data={"umbral_pct": 80},
    )
    assert result.umbral_pct == 80


@pytest.mark.asyncio
async def test_tenant_isolation_umbral_repo(db_session, tenant_a, tenant_b):
    """TRIANGULATE 4.4: tenant isolation."""
    ma = Materia(codigo="UMB-A", nombre="A", tenant_id=tenant_a.id)
    mb = Materia(codigo="UMB-B", nombre="B", tenant_id=tenant_b.id)
    db_session.add_all([ma, mb])
    await db_session.commit()
    await db_session.refresh(ma)
    await db_session.refresh(mb)

    ua = UmbralMateria(tenant_id=tenant_a.id, materia_id=ma.id, umbral_pct=60)
    ua.valores_aprobatorios = ["Satisfactorio"]
    ub = UmbralMateria(tenant_id=tenant_b.id, materia_id=mb.id, umbral_pct=70)
    ub.valores_aprobatorios = ["Satisfactorio"]
    db_session.add_all([ua, ub])
    await db_session.commit()

    repo_a = UmbralRepository(db_session, tenant_a.id)
    result = await repo_a.get_by_materia(ma.id)
    assert result is not None
    assert result.umbral_pct == 60

    # Should NOT see tenant_b's umbral
    result_b = await repo_a.get_by_materia(mb.id)
    assert result_b is None
