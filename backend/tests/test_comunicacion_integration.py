"""TDD: Comunicacion integration test — service + worker + repo E2E."""

import uuid
from datetime import date, datetime, timedelta, timezone

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.integrations.email_sender import MockEmailSender
from app.models.comunicacion import Comunicacion, EstadoComunicacion
from app.models.permiso import Permiso
from app.models.rol import Rol
from app.models.rol_permiso import RolPermiso
from app.models.asignacion import Asignacion
from app.models.auth_user import AuthUser
from app.models.usuario import Usuario
from app.models.padron import EntradaPadron, VersionPadron
from app.models.materia import Materia
from app.models.tenant import Tenant
from app.repositories.comunicacion_repository import ComunicacionRepository
from app.services.comunicacion_service import ComunicacionService
from app.workers.comunicacion_worker import ComunicacionWorker

pytestmark = pytest.mark.asyncio


async def _setup_padron(db_session, tenant, count=2):
    vp = VersionPadron(tenant_id=tenant.id, activa=True)
    db_session.add(vp)
    await db_session.flush()
    for i in range(count):
        db_session.add(EntradaPadron(
            tenant_id=tenant.id, version_id=vp.id,
            nombre=f"N{i}", apellidos=f"A{i}", email=f"s{i}@t.com",
        ))
    await db_session.commit()


async def _create_user(db_session, tenant):
    au = AuthUser(tenant_id=tenant.id, email="int@t.com", password_hash="x")
    db_session.add(au)
    await db_session.flush()
    u = Usuario(id=au.id, tenant_id=tenant.id, nombre="Int", apellidos="T")
    db_session.add(u)
    await db_session.flush()
    rol = Rol(nombre="INT_ROLE", tenant_id=tenant.id)
    db_session.add(rol)
    await db_session.flush()
    for codigo in ("comunicacion:enviar", "comunicacion:aprobar", "comunicacion:ver"):
        p = Permiso(codigo=codigo)
        db_session.add(p)
        await db_session.flush()
        db_session.add(RolPermiso(rol_id=rol.id, permiso_id=p.id))
    db_session.add(Asignacion(
        usuario_id=u.id, rol_id=rol.id,
        tenant_id=tenant.id, vig_desde=date.today(),
    ))
    await db_session.commit()
    return u


async def test_worker_sends_pending_messages(
    db_session: AsyncSession, tenant: Tenant,
):
    user = await _create_user(db_session, tenant)
    svc = ComunicacionService(db_session, tenant.id, user.id)
    await _setup_padron(db_session, tenant, count=2)
    materia = Materia(codigo="INT-MAT", nombre="Test", tenant_id=tenant.id)
    db_session.add(materia)
    await db_session.commit()

    preview = await svc.preview(
        materia_id=materia.id,
        cohorte_id=materia.id,
        template_body="Hola {{nombre}}",
        template_asunto="Test",
    )

    result = await svc.enqueue(
        preview_token=preview["preview_token"],
        preview_token_timestamp=preview["preview_token_timestamp"],
        materia_id=materia.id,
        cohorte_id=materia.id,
        template_body="Hola {{nombre}}",
        template_asunto="Test",
    )
    assert result["creados"] == 2

    sender = MockEmailSender(failure_rate=0.0)
    worker = ComunicacionWorker(session_factory=None, email_sender=sender)
    processed = await worker.poll_once(db_session)
    assert processed == 2


async def test_worker_handles_empty_queue(
    db_session: AsyncSession, tenant: Tenant,
):
    sender = MockEmailSender(failure_rate=0.0)
    worker = ComunicacionWorker(session_factory=None, email_sender=sender)
    processed = await worker.poll_once(db_session)
    assert processed == 0


async def test_worker_skips_requiere_aprobacion(
    db_session: AsyncSession, tenant: Tenant,
):
    repo = ComunicacionRepository(db_session, tenant.id)
    await repo.create({
        "destinatario": "test@t.com",
        "asunto": "S1",
        "cuerpo": "C1",
        "lote_id": uuid.uuid4(),
        "estado": EstadoComunicacion.PENDIENTE.value,
        "requiere_aprobacion": True,
    })
    await repo.create({
        "destinatario": "test2@t.com",
        "asunto": "S2",
        "cuerpo": "C2",
        "lote_id": uuid.uuid4(),
        "estado": EstadoComunicacion.PENDIENTE.value,
        "requiere_aprobacion": False,
    })

    sender = MockEmailSender(failure_rate=0.0)
    worker = ComunicacionWorker(session_factory=None, email_sender=sender)
    processed = await worker.poll_once(db_session)
    assert processed == 1


async def test_worker_recovery_sticks_stuck_records(
    db_session: AsyncSession, tenant: Tenant,
):
    repo = ComunicacionRepository(db_session, tenant.id)
    stuck = await repo.create({
        "destinatario": "stuck@t.com", "asunto": "S", "cuerpo": "C",
        "lote_id": uuid.uuid4(),
        "estado": EstadoComunicacion.ENVIANDO.value,
    })
    stuck.updated_at = datetime.now(timezone.utc) - timedelta(hours=2)
    await db_session.commit()

    sender = MockEmailSender(failure_rate=0.0)
    worker = ComunicacionWorker(session_factory=None, email_sender=sender)
    recovered = await worker.startup_recovery(db_session)
    assert recovered == 1

    processed = await worker.poll_once(db_session)
    assert processed == 1


async def test_full_e2e_service_to_worker(
    db_session: AsyncSession, tenant: Tenant,
):
    user = await _create_user(db_session, tenant)
    svc = ComunicacionService(db_session, tenant.id, user.id)
    await _setup_padron(db_session, tenant, count=1)
    materia = Materia(codigo="INT-MAT2", nombre="Test2", tenant_id=tenant.id)
    db_session.add(materia)
    await db_session.commit()

    preview = await svc.preview(
        materia_id=materia.id,
        cohorte_id=materia.id,
        template_body="Hola {{nombre}}",
        template_asunto="E2E",
    )

    enq = await svc.enqueue(
        preview_token=preview["preview_token"],
        preview_token_timestamp=preview["preview_token_timestamp"],
        materia_id=materia.id,
        cohorte_id=materia.id,
        template_body="Hola {{nombre}}",
        template_asunto="E2E",
    )
    assert enq["creados"] == 1

    sender = MockEmailSender(failure_rate=0.0)
    worker = ComunicacionWorker(session_factory=None, email_sender=sender)
    processed = await worker.poll_once(db_session)
    assert processed == 1

    repo = ComunicacionRepository(db_session, tenant.id)
    comps = await repo.list_filtered()
    assert len(comps) == 1
    assert comps[0].estado == EstadoComunicacion.ENVIADO.value
