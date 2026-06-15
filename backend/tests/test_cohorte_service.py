import uuid
from datetime import date

import pytest
from fastapi import HTTPException

from app.models.carrera import Carrera
from app.repositories.cohorte_repository import CohorteRepository
from app.services.estructura_service import CohorteService


@pytest.mark.asyncio
async def test_create_cohorte_with_active_carrera_succeeds(db_session, tenant):
    carrera = Carrera(
        codigo="ACTIVA-SRV", nombre="Carrera Activa",
        tenant_id=tenant.id, estado="Activa",
    )
    db_session.add(carrera)
    await db_session.commit()
    await db_session.refresh(carrera)

    repo = CohorteRepository(db_session, tenant.id)
    service = CohorteService(repo, db_session, tenant.id)

    cohorte = await service.create({
        "carrera_id": carrera.id,
        "nombre": "SRV-TEST",
        "anio": 2025,
        "vig_desde": date(2025, 1, 1),
    })

    assert cohorte is not None
    assert cohorte.nombre == "SRV-TEST"
    assert cohorte.estado == "Activa"


@pytest.mark.asyncio
async def test_create_cohorte_with_inactive_carrera_raises_error(db_session, tenant):
    carrera = Carrera(
        codigo="INACTIVA-SRV", nombre="Carrera Inactiva",
        tenant_id=tenant.id, estado="Inactiva",
    )
    db_session.add(carrera)
    await db_session.commit()
    await db_session.refresh(carrera)

    repo = CohorteRepository(db_session, tenant.id)
    service = CohorteService(repo, db_session, tenant.id)

    with pytest.raises(HTTPException) as exc:
        await service.create({
            "carrera_id": carrera.id,
            "nombre": "SRV-FAIL",
            "anio": 2025,
            "vig_desde": date(2025, 1, 1),
        })
    assert exc.value.status_code == 409
    assert "Carrera must be active" in exc.value.detail


@pytest.mark.asyncio
async def test_update_cohorte_to_activa_with_inactive_carrera_raises(db_session, tenant):
    carrera = Carrera(
        codigo="UPD-INACT", nombre="Carrera Inactiva",
        tenant_id=tenant.id, estado="Inactiva",
    )
    db_session.add(carrera)
    await db_session.commit()
    await db_session.refresh(carrera)

    repo = CohorteRepository(db_session, tenant.id)
    service = CohorteService(repo, db_session, tenant.id)

    with pytest.raises(HTTPException) as exc:
        await service.update(uuid.UUID(int=0), {
            "estado": "Activa",
            "carrera_id": carrera.id,
        })
    assert exc.value.status_code == 409
