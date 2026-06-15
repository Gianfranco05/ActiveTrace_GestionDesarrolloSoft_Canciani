"""TDD: EncuentroService tests."""

import uuid
from datetime import date, time

import uuid

import pytest
from sqlalchemy import select

from app.models.instancia_encuentro import InstanciaEncuentro
from app.models.audit_log import AuditLog
from app.repositories.audit_repository import AuditLogRepository
from app.schemas.encuentros import (
    EstadoEncuentro,
    InstanciaUnicaCreateRequest,
    InstanciaUpdateRequest,
)
from app.services.audit_service import AuditService
from app.services.encuentro_service import EncuentroService
from tests.helpers_encuentros import create_asignacion_chain


@pytest.fixture
def audit_svc(db_session, tenant):
    repo = AuditLogRepository(db_session, tenant.id)
    return AuditService(db_session, repo)


@pytest.mark.asyncio
async def test_crear_instancia_unica(db_session, tenant, audit_svc):
    a, m, _, _ = await create_asignacion_chain(db_session, tenant)
    svc = EncuentroService(db_session, tenant.id, audit_svc)

    req = InstanciaUnicaCreateRequest(
        materia_id=m.id, asignacion_id=a.id,
        titulo="Clase ad-hoc", fecha=date(2026, 7, 15), hora=time(15, 0),
    )
    instancia = await svc.crear_instancia_unica(req, a.usuario_id)
    assert instancia.id is not None
    assert instancia.estado == "Programado"
    assert instancia.slot_id is None


@pytest.mark.asyncio
async def test_editar_instancia_cambia_estado(db_session, tenant, audit_svc):
    a, m, _, _ = await create_asignacion_chain(db_session, tenant)
    instancia = InstanciaEncuentro(
        tenant_id=tenant.id, materia_id=m.id, asignacion_id=a.id,
        fecha=date(2026, 6, 8), hora=time(14, 0), titulo="Test",
    )
    db_session.add(instancia)
    await db_session.commit()
    await db_session.refresh(instancia)

    svc = EncuentroService(db_session, tenant.id, audit_svc)
    req = InstanciaUpdateRequest(estado=EstadoEncuentro.REALIZADO)
    updated = await svc.editar_instancia(
        instancia.id, req, a.usuario_id, ["PROFESOR"],
    )
    assert updated.estado == "Realizado"


@pytest.mark.asyncio
async def test_editar_solo_campos_permitidos(db_session, tenant, audit_svc):
    a, m, _, _ = await create_asignacion_chain(db_session, tenant)
    instancia = InstanciaEncuentro(
        tenant_id=tenant.id, materia_id=m.id, asignacion_id=a.id,
        fecha=date(2026, 6, 8), hora=time(14, 0), titulo="Test",
    )
    db_session.add(instancia)
    await db_session.commit()
    await db_session.refresh(instancia)

    svc = EncuentroService(db_session, tenant.id, audit_svc)
    original_titulo = instancia.titulo
    req = InstanciaUpdateRequest(video_url="https://v.test", comentario="Grabado")
    updated = await svc.editar_instancia(
        instancia.id, req, a.usuario_id, ["PROFESOR"],
    )
    assert updated.titulo == original_titulo
    assert updated.video_url == "https://v.test"


@pytest.mark.asyncio
async def test_editar_instancia_ajena_profesor_403(db_session, tenant, audit_svc):
    a, m, _, _ = await create_asignacion_chain(db_session, tenant)
    instancia = InstanciaEncuentro(
        tenant_id=tenant.id, materia_id=m.id, asignacion_id=a.id,
        fecha=date(2026, 6, 8), hora=time(14, 0), titulo="Test",
    )
    db_session.add(instancia)
    await db_session.commit()
    await db_session.refresh(instancia)

    svc = EncuentroService(db_session, tenant.id, audit_svc)
    req = InstanciaUpdateRequest(estado=EstadoEncuentro.CANCELADO)
    from fastapi import HTTPException
    with pytest.raises(HTTPException) as exc:
        await svc.editar_instancia(instancia.id, req, uuid.uuid4(), ["PROFESOR"])
    assert exc.value.status_code == 403


@pytest.mark.asyncio
async def test_coordinador_puede_editar_cualquiera(db_session, tenant, audit_svc):
    a, m, _, _ = await create_asignacion_chain(db_session, tenant)
    from app.models.auth_user import AuthUser
    user = AuthUser(tenant_id=tenant.id, email=f"coord_{uuid.uuid4().hex[:6]}@t.com", password_hash="x")
    db_session.add(user)
    await db_session.flush()

    instancia = InstanciaEncuentro(
        tenant_id=tenant.id, materia_id=m.id, asignacion_id=a.id,
        fecha=date(2026, 6, 8), hora=time(14, 0), titulo="Test",
    )
    db_session.add(instancia)
    await db_session.commit()
    await db_session.refresh(instancia)

    svc = EncuentroService(db_session, tenant.id, audit_svc)
    req = InstanciaUpdateRequest(comentario="Coordinador update")
    updated = await svc.editar_instancia(
        instancia.id, req, user.id, ["COORDINADOR"],
    )
    assert updated.comentario == "Coordinador update"


@pytest.mark.asyncio
async def test_generar_html_incluye_todas_instancias(db_session, tenant, audit_svc):
    a, m, _, _ = await create_asignacion_chain(db_session, tenant)
    from app.models.slot_encuentro import SlotEncuentro
    from datetime import date as d, time as t
    slot = SlotEncuentro(
        tenant_id=tenant.id, asignacion_id=a.id, materia_id=m.id,
        titulo="HTML Slot", hora=t(14, 0),
    )
    db_session.add(slot)
    await db_session.flush()

    for i in range(2):
        db_session.add(InstanciaEncuentro(
            tenant_id=tenant.id, materia_id=m.id, asignacion_id=a.id,
            slot_id=slot.id, fecha=d(2026, 6, 8 + i), hora=t(14, 0),
            titulo=f"C{i}", estado="Programado",
        ))
    await db_session.commit()

    svc = EncuentroService(db_session, tenant.id, audit_svc)
    html = await svc.generar_html_slot(slot.id, tenant.id)
    assert html is not None
    assert "HTML Slot" in html
    assert "2026-06-08" in html
    assert "2026-06-09" in html
    assert "Programado" in html


@pytest.mark.asyncio
async def test_generar_html_canceladas_marcadas(db_session, tenant, audit_svc):
    a, m, _, _ = await create_asignacion_chain(db_session, tenant)
    from app.models.slot_encuentro import SlotEncuentro
    from datetime import date as d, time as t
    slot = SlotEncuentro(
        tenant_id=tenant.id, asignacion_id=a.id, materia_id=m.id,
        titulo="Cancel Slot", hora=t(14, 0),
    )
    db_session.add(slot)
    await db_session.flush()

    db_session.add(InstanciaEncuentro(
        tenant_id=tenant.id, materia_id=m.id, asignacion_id=a.id,
        slot_id=slot.id, fecha=d(2026, 6, 8), hora=t(14, 0),
        titulo="Cancelada", estado="Cancelado",
    ))
    await db_session.commit()

    svc = EncuentroService(db_session, tenant.id, audit_svc)
    html = await svc.generar_html_slot(slot.id, tenant.id)
    assert html is not None
    assert "Cancelado" in html


@pytest.mark.asyncio
async def test_generar_html_slot_no_existe(db_session, tenant, audit_svc):
    svc = EncuentroService(db_session, tenant.id, audit_svc)
    result = await svc.generar_html_slot(uuid.uuid4(), tenant.id)
    assert result is None
