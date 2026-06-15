import uuid
from datetime import datetime, timezone

import pytest

from app.models.auth_user import AuthUser
from app.models.mensaje import Mensaje
from app.models.usuario import Usuario


def _create_user(db_session, tenant, email, nombre, apellidos):
    auth = AuthUser(
        tenant_id=tenant.id,
        email=email,
        password_hash="hash",
    )
    db_session.add(auth)
    db_session.commit_sync = None
    return auth


@pytest.mark.asyncio
async def test_mensaje_creation(db_session, tenant):
    auth_sender = AuthUser(tenant_id=tenant.id, email="sender@test.com", password_hash="x")
    auth_recip = AuthUser(tenant_id=tenant.id, email="recip@test.com", password_hash="x")
    db_session.add_all([auth_sender, auth_recip])
    await db_session.commit()
    await db_session.refresh(auth_sender)
    await db_session.refresh(auth_recip)

    sender = Usuario(id=auth_sender.id, tenant_id=tenant.id, nombre="Emisor", apellidos="Test")
    recip = Usuario(id=auth_recip.id, tenant_id=tenant.id, nombre="Receptor", apellidos="Test")
    db_session.add_all([sender, recip])
    await db_session.commit()

    msg = Mensaje(
        tenant_id=tenant.id,
        sender_id=sender.id,
        recipient_id=recip.id,
        asunto="Test subject",
        cuerpo="Test body",
    )
    db_session.add(msg)
    await db_session.commit()
    await db_session.refresh(msg)

    assert msg.id is not None
    assert isinstance(msg.id, uuid.UUID)
    assert msg.tenant_id == tenant.id
    assert msg.sender_id == sender.id
    assert msg.recipient_id == recip.id
    assert msg.parent_id is None
    assert msg.asunto == "Test subject"
    assert msg.cuerpo == "Test body"
    assert msg.leido is False
    assert msg.leido_at is None
    assert msg.created_at is not None
    assert msg.updated_at is not None
    assert msg.deleted_at is None


@pytest.mark.asyncio
async def test_mensaje_parent_nullable(db_session, tenant):
    auth = AuthUser(tenant_id=tenant.id, email="a@test.com", password_hash="x")
    db_session.add(auth)
    await db_session.commit()
    await db_session.refresh(auth)
    u = Usuario(id=auth.id, tenant_id=tenant.id, nombre="A", apellidos="B")
    db_session.add(u)
    await db_session.commit()

    msg = Mensaje(tenant_id=tenant.id, sender_id=u.id, recipient_id=u.id, asunto="S", cuerpo="C")
    db_session.add(msg)
    await db_session.commit()

    assert msg.parent_id is None


@pytest.mark.asyncio
async def test_mensaje_leido_default_false(db_session, tenant):
    auth = AuthUser(tenant_id=tenant.id, email="b@test.com", password_hash="x")
    db_session.add(auth)
    await db_session.commit()
    await db_session.refresh(auth)
    u = Usuario(id=auth.id, tenant_id=tenant.id, nombre="B", apellidos="C")
    db_session.add(u)
    await db_session.commit()

    msg = Mensaje(tenant_id=tenant.id, sender_id=u.id, recipient_id=u.id, asunto="S", cuerpo="C")
    db_session.add(msg)
    await db_session.commit()
    await db_session.refresh(msg)

    assert msg.leido is False


@pytest.mark.asyncio
async def test_mensaje_self_referential_fk(db_session, tenant):
    auth = AuthUser(tenant_id=tenant.id, email="c@test.com", password_hash="x")
    db_session.add(auth)
    await db_session.commit()
    await db_session.refresh(auth)
    u = Usuario(id=auth.id, tenant_id=tenant.id, nombre="C", apellidos="D")
    db_session.add(u)
    await db_session.commit()

    parent = Mensaje(tenant_id=tenant.id, sender_id=u.id, recipient_id=u.id, asunto="Root", cuerpo="Root body")
    db_session.add(parent)
    await db_session.commit()
    await db_session.refresh(parent)

    reply = Mensaje(
        tenant_id=tenant.id,
        sender_id=u.id,
        recipient_id=u.id,
        parent_id=parent.id,
        asunto="Re: Root",
        cuerpo="Reply body",
    )
    db_session.add(reply)
    await db_session.commit()
    await db_session.refresh(reply)

    assert reply.parent_id == parent.id


@pytest.mark.asyncio
async def test_mensaje_tenant_id_not_null(db_session, tenant):
    auth = AuthUser(tenant_id=tenant.id, email="d@test.com", password_hash="x")
    db_session.add(auth)
    await db_session.commit()
    await db_session.refresh(auth)
    u = Usuario(id=auth.id, tenant_id=tenant.id, nombre="D", apellidos="E")
    db_session.add(u)
    await db_session.commit()

    msg = Mensaje(tenant_id=tenant.id, sender_id=u.id, recipient_id=u.id, asunto="T", cuerpo="B")
    db_session.add(msg)
    await db_session.commit()

    assert msg.tenant_id is not None
    assert msg.tenant_id == tenant.id


@pytest.mark.asyncio
async def test_mensaje_soft_delete(db_session, tenant):
    auth = AuthUser(tenant_id=tenant.id, email="e@test.com", password_hash="x")
    db_session.add(auth)
    await db_session.commit()
    await db_session.refresh(auth)
    u = Usuario(id=auth.id, tenant_id=tenant.id, nombre="E", apellidos="F")
    db_session.add(u)
    await db_session.commit()

    msg = Mensaje(tenant_id=tenant.id, sender_id=u.id, recipient_id=u.id, asunto="Soft", cuerpo="Delete")
    db_session.add(msg)
    await db_session.commit()
    await db_session.refresh(msg)

    assert msg.deleted_at is None
    msg.deleted_at = datetime.now(timezone.utc)
    await db_session.commit()
    await db_session.refresh(msg)
    assert msg.deleted_at is not None
