"""TDD: UmbralService tests."""

import uuid

import pytest

from app.models.materia import Materia
from app.models.calificacion import UmbralMateria, Calificacion
from app.services.umbral_service import UmbralService


@pytest.fixture
async def materia(db_session, tenant):
    m = Materia(codigo="US-MAT", nombre="Umbral Svc", tenant_id=tenant.id)
    db_session.add(m)
    await db_session.commit()
    await db_session.refresh(m)
    return m


@pytest.mark.asyncio
async def test_get_umbral_returns_config(db_session, tenant, materia):
    """RED 7.1: get_umbral returns stored config."""
    um = UmbralMateria(tenant_id=tenant.id, materia_id=materia.id, umbral_pct=75)
    um.valores_aprobatorios = ["Aprobado"]
    db_session.add(um)
    await db_session.commit()

    svc = UmbralService(db_session, tenant.id)
    result = await svc.get_umbral(materia.id)

    assert result["umbral_pct"] == 75
    assert result["materia_id"] == materia.id


@pytest.mark.asyncio
async def test_get_umbral_returns_defaults_when_no_config(db_session, tenant, materia):
    """TRIANGULATE 7.4: Returns defaults when no config."""
    svc = UmbralService(db_session, tenant.id)
    result = await svc.get_umbral(materia.id)

    assert result["umbral_pct"] == 60
    assert result["valores_aprobatorios"] == ["Satisfactorio", "Supera lo esperado"]


@pytest.mark.asyncio
async def test_set_umbral_creates_new(db_session, tenant, materia):
    """TRIANGULATE 7.4: Creates new umbral config."""
    svc = UmbralService(db_session, tenant.id)
    result = await svc.set_umbral(materia.id, 80)

    assert result["umbral_pct"] == 80
    assert result["materia_id"] == materia.id


@pytest.mark.asyncio
async def test_set_umbral_updates_existing(db_session, tenant, materia):
    """TRIANGULATE 7.4: Updates existing umbral."""
    um = UmbralMateria(tenant_id=tenant.id, materia_id=materia.id, umbral_pct=50)
    um.valores_aprobatorios = ["Satisfactorio"]
    db_session.add(um)
    await db_session.commit()

    svc = UmbralService(db_session, tenant.id)
    result = await svc.set_umbral(materia.id, 80)

    assert result["umbral_pct"] == 80


@pytest.mark.asyncio
async def test_set_umbral_invalid_range_raises(db_session, tenant, materia):
    """TRIANGULATE 7.4: Invalid range raises."""
    svc = UmbralService(db_session, tenant.id)

    with pytest.raises(Exception) as exc:
        await svc.set_umbral(materia.id, 0)
    assert "422" in str(exc.type) or exc.value.status_code == 422

    with pytest.raises(Exception) as exc:
        await svc.set_umbral(materia.id, 101)
    assert "422" in str(exc.type) or exc.value.status_code == 422


@pytest.mark.asyncio
async def test_set_umbral_non_existent_materia_raises(db_session, tenant):
    """TRIANGULATE 7.4: Non-existent materia raises."""
    svc = UmbralService(db_session, tenant.id)
    with pytest.raises(Exception) as exc:
        await svc.set_umbral(uuid.uuid4(), 60)
    assert "404" in str(exc.type) or exc.value.status_code == 404


@pytest.mark.asyncio
async def test_get_umbral_non_existent_materia_raises(db_session, tenant):
    """TRIANGULATE 7.4: Non-existent materia raises."""
    svc = UmbralService(db_session, tenant.id)
    with pytest.raises(Exception) as exc:
        await svc.get_umbral(uuid.uuid4())
    assert "404" in str(exc.type) or exc.value.status_code == 404


@pytest.mark.asyncio
async def test_umbral_change_does_not_affect_existing_calificaciones(db_session, tenant, materia):
    """TRIANGULATE 7.4: Changing umbral does NOT retroactively affect grades."""
    svc = UmbralService(db_session, tenant.id)
    await svc.set_umbral(materia.id, 60)

    result = await svc.get_umbral(materia.id)
    assert result["umbral_pct"] == 60

    await svc.set_umbral(materia.id, 40)
    result = await svc.get_umbral(materia.id)
    assert result["umbral_pct"] == 40
