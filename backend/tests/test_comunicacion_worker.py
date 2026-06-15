"""TDD: ComunicacionWorker tests — startup recovery, polling, processing."""

import uuid
from datetime import datetime, timedelta, timezone

import pytest

from app.models.auth_user import AuthUser
from app.models.comunicacion import Comunicacion, EstadoComunicacion
from app.models.usuario import Usuario
from app.workers.comunicacion_worker import ComunicacionWorker
from app.integrations.email_sender import MockEmailSender


async def _create_user(db_session, tenant):
    au = AuthUser(tenant_id=tenant.id, email="wk@test.com", password_hash="hash")
    db_session.add(au)
    await db_session.commit()
    await db_session.refresh(au)
    u = Usuario(id=au.id, tenant_id=tenant.id, nombre="Wk", apellidos="Test")
    db_session.add(u)
    await db_session.commit()
    await db_session.refresh(u)
    return u


@pytest.mark.asyncio
async def test_startup_recovery_resets_stuck_enviando(db_session, tenant):
    old = datetime.now(timezone.utc) - timedelta(hours=2)
    c = Comunicacion(
        tenant_id=tenant.id, lote_id=uuid.uuid4(),
        destinatario="a@t.com", asunto="A", cuerpo="A",
        estado=EstadoComunicacion.ENVIANDO.value,
        updated_at=old,
    )
    db_session.add(c)
    await db_session.commit()

    worker = ComunicacionWorker(None)
    recovered = await worker.startup_recovery(db_session)
    assert recovered == 1

    await db_session.refresh(c)
    assert c.estado == EstadoComunicacion.PENDIENTE.value
    assert c.error_detalle == "Recovered from stuck Enviando state"


@pytest.mark.asyncio
async def test_startup_recovery_ignores_recent_enviando(db_session, tenant):
    recent = datetime.now(timezone.utc)
    c = Comunicacion(
        tenant_id=tenant.id, lote_id=uuid.uuid4(),
        destinatario="a@t.com", asunto="A", cuerpo="A",
        estado=EstadoComunicacion.ENVIANDO.value,
        updated_at=recent,
    )
    db_session.add(c)
    await db_session.commit()

    worker = ComunicacionWorker(None)
    recovered = await worker.startup_recovery(db_session)
    assert recovered == 0


@pytest.mark.asyncio
async def test_startup_recovery_ignores_pendiente(db_session, tenant):
    old = datetime.now(timezone.utc) - timedelta(hours=2)
    c = Comunicacion(
        tenant_id=tenant.id, lote_id=uuid.uuid4(),
        destinatario="a@t.com", asunto="A", cuerpo="A",
        estado=EstadoComunicacion.PENDIENTE.value,
        updated_at=old,
    )
    db_session.add(c)
    await db_session.commit()

    worker = ComunicacionWorker(None)
    recovered = await worker.startup_recovery(db_session)
    assert recovered == 0


@pytest.mark.asyncio
async def test_poll_once_processes_pendiente_without_aprobacion(db_session, tenant):
    c = Comunicacion(
        tenant_id=tenant.id, lote_id=uuid.uuid4(),
        destinatario="a@t.com", asunto="A", cuerpo="A",
        estado=EstadoComunicacion.PENDIENTE.value,
        requiere_aprobacion=False,
    )
    db_session.add(c)
    await db_session.commit()

    sender = MockEmailSender(failure_rate=0.0)
    worker = ComunicacionWorker(None, email_sender=sender)
    processed = await worker.poll_once(db_session)
    assert processed == 1
    assert len(sender._sent) == 1


@pytest.mark.asyncio
async def test_poll_once_skips_pendiente_requiring_aprobacion(db_session, tenant):
    c = Comunicacion(
        tenant_id=tenant.id, lote_id=uuid.uuid4(),
        destinatario="a@t.com", asunto="A", cuerpo="A",
        estado=EstadoComunicacion.PENDIENTE.value,
        requiere_aprobacion=True,
    )
    db_session.add(c)
    await db_session.commit()

    worker = ComunicacionWorker(None)
    processed = await worker.poll_once(db_session)
    assert processed == 0


@pytest.mark.asyncio
async def test_poll_once_processes_approved_pendiente(db_session, tenant):
    user = await _create_user(db_session, tenant)
    c = Comunicacion(
        tenant_id=tenant.id, lote_id=uuid.uuid4(),
        destinatario="a@t.com", asunto="A", cuerpo="A",
        estado=EstadoComunicacion.PENDIENTE.value,
        requiere_aprobacion=True,
        aprobado_por=user.id,
    )
    db_session.add(c)
    await db_session.commit()
    await db_session.refresh(c)

    sender = MockEmailSender(failure_rate=0.0)
    worker = ComunicacionWorker(None, email_sender=sender)
    processed = await worker.poll_once(db_session)
    assert processed == 1


@pytest.mark.asyncio
async def test_process_record_marks_enviado_on_success(db_session, tenant):
    c = Comunicacion(
        tenant_id=tenant.id, lote_id=uuid.uuid4(),
        destinatario="a@t.com", asunto="A", cuerpo="A",
        estado=EstadoComunicacion.PENDIENTE.value,
    )
    db_session.add(c)
    await db_session.commit()

    sender = MockEmailSender(failure_rate=0.0)
    worker = ComunicacionWorker(None, email_sender=sender)
    await worker._process_record(db_session, c)

    assert c.estado == EstadoComunicacion.ENVIADO.value
    assert c.enviado_at is not None
    assert len(sender._sent) == 1


@pytest.mark.asyncio
async def test_process_record_marks_error_on_failure(db_session, tenant):
    c = Comunicacion(
        tenant_id=tenant.id, lote_id=uuid.uuid4(),
        destinatario="a@t.com", asunto="A", cuerpo="A",
        estado=EstadoComunicacion.PENDIENTE.value,
    )
    db_session.add(c)
    await db_session.commit()

    sender = MockEmailSender(failure_rate=1.0)
    worker = ComunicacionWorker(None, email_sender=sender)
    await worker._process_record(db_session, c)

    assert c.estado == EstadoComunicacion.ERROR.value
    assert c.error_detalle == "Email send failed"


@pytest.mark.asyncio
async def test_mock_email_sender_tracks_sent():
    sender = MockEmailSender()
    ok = await sender.send("a@t.com", "S", "Body")
    assert ok is True
    assert sender._sent == [("a@t.com", "S", "Body")]


@pytest.mark.asyncio
async def test_mock_email_sender_failure():
    sender = MockEmailSender(failure_rate=1.0)
    ok = await sender.send("a@t.com", "S", "Body")
    assert ok is False
