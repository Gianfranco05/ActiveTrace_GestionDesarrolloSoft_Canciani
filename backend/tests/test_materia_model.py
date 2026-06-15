import uuid

import pytest
from sqlalchemy.exc import IntegrityError

from app.core.estado_registro import EstadoRegistro
from app.models.materia import Materia


@pytest.mark.asyncio
async def test_create_materia(db_session, tenant):
    materia = Materia(
        codigo="PROG_I",
        nombre="Programación I",
        tenant_id=tenant.id,
    )
    db_session.add(materia)
    await db_session.commit()
    await db_session.refresh(materia)

    assert isinstance(materia.id, uuid.UUID)
    assert materia.tenant_id == tenant.id
    assert materia.codigo == "PROG_I"
    assert materia.nombre == "Programación I"
    assert materia.estado == EstadoRegistro.ACTIVA.value
    assert materia.created_at is not None
    assert materia.updated_at is not None
    assert materia.deleted_at is None


@pytest.mark.asyncio
async def test_materia_codigo_unique_per_tenant(db_session, tenant):
    m1 = Materia(codigo="UNICO", nombre="Mat 1", tenant_id=tenant.id)
    db_session.add(m1)
    await db_session.commit()

    m2 = Materia(codigo="UNICO", nombre="Mat 2", tenant_id=tenant.id)
    db_session.add(m2)
    with pytest.raises(IntegrityError):
        await db_session.commit()
    await db_session.rollback()


@pytest.mark.asyncio
async def test_materia_same_codigo_different_tenant(db_session, tenant_a, tenant_b):
    m1 = Materia(codigo="COMPARTIDO", nombre="Mat A", tenant_id=tenant_a.id)
    db_session.add(m1)
    await db_session.commit()

    m2 = Materia(codigo="COMPARTIDO", nombre="Mat B", tenant_id=tenant_b.id)
    db_session.add(m2)
    await db_session.commit()

    assert m1.id != m2.id


@pytest.mark.asyncio
async def test_materia_default_estado(db_session, tenant):
    m = Materia(codigo="DEF", nombre="Default", tenant_id=tenant.id)
    db_session.add(m)
    await db_session.commit()
    await db_session.refresh(m)
    assert m.estado == "Activa"


@pytest.mark.asyncio
async def test_materia_soft_delete(db_session, tenant):
    from datetime import datetime, timezone

    m = Materia(codigo="SD", nombre="Soft Delete", tenant_id=tenant.id)
    db_session.add(m)
    await db_session.commit()
    await db_session.refresh(m)

    assert m.deleted_at is None

    m.deleted_at = datetime.now(timezone.utc)
    await db_session.commit()
    assert m.deleted_at is not None


@pytest.mark.asyncio
async def test_materia_no_carrera_relation(db_session, tenant):
    m = Materia(codigo="MAT-INDEP", nombre="Independiente", tenant_id=tenant.id)
    assert not hasattr(m, "carrera_id")
    assert not hasattr(m, "cohorte_id")
