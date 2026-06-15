import uuid

import pytest

from app.core.audit_codes import AuditAction
from app.models.auth_user import AuthUser
from app.models.mensaje import Mensaje
from app.models.usuario import Usuario
from app.schemas.mensajes import MensajeCreateRequest, MensajeReplyRequest


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
async def test_enviar_mensaje_crea_raiz(db_session, tenant):
    sender = await _create_user(db_session, tenant, "svc1@test.com", "Sender")
    recip = await _create_user(db_session, tenant, "svc2@test.com", "Recipient")

    from app.services.mensaje_service import MensajeService
    svc = MensajeService(db_session, tenant.id)
    req = MensajeCreateRequest(recipient_id=recip.id, asunto="Hola", cuerpo="Mensaje de prueba")
    result = await svc.enviar_mensaje(sender.id, tenant.id, req)

    assert result.parent_id is None
    assert result.asunto == "Hola"
    assert result.cuerpo == "Mensaje de prueba"
    assert result.sender_id == sender.id
    assert result.recipient_id == recip.id
    assert result.leido is False


@pytest.mark.asyncio
async def test_enviar_mensaje_recipient_no_existe_404(db_session, tenant):
    sender = await _create_user(db_session, tenant, "svc3@test.com", "Sender")

    from app.services.mensaje_service import MensajeService
    svc = MensajeService(db_session, tenant.id)
    req = MensajeCreateRequest(recipient_id=uuid.uuid4(), asunto="H", cuerpo="C")

    from fastapi import HTTPException
    with pytest.raises(HTTPException) as exc:
        await svc.enviar_mensaje(sender.id, tenant.id, req)
    assert exc.value.status_code == 404


@pytest.mark.asyncio
async def test_enviar_mensaje_audit(db_session, tenant):
    sender = await _create_user(db_session, tenant, "svc_audit@test.com", "Sender")
    recip = await _create_user(db_session, tenant, "svc_audit2@test.com", "Recipient")

    from app.repositories.audit_repository import AuditLogRepository
    from app.services.audit_service import AuditService
    from app.services.mensaje_service import MensajeService

    audit_repo = AuditLogRepository(db_session, tenant.id)
    audit_svc = AuditService(db_session, audit_repo)
    svc = MensajeService(db_session, tenant.id, audit_svc)
    req = MensajeCreateRequest(recipient_id=recip.id, asunto="Audit", cuerpo="Test audit")
    await svc.enviar_mensaje(sender.id, tenant.id, req)

    logs = await audit_repo.list(accion=AuditAction.MENSAJE_ENVIAR.value, limit=5)
    assert len(logs) == 1
    assert logs[0].actor_id == sender.id


@pytest.mark.asyncio
async def test_listar_inbox_solo_hilos_propios(db_session, tenant):
    u1 = await _create_user(db_session, tenant, "svc_inbox1@test.com", "A")
    u2 = await _create_user(db_session, tenant, "svc_inbox2@test.com", "B")
    u3 = await _create_user(db_session, tenant, "svc_inbox3@test.com", "C")

    from app.services.mensaje_service import MensajeService
    svc = MensajeService(db_session, tenant.id)

    req = MensajeCreateRequest(recipient_id=u2.id, asunto="Para B", cuerpo="Mensaje para B")
    await svc.enviar_mensaje(u1.id, tenant.id, req)

    req2 = MensajeCreateRequest(recipient_id=u3.id, asunto="Para C", cuerpo="Mensaje para C")
    await svc.enviar_mensaje(u1.id, tenant.id, req2)

    result = await svc.listar_inbox(u2.id, tenant.id, 0, 20)
    assert result["total"] == 1


@pytest.mark.asyncio
async def test_inbox_ordenado_por_actividad(db_session, tenant):
    u1 = await _create_user(db_session, tenant, "svc_ord1@test.com", "A")
    u2 = await _create_user(db_session, tenant, "svc_ord2@test.com", "B")

    from app.services.mensaje_service import MensajeService
    svc = MensajeService(db_session, tenant.id)

    req1 = MensajeCreateRequest(recipient_id=u2.id, asunto="Primero", cuerpo="C")
    await svc.enviar_mensaje(u1.id, tenant.id, req1)

    req2 = MensajeCreateRequest(recipient_id=u2.id, asunto="Segundo", cuerpo="C")
    await svc.enviar_mensaje(u1.id, tenant.id, req2)

    result = await svc.listar_inbox(u2.id, tenant.id, 0, 20)
    assert result["items"][0].asunto == "Segundo"


@pytest.mark.asyncio
async def test_inbox_thread_con_unread_count(db_session, tenant):
    u1 = await _create_user(db_session, tenant, "svc_unread1@test.com", "A")
    u2 = await _create_user(db_session, tenant, "svc_unread2@test.com", "B")

    from app.services.mensaje_service import MensajeService
    svc = MensajeService(db_session, tenant.id)

    req = MensajeCreateRequest(recipient_id=u2.id, asunto="Unread", cuerpo="C")
    await svc.enviar_mensaje(u1.id, tenant.id, req)

    result = await svc.listar_inbox(u2.id, tenant.id, 0, 20)
    assert result["items"][0].unread_count == 1


@pytest.mark.asyncio
async def test_ver_hilo_marca_como_leido(db_session, tenant):
    u1 = await _create_user(db_session, tenant, "svc_leido1@test.com", "A")
    u2 = await _create_user(db_session, tenant, "svc_leido2@test.com", "B")

    from app.services.mensaje_service import MensajeService
    svc = MensajeService(db_session, tenant.id)

    req = MensajeCreateRequest(recipient_id=u2.id, asunto="Leido", cuerpo="C")
    sent = await svc.enviar_mensaje(u1.id, tenant.id, req)

    msg_id = sent.id if hasattr(sent, 'id') else sent["id"]
    detail = await svc.ver_hilo(msg_id, u2.id, tenant.id)
    assert detail.thread.leido is True


@pytest.mark.asyncio
async def test_ver_hilo_incluye_respuestas(db_session, tenant):
    u1 = await _create_user(db_session, tenant, "svc_resp1@test.com", "A")
    u2 = await _create_user(db_session, tenant, "svc_resp2@test.com", "B")

    from app.services.mensaje_service import MensajeService
    svc = MensajeService(db_session, tenant.id)

    req = MensajeCreateRequest(recipient_id=u2.id, asunto="Hilo", cuerpo="Root")
    sent = await svc.enviar_mensaje(u1.id, tenant.id, req)

    msg_id = sent.id if hasattr(sent, 'id') else sent["id"]
    reply_req = MensajeReplyRequest(cuerpo="Reply")
    await svc.responder(msg_id, u2.id, tenant.id, reply_req)

    detail = await svc.ver_hilo(msg_id, u2.id, tenant.id)
    assert len(detail.replies) == 1


@pytest.mark.asyncio
async def test_ver_hilo_ajeno_404(db_session, tenant):
    u1 = await _create_user(db_session, tenant, "svc_ajeno1@test.com", "A")
    u2 = await _create_user(db_session, tenant, "svc_ajeno2@test.com", "B")
    u3 = await _create_user(db_session, tenant, "svc_ajeno3@test.com", "C")

    from app.services.mensaje_service import MensajeService
    svc = MensajeService(db_session, tenant.id)

    req = MensajeCreateRequest(recipient_id=u2.id, asunto="Hilo", cuerpo="Root")
    sent = await svc.enviar_mensaje(u1.id, tenant.id, req)
    msg_id = sent.id if hasattr(sent, 'id') else sent["id"]

    from fastapi import HTTPException
    with pytest.raises(HTTPException) as exc:
        await svc.ver_hilo(msg_id, u3.id, tenant.id)
    assert exc.value.status_code == 404


@pytest.mark.asyncio
async def test_responder_en_hilo(db_session, tenant):
    u1 = await _create_user(db_session, tenant, "svc_r1@test.com", "A")
    u2 = await _create_user(db_session, tenant, "svc_r2@test.com", "B")

    from app.services.mensaje_service import MensajeService
    svc = MensajeService(db_session, tenant.id)

    req = MensajeCreateRequest(recipient_id=u2.id, asunto="Original", cuerpo="Root")
    sent = await svc.enviar_mensaje(u1.id, tenant.id, req)
    msg_id = sent.id if hasattr(sent, 'id') else sent["id"]

    reply_req = MensajeReplyRequest(cuerpo="Mi respuesta")
    result = await svc.responder(msg_id, u2.id, tenant.id, reply_req)

    assert result.parent_id == msg_id
    assert result.asunto == "Original"
    assert result.cuerpo == "Mi respuesta"
    assert result.sender_id == u2.id
    assert result.recipient_id == u1.id


@pytest.mark.asyncio
async def test_responder_hilo_no_existe_404(db_session, tenant):
    u1 = await _create_user(db_session, tenant, "svc_r3@test.com", "A")

    from app.services.mensaje_service import MensajeService
    svc = MensajeService(db_session, tenant.id)
    reply_req = MensajeReplyRequest(cuerpo="Reply")

    from fastapi import HTTPException
    with pytest.raises(HTTPException) as exc:
        await svc.responder(uuid.uuid4(), u1.id, tenant.id, reply_req)
    assert exc.value.status_code == 404


@pytest.mark.asyncio
async def test_responder_audit(db_session, tenant):
    u1 = await _create_user(db_session, tenant, "svc_raudit1@test.com", "A")
    u2 = await _create_user(db_session, tenant, "svc_raudit2@test.com", "B")

    from app.repositories.audit_repository import AuditLogRepository
    from app.services.audit_service import AuditService
    from app.services.mensaje_service import MensajeService

    audit_repo = AuditLogRepository(db_session, tenant.id)
    audit_svc = AuditService(db_session, audit_repo)
    svc = MensajeService(db_session, tenant.id, audit_svc)

    req = MensajeCreateRequest(recipient_id=u2.id, asunto="Audit", cuerpo="Root")
    sent = await svc.enviar_mensaje(u1.id, tenant.id, req)
    msg_id = sent.id if hasattr(sent, 'id') else sent["id"]

    reply_req = MensajeReplyRequest(cuerpo="Audit reply")
    await svc.responder(msg_id, u2.id, tenant.id, reply_req)

    logs = await audit_repo.list(accion=AuditAction.MENSAJE_ENVIAR.value, limit=10)
    assert len(logs) == 2


@pytest.mark.asyncio
async def test_inbox_tenant_isolation(db_session, tenant):
    u1 = await _create_user(db_session, tenant, "svc_iso1@test.com", "A")
    u2 = await _create_user(db_session, tenant, "svc_iso2@test.com", "B")

    from app.services.mensaje_service import MensajeService
    svc = MensajeService(db_session, tenant.id)

    req = MensajeCreateRequest(recipient_id=u2.id, asunto="Iso", cuerpo="C")
    await svc.enviar_mensaje(u1.id, tenant.id, req)

    other_tenant = uuid.uuid4()
    result = await svc.listar_inbox(u2.id, other_tenant, 0, 20)
    assert result["total"] == 0
