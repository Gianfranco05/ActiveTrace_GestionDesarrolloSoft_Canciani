import uuid

import pytest

from app.models.auth_user import AuthUser
from app.models.mensaje import Mensaje
from app.models.usuario import Usuario


async def _create_user(db_session, tenant, email, nombre):
    auth = AuthUser(tenant_id=tenant.id, email=email, password_hash="x")
    db_session.add(auth)
    await db_session.commit()
    await db_session.refresh(auth)
    u = Usuario(id=auth.id, tenant_id=tenant.id, nombre=nombre, apellidos="Test")
    db_session.add(u)
    await db_session.commit()
    return u


@pytest.mark.asyncio
async def test_create_mensaje_persists(db_session, tenant):
    u = await _create_user(db_session, tenant, "repo1@test.com", "User1")

    from app.repositories.mensaje_repository import MensajeRepository
    repo = MensajeRepository(db_session, tenant.id)
    msg = Mensaje(tenant_id=tenant.id, sender_id=u.id, recipient_id=u.id, asunto="A", cuerpo="B")
    result = await repo.create(msg)
    assert result.id is not None
    assert result.created_at is not None


@pytest.mark.asyncio
async def test_get_threads_for_user_returns_only_roots(db_session, tenant):
    u1 = await _create_user(db_session, tenant, "threads1@test.com", "Sender")
    u2 = await _create_user(db_session, tenant, "threads2@test.com", "Recipient")

    from app.repositories.mensaje_repository import MensajeRepository
    repo = MensajeRepository(db_session, tenant.id)

    root = Mensaje(tenant_id=tenant.id, sender_id=u1.id, recipient_id=u2.id, asunto="Thread 1", cuerpo="Body")
    await repo.create(root)

    reply = Mensaje(
        tenant_id=tenant.id, sender_id=u2.id, recipient_id=u1.id,
        parent_id=root.id, asunto="Re: Thread 1", cuerpo="Reply",
    )
    await repo.create(reply)

    threads, total = await repo.get_threads_for_user(u2.id, tenant.id, 0, 20)
    assert total == 1
    assert len(threads) == 1
    assert threads[0]["thread_id"] == root.id


@pytest.mark.asyncio
async def test_get_threads_for_user_tenant_isolation(db_session, tenant):
    u = await _create_user(db_session, tenant, "iso1@test.com", "User")

    from app.repositories.mensaje_repository import MensajeRepository
    repo = MensajeRepository(db_session, tenant.id)
    root = Mensaje(tenant_id=tenant.id, sender_id=u.id, recipient_id=u.id, asunto="T", cuerpo="B")
    await repo.create(root)

    other_tenant = uuid.uuid4()
    threads, total = await repo.get_threads_for_user(u.id, other_tenant, 0, 20)
    assert total == 0
    assert len(threads) == 0


@pytest.mark.asyncio
async def test_get_threads_pagination(db_session, tenant):
    u1 = await _create_user(db_session, tenant, "page1@test.com", "S")
    u2 = await _create_user(db_session, tenant, "page2@test.com", "R")

    from app.repositories.mensaje_repository import MensajeRepository
    repo = MensajeRepository(db_session, tenant.id)

    for i in range(5):
        root = Mensaje(tenant_id=tenant.id, sender_id=u1.id, recipient_id=u2.id, asunto=f"T{i}", cuerpo="B")
        await repo.create(root)

    threads, total = await repo.get_threads_for_user(u2.id, tenant.id, 0, 2)
    assert total == 5
    assert len(threads) == 2


@pytest.mark.asyncio
async def test_get_thread_detail_includes_replies(db_session, tenant):
    u1 = await _create_user(db_session, tenant, "det1@test.com", "S")
    u2 = await _create_user(db_session, tenant, "det2@test.com", "R")

    from app.repositories.mensaje_repository import MensajeRepository
    repo = MensajeRepository(db_session, tenant.id)

    root = Mensaje(tenant_id=tenant.id, sender_id=u1.id, recipient_id=u2.id, asunto="Root", cuerpo="Root body")
    await repo.create(root)

    reply = Mensaje(
        tenant_id=tenant.id, sender_id=u2.id, recipient_id=u1.id,
        parent_id=root.id, asunto="Re: Root", cuerpo="Reply body",
    )
    await repo.create(reply)

    root_msg, replies = await repo.get_thread_detail(root.id, tenant.id)
    assert root_msg is not None
    assert root_msg.id == root.id
    assert len(replies) == 1
    assert replies[0].id == reply.id


@pytest.mark.asyncio
async def test_get_thread_detail_ordered_asc(db_session, tenant):
    u1 = await _create_user(db_session, tenant, "ord1@test.com", "S")
    u2 = await _create_user(db_session, tenant, "ord2@test.com", "R")

    from app.repositories.mensaje_repository import MensajeRepository
    repo = MensajeRepository(db_session, tenant.id)

    root = Mensaje(tenant_id=tenant.id, sender_id=u1.id, recipient_id=u2.id, asunto="R", cuerpo="B")
    await repo.create(root)

    reply1 = Mensaje(
        tenant_id=tenant.id, sender_id=u2.id, recipient_id=u1.id,
        parent_id=root.id, asunto="Re", cuerpo="First reply",
    )
    await repo.create(reply1)

    reply2 = Mensaje(
        tenant_id=tenant.id, sender_id=u1.id, recipient_id=u2.id,
        parent_id=root.id, asunto="Re", cuerpo="Second reply",
    )
    await repo.create(reply2)

    _, replies = await repo.get_thread_detail(root.id, tenant.id)
    assert replies[0].id == reply1.id
    assert replies[1].id == reply2.id


@pytest.mark.asyncio
async def test_mark_as_read_sets_timestamp(db_session, tenant):
    u = await _create_user(db_session, tenant, "read1@test.com", "U")

    from app.repositories.mensaje_repository import MensajeRepository
    repo = MensajeRepository(db_session, tenant.id)

    msg = Mensaje(tenant_id=tenant.id, sender_id=u.id, recipient_id=u.id, asunto="T", cuerpo="B")
    await repo.create(msg)
    assert msg.leido is False
    assert msg.leido_at is None

    await repo.mark_as_read(msg.id, tenant.id)
    await db_session.refresh(msg)
    assert msg.leido is True
    assert msg.leido_at is not None


@pytest.mark.asyncio
async def test_mark_thread_as_read_only_recipient(db_session, tenant):
    u1 = await _create_user(db_session, tenant, "mr1@test.com", "S")
    u2 = await _create_user(db_session, tenant, "mr2@test.com", "R")

    from app.repositories.mensaje_repository import MensajeRepository
    repo = MensajeRepository(db_session, tenant.id)

    root = Mensaje(tenant_id=tenant.id, sender_id=u1.id, recipient_id=u2.id, asunto="Thread", cuerpo="Root")
    await repo.create(root)

    reply = Mensaje(
        tenant_id=tenant.id, sender_id=u1.id, recipient_id=u2.id,
        parent_id=root.id, asunto="Re", cuerpo="Reply",
    )
    await repo.create(reply)

    await repo.mark_thread_as_read(root.id, u2.id, tenant.id)
    await db_session.refresh(root)
    await db_session.refresh(reply)

    assert root.leido is True
    assert reply.leido is True


@pytest.mark.asyncio
async def test_mark_thread_as_read_does_not_affect_sender(db_session, tenant):
    u1 = await _create_user(db_session, tenant, "ms1@test.com", "S")
    u2 = await _create_user(db_session, tenant, "ms2@test.com", "R")

    from app.repositories.mensaje_repository import MensajeRepository
    repo = MensajeRepository(db_session, tenant.id)

    root = Mensaje(tenant_id=tenant.id, sender_id=u1.id, recipient_id=u2.id, asunto="Thread", cuerpo="Root")
    await repo.create(root)

    reply = Mensaje(
        tenant_id=tenant.id, sender_id=u2.id, recipient_id=u1.id,
        parent_id=root.id, asunto="Re", cuerpo="Reply",
    )
    await repo.create(reply)

    await repo.mark_thread_as_read(root.id, u2.id, tenant.id)
    await db_session.refresh(reply)

    assert reply.leido is False
