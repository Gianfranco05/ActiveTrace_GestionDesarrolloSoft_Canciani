"""TDD: Comunicacion model tests."""

import uuid

import pytest
from sqlalchemy import select

from app.models.comunicacion import Comunicacion, EstadoComunicacion


@pytest.mark.asyncio
async def test_create_comunicacion_pendiente(db_session, tenant):
    c = Comunicacion(
        tenant_id=tenant.id,
        lote_id=uuid.uuid4(),
        destinatario="encrypted@test.com",
        asunto="Test Asunto",
        cuerpo="Test Cuerpo",
        estado=EstadoComunicacion.PENDIENTE,
    )
    db_session.add(c)
    await db_session.commit()
    await db_session.refresh(c)

    assert c.id is not None
    assert isinstance(c.id, uuid.UUID)
    assert c.tenant_id == tenant.id
    assert c.estado == EstadoComunicacion.PENDIENTE
    assert c.created_at is not None
    assert c.updated_at is not None


@pytest.mark.asyncio
async def test_estado_comunicacion_enum_values():
    assert EstadoComunicacion.PENDIENTE.value == "Pendiente"
    assert EstadoComunicacion.ENVIANDO.value == "Enviando"
    assert EstadoComunicacion.ENVIADO.value == "Enviado"
    assert EstadoComunicacion.ERROR.value == "Error"
    assert EstadoComunicacion.CANCELADO.value == "Cancelado"


@pytest.mark.asyncio
async def test_soft_delete_mixin(db_session, tenant):
    c = Comunicacion(
        tenant_id=tenant.id,
        lote_id=uuid.uuid4(),
        destinatario="test@test.com",
        asunto="Test",
        cuerpo="Test",
        estado=EstadoComunicacion.PENDIENTE,
    )
    db_session.add(c)
    await db_session.commit()
    await db_session.refresh(c)

    c.deleted_at = __import__("datetime").datetime.now(__import__("datetime").timezone.utc)
    await db_session.commit()

    result = await db_session.execute(
        select(Comunicacion).where(
            Comunicacion.id == c.id,
            Comunicacion.deleted_at.is_(None),
        ),
    )
    assert result.scalar_one_or_none() is None


@pytest.mark.asyncio
async def test_comunicacion_encrypted_destinatario_field(db_session, tenant):
    c = Comunicacion(
        tenant_id=tenant.id,
        lote_id=uuid.uuid4(),
        destinatario="user@example.com",
        asunto="Test",
        cuerpo="Test",
        estado=EstadoComunicacion.PENDIENTE,
    )
    db_session.add(c)
    await db_session.commit()
    result = await db_session.execute(
        select(Comunicacion.destinatario).where(Comunicacion.id == c.id),
    )
    db_value = result.scalar_one()
    assert db_value != "user@example.com"
    assert len(db_value) > 30


@pytest.mark.asyncio
async def test_comunicacion_lote_id_groups_messages(db_session, tenant):
    lote_id = uuid.uuid4()
    c1 = Comunicacion(
        tenant_id=tenant.id, lote_id=lote_id,
        destinatario="a@test.com", asunto="A", cuerpo="A",
        estado=EstadoComunicacion.PENDIENTE,
    )
    c2 = Comunicacion(
        tenant_id=tenant.id, lote_id=lote_id,
        destinatario="b@test.com", asunto="B", cuerpo="B",
        estado=EstadoComunicacion.PENDIENTE,
    )
    db_session.add_all([c1, c2])
    await db_session.commit()

    result = await db_session.execute(
        select(Comunicacion).where(Comunicacion.lote_id == lote_id),
    )
    records = result.scalars().all()
    assert len(records) == 2


@pytest.mark.asyncio
async def test_comunicacion_requiere_aprobacion_default(db_session, tenant):
    c = Comunicacion(
        tenant_id=tenant.id,
        lote_id=uuid.uuid4(),
        destinatario="test@test.com",
        asunto="Test",
        cuerpo="Test",
        estado=EstadoComunicacion.PENDIENTE,
    )
    db_session.add(c)
    await db_session.commit()
    await db_session.refresh(c)
    assert c.requiere_aprobacion is False
    assert c.aprobado_por is None
