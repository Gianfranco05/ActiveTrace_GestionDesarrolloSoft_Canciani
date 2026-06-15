import uuid
from datetime import date

import pytest
from sqlalchemy.exc import IntegrityError

from app.core.estado_registro import EstadoRegistro
from app.models.carrera import Carrera
from app.models.cohorte import Cohorte


@pytest.mark.asyncio
async def test_create_cohorte(db_session, tenant):
    carrera = Carrera(codigo="CARR", nombre="Carrera Test", tenant_id=tenant.id)
    db_session.add(carrera)
    await db_session.commit()
    await db_session.refresh(carrera)

    cohorte = Cohorte(
        carrera_id=carrera.id,
        nombre="AGO-2025",
        anio=2025,
        vig_desde=date(2025, 8, 1),
        tenant_id=tenant.id,
    )
    db_session.add(cohorte)
    await db_session.commit()
    await db_session.refresh(cohorte)

    assert isinstance(cohorte.id, uuid.UUID)
    assert cohorte.tenant_id == tenant.id
    assert cohorte.carrera_id == carrera.id
    assert cohorte.nombre == "AGO-2025"
    assert cohorte.anio == 2025
    assert cohorte.vig_desde == date(2025, 8, 1)
    assert cohorte.vig_hasta is None
    assert cohorte.estado == EstadoRegistro.ACTIVA.value
    assert cohorte.created_at is not None
    assert cohorte.updated_at is not None
    assert cohorte.deleted_at is None


@pytest.mark.asyncio
async def test_cohorte_nombre_unique_per_carrera(db_session, tenant):
    carrera = Carrera(codigo="UQ", nombre="Unica", tenant_id=tenant.id)
    db_session.add(carrera)
    await db_session.commit()
    await db_session.refresh(carrera)

    c1 = Cohorte(
        carrera_id=carrera.id, nombre="UNICO",
        anio=2025, vig_desde=date(2025, 1, 1), tenant_id=tenant.id,
    )
    db_session.add(c1)
    await db_session.commit()

    c2 = Cohorte(
        carrera_id=carrera.id, nombre="UNICO",
        anio=2025, vig_desde=date(2025, 1, 1), tenant_id=tenant.id,
    )
    db_session.add(c2)
    with pytest.raises(IntegrityError):
        await db_session.commit()
    await db_session.rollback()


@pytest.mark.asyncio
async def test_cohorte_default_estado(db_session, tenant):
    carrera = Carrera(codigo="CDEF", nombre="Carrera Def", tenant_id=tenant.id)
    db_session.add(carrera)
    await db_session.commit()
    await db_session.refresh(carrera)

    cohorte = Cohorte(
        carrera_id=carrera.id, nombre="DEF",
        anio=2025, vig_desde=date(2025, 1, 1), tenant_id=tenant.id,
    )
    db_session.add(cohorte)
    await db_session.commit()
    await db_session.refresh(cohorte)

    assert cohorte.estado == "Activa"


@pytest.mark.asyncio
async def test_cohorte_vig_hasta_nullable(db_session, tenant):
    carrera = Carrera(codigo="VHN", nombre="VigHasta Null", tenant_id=tenant.id)
    db_session.add(carrera)
    await db_session.commit()
    await db_session.refresh(carrera)

    cohorte = Cohorte(
        carrera_id=carrera.id, nombre="OPEN",
        anio=2025, vig_desde=date(2025, 1, 1),
        vig_hasta=date(2025, 12, 31), tenant_id=tenant.id,
    )
    db_session.add(cohorte)
    await db_session.commit()
    await db_session.refresh(cohorte)

    assert cohorte.vig_hasta == date(2025, 12, 31)


@pytest.mark.asyncio
async def test_cohorte_fk_carrera_enforced(db_session, tenant):
    fake_id = uuid.uuid4()
    cohorte = Cohorte(
        carrera_id=fake_id, nombre="NO-CARR",
        anio=2025, vig_desde=date(2025, 1, 1), tenant_id=tenant.id,
    )
    db_session.add(cohorte)
    with pytest.raises(IntegrityError):
        await db_session.commit()
    await db_session.rollback()


@pytest.mark.asyncio
async def test_cohorte_soft_delete(db_session, tenant):
    from datetime import datetime, timezone

    carrera = Carrera(codigo="CSD", nombre="Cohorte SD", tenant_id=tenant.id)
    db_session.add(carrera)
    await db_session.commit()
    await db_session.refresh(carrera)

    cohorte = Cohorte(
        carrera_id=carrera.id, nombre="SD-TEST",
        anio=2025, vig_desde=date(2025, 1, 1), tenant_id=tenant.id,
    )
    db_session.add(cohorte)
    await db_session.commit()
    await db_session.refresh(cohorte)

    assert cohorte.deleted_at is None

    cohorte.deleted_at = datetime.now(timezone.utc)
    await db_session.commit()

    assert cohorte.deleted_at is not None
