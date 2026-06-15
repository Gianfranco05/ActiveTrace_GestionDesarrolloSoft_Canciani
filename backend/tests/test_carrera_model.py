import uuid

import pytest
from sqlalchemy.exc import IntegrityError

from app.core.estado_registro import EstadoRegistro
from app.models.carrera import Carrera


@pytest.mark.asyncio
async def test_create_carrera(db_session, tenant):
    carrera = Carrera(
        codigo="LIC-2025",
        nombre="Licenciatura 2025",
        tenant_id=tenant.id,
    )
    db_session.add(carrera)
    await db_session.commit()
    await db_session.refresh(carrera)

    assert isinstance(carrera.id, uuid.UUID)
    assert carrera.tenant_id == tenant.id
    assert carrera.codigo == "LIC-2025"
    assert carrera.nombre == "Licenciatura 2025"
    assert carrera.estado == EstadoRegistro.ACTIVA.value
    assert carrera.created_at is not None
    assert carrera.updated_at is not None
    assert carrera.deleted_at is None


@pytest.mark.asyncio
async def test_carrera_codigo_unique_per_tenant(db_session, tenant):
    c1 = Carrera(codigo="UNICO", nombre="Carrera 1", tenant_id=tenant.id)
    db_session.add(c1)
    await db_session.commit()

    c2 = Carrera(codigo="UNICO", nombre="Carrera 2", tenant_id=tenant.id)
    db_session.add(c2)
    with pytest.raises(IntegrityError):
        await db_session.commit()
    await db_session.rollback()


@pytest.mark.asyncio
async def test_carrera_same_codigo_different_tenant(db_session, tenant_a, tenant_b):
    c1 = Carrera(codigo="COMPARTIDO", nombre="Carrera A", tenant_id=tenant_a.id)
    db_session.add(c1)
    await db_session.commit()

    c2 = Carrera(codigo="COMPARTIDO", nombre="Carrera B", tenant_id=tenant_b.id)
    db_session.add(c2)
    await db_session.commit()

    assert c1.id != c2.id


@pytest.mark.asyncio
async def test_carrera_default_estado(db_session, tenant):
    carrera = Carrera(codigo="DEF", nombre="Default Estado", tenant_id=tenant.id)
    db_session.add(carrera)
    await db_session.commit()
    await db_session.refresh(carrera)

    assert carrera.estado == "Activa"


@pytest.mark.asyncio
async def test_carrera_custom_estado(db_session, tenant):
    carrera = Carrera(
        codigo="INACT",
        nombre="Inactiva",
        estado="Inactiva",
        tenant_id=tenant.id,
    )
    db_session.add(carrera)
    await db_session.commit()
    await db_session.refresh(carrera)

    assert carrera.estado == "Inactiva"


@pytest.mark.asyncio
async def test_carrera_soft_delete(db_session, tenant):
    carrera = Carrera(codigo="SD", nombre="Soft Delete", tenant_id=tenant.id)
    db_session.add(carrera)
    await db_session.commit()
    await db_session.refresh(carrera)

    assert carrera.deleted_at is None

    from datetime import datetime, timezone
    carrera.deleted_at = datetime.now(timezone.utc)
    await db_session.commit()

    assert carrera.deleted_at is not None
