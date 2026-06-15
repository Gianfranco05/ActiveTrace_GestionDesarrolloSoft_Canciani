"""TDD: ComunicacionRepository tests."""

import uuid
from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import select

from app.models.comunicacion import Comunicacion, EstadoComunicacion
from app.models.auth_user import AuthUser
from app.models.usuario import Usuario
from app.repositories.comunicacion_repository import ComunicacionRepository


async def _create_user(db_session, tenant):
    au = AuthUser(tenant_id=tenant.id, email="rep@test.com", password_hash="hash")
    db_session.add(au)
    await db_session.commit()
    await db_session.refresh(au)
    u = Usuario(id=au.id, tenant_id=tenant.id, nombre="Rep", apellidos="Test")
    db_session.add(u)
    await db_session.commit()
    await db_session.refresh(u)
    return u


@pytest.mark.asyncio
async def test_create_comunicacion_encrypts_destinatario(db_session, tenant):
    repo = ComunicacionRepository(db_session, tenant.id)
    c = await repo.create({
        "lote_id": uuid.uuid4(),
        "destinatario": "student@test.com",
        "asunto": "Test",
        "cuerpo": "Hello",
        "estado": EstadoComunicacion.PENDIENTE.value,
    })
    assert c.id is not None
    assert c.tenant_id == tenant.id
    assert c.destinatario == "student@test.com"

    result = await db_session.execute(
        select(Comunicacion.destinatario).where(Comunicacion.id == c.id),
    )
    db_value = result.scalar_one()
    assert db_value != "student@test.com"
    assert len(db_value) > 30


@pytest.mark.asyncio
async def test_get_by_id_returns_decrypted(db_session, tenant):
    repo = ComunicacionRepository(db_session, tenant.id)
    c = await repo.create({
        "lote_id": uuid.uuid4(),
        "destinatario": "secret@test.com",
        "asunto": "Get Test",
        "cuerpo": "Body",
        "estado": EstadoComunicacion.PENDIENTE.value,
    })
    retrieved = await repo.get_by_id(c.id)
    assert retrieved is not None
    assert retrieved.destinatario == "secret@test.com"


@pytest.mark.asyncio
async def test_list_by_estado(db_session, tenant):
    repo = ComunicacionRepository(db_session, tenant.id)
    lote = uuid.uuid4()
    await repo.create({
        "lote_id": lote, "destinatario": "a@t.com",
        "asunto": "A", "cuerpo": "A",
        "estado": EstadoComunicacion.PENDIENTE.value,
    })
    await repo.create({
        "lote_id": lote, "destinatario": "b@t.com",
        "asunto": "B", "cuerpo": "B",
        "estado": EstadoComunicacion.ENVIADO.value,
    })
    db_session.expire_all()
    pendientes = await repo.list_by_estado(EstadoComunicacion.PENDIENTE.value)
    assert len(pendientes) >= 1


@pytest.mark.asyncio
async def test_list_by_lote(db_session, tenant):
    repo = ComunicacionRepository(db_session, tenant.id)
    lote_a = uuid.uuid4()
    lote_b = uuid.uuid4()
    await repo.create({
        "lote_id": lote_a, "destinatario": "a@t.com",
        "asunto": "A", "cuerpo": "A",
        "estado": EstadoComunicacion.PENDIENTE.value,
    })
    await repo.create({
        "lote_id": lote_b, "destinatario": "b@t.com",
        "asunto": "B", "cuerpo": "B",
        "estado": EstadoComunicacion.PENDIENTE.value,
    })
    db_session.expire_all()
    lote_a_items = await repo.list_by_lote(lote_a)
    assert len(lote_a_items) >= 1


@pytest.mark.asyncio
async def test_list_by_date_range(db_session, tenant):
    repo = ComunicacionRepository(db_session, tenant.id)
    now = datetime.now(timezone.utc)
    await repo.create({
        "lote_id": uuid.uuid4(), "destinatario": "a@t.com",
        "asunto": "A", "cuerpo": "A",
        "estado": EstadoComunicacion.PENDIENTE.value,
    })
    db_session.expire_all()
    items = await repo.list_by_date_range(
        now - timedelta(hours=1), now + timedelta(hours=1),
    )
    assert len(items) >= 1


@pytest.mark.asyncio
async def test_soft_delete(db_session, tenant):
    repo = ComunicacionRepository(db_session, tenant.id)
    c = await repo.create({
        "lote_id": uuid.uuid4(), "destinatario": "del@t.com",
        "asunto": "Del", "cuerpo": "Test",
        "estado": EstadoComunicacion.PENDIENTE.value,
    })
    c_id = c.id
    db_session.expire_all()
    deleted = await repo.soft_delete(c_id)
    assert deleted is True
    assert await repo.get_by_id(c_id) is None


@pytest.mark.asyncio
async def test_tenant_scope_enforced(db_session, tenant, tenant_b):
    repo_a = ComunicacionRepository(db_session, tenant.id)
    c = await repo_a.create({
        "lote_id": uuid.uuid4(), "destinatario": "a@t.com",
        "asunto": "A", "cuerpo": "A",
        "estado": EstadoComunicacion.PENDIENTE.value,
    })
    repo_b = ComunicacionRepository(db_session, tenant_b.id)
    assert await repo_b.get_by_id(c.id) is None


@pytest.mark.asyncio
async def test_bulk_set_aprobado(db_session, tenant):
    user = await _create_user(db_session, tenant)
    repo = ComunicacionRepository(db_session, tenant.id)
    lote = uuid.uuid4()
    await repo.create({
        "lote_id": lote, "destinatario": "a@t.com",
        "asunto": "A", "cuerpo": "A",
        "estado": EstadoComunicacion.PENDIENTE.value,
    })
    await repo.create({
        "lote_id": lote, "destinatario": "b@t.com",
        "asunto": "B", "cuerpo": "B",
        "estado": EstadoComunicacion.PENDIENTE.value,
    })
    count = await repo.bulk_set_aprobado(lote, user.id)
    assert count == 2


@pytest.mark.asyncio
async def test_bulk_cancel_by_lote(db_session, tenant):
    repo = ComunicacionRepository(db_session, tenant.id)
    lote = uuid.uuid4()
    await repo.create({
        "lote_id": lote, "destinatario": "a@t.com",
        "asunto": "A", "cuerpo": "A",
        "estado": EstadoComunicacion.PENDIENTE.value,
    })
    db_session.expire_all()
    count = await repo.bulk_cancel_by_lote(lote)
    assert count == 1
    items = await repo.list_by_lote(lote)
    assert items[0].estado == EstadoComunicacion.CANCELADO.value
