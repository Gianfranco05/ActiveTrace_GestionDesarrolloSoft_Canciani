"""TDD: GuardiaService tests."""

import uuid

import pytest

from app.models.guardia import Guardia
from app.repositories.audit_repository import AuditLogRepository
from app.schemas.guardias import DiaSemana, EstadoGuardia, GuardiaCreateRequest, GuardiaUpdateRequest
from app.services.audit_service import AuditService
from app.services.guardia_service import GuardiaService
from tests.helpers_encuentros import create_asignacion_chain


@pytest.fixture
def audit_svc(db_session, tenant):
    repo = AuditLogRepository(db_session, tenant.id)
    return AuditService(db_session, repo)


@pytest.mark.asyncio
async def test_registrar_guardia_crea_con_estado_pendiente(db_session, tenant, audit_svc):
    a, m, c, coh = await create_asignacion_chain(db_session, tenant)
    svc = GuardiaService(db_session, tenant.id, audit_svc)

    req = GuardiaCreateRequest(
        asignacion_id=a.id, materia_id=m.id,
        carrera_id=c.id, cohorte_id=coh.id,
        dia=DiaSemana.LUNES, horario="14:00–14:45",
        comentarios="Consulta",
    )
    guardia = await svc.registrar_guardia(req, a.usuario_id, ["TUTOR"])
    assert guardia.id is not None
    assert guardia.estado == "Pendiente"


@pytest.mark.asyncio
async def test_tutor_no_puede_registrar_guardia_ajena(db_session, tenant, audit_svc):
    a, m, c, coh = await create_asignacion_chain(db_session, tenant)
    svc = GuardiaService(db_session, tenant.id, audit_svc)

    req = GuardiaCreateRequest(
        asignacion_id=a.id, materia_id=m.id,
        carrera_id=c.id, cohorte_id=coh.id,
        dia=DiaSemana.LUNES, horario="14:00–14:45",
    )
    from fastapi import HTTPException
    with pytest.raises(HTTPException) as exc:
        await svc.registrar_guardia(req, uuid.uuid4(), ["TUTOR"])
    assert exc.value.status_code == 403


@pytest.mark.asyncio
async def test_coordinador_puede_registrar_para_cualquiera(db_session, tenant, audit_svc):
    a, m, c, coh = await create_asignacion_chain(db_session, tenant)
    from app.models.auth_user import AuthUser
    user = AuthUser(tenant_id=tenant.id, email=f"coord_{uuid.uuid4().hex[:6]}@t.com", password_hash="x")
    db_session.add(user)
    await db_session.flush()

    svc = GuardiaService(db_session, tenant.id, audit_svc)

    req = GuardiaCreateRequest(
        asignacion_id=a.id, materia_id=m.id,
        carrera_id=c.id, cohorte_id=coh.id,
        dia=DiaSemana.VIERNES, horario="16:00–17:00",
    )
    guardia = await svc.registrar_guardia(req, user.id, ["COORDINADOR"])
    assert guardia.estado == "Pendiente"


@pytest.mark.asyncio
async def test_editar_guardia_audit(db_session, tenant, audit_svc):
    a, m, c, coh = await create_asignacion_chain(db_session, tenant)
    g = Guardia(
        tenant_id=tenant.id, asignacion_id=a.id, materia_id=m.id,
        carrera_id=c.id, cohorte_id=coh.id,
        dia="Lunes", horario="14:00–14:45",
    )
    db_session.add(g)
    await db_session.commit()
    await db_session.refresh(g)

    svc = GuardiaService(db_session, tenant.id, audit_svc)
    req = GuardiaUpdateRequest(estado=EstadoGuardia.REALIZADA)
    updated = await svc.editar_guardia(g.id, req, a.usuario_id, ["TUTOR"])
    assert updated.estado == "Realizada"


@pytest.mark.asyncio
async def test_listar_guardias_scope_tutor(db_session, tenant, audit_svc):
    a1, m1, c1, coh1 = await create_asignacion_chain(db_session, tenant)
    a2, m2, c2, coh2 = await create_asignacion_chain(db_session, tenant)

    g1 = Guardia(
        tenant_id=tenant.id, asignacion_id=a1.id, materia_id=m1.id,
        carrera_id=c1.id, cohorte_id=coh1.id,
        dia="Lunes", horario="14:00–14:45",
    )
    g2 = Guardia(
        tenant_id=tenant.id, asignacion_id=a2.id, materia_id=m2.id,
        carrera_id=c2.id, cohorte_id=coh2.id,
        dia="Martes", horario="10:00–10:45",
    )
    db_session.add_all([g1, g2])
    await db_session.commit()

    svc = GuardiaService(db_session, tenant.id, audit_svc)
    items, total = await svc.listar_guardias(
        {}, a1.usuario_id, tenant.id, ["TUTOR"],
    )
    assert total == 1


@pytest.mark.asyncio
async def test_listar_guardias_scope_coordinador(db_session, tenant, audit_svc):
    a1, m1, c1, coh1 = await create_asignacion_chain(db_session, tenant)
    a2, m2, c2, coh2 = await create_asignacion_chain(db_session, tenant)

    g1 = Guardia(
        tenant_id=tenant.id, asignacion_id=a1.id, materia_id=m1.id,
        carrera_id=c1.id, cohorte_id=coh1.id,
        dia="Lunes", horario="14:00–14:45",
    )
    g2 = Guardia(
        tenant_id=tenant.id, asignacion_id=a2.id, materia_id=m2.id,
        carrera_id=c2.id, cohorte_id=coh2.id,
        dia="Martes", horario="10:00–10:45",
    )
    db_session.add_all([g1, g2])
    await db_session.commit()

    svc = GuardiaService(db_session, tenant.id, audit_svc)
    items, total = await svc.listar_guardias(
        {}, uuid.uuid4(), tenant.id, ["COORDINADOR"],
    )
    assert total == 2


@pytest.mark.asyncio
async def test_exportar_csv_tiene_headers(db_session, tenant, audit_svc):
    svc = GuardiaService(db_session, tenant.id, audit_svc)
    csv_data = await svc.exportar_guardias(
        {}, uuid.uuid4(), tenant.id, ["COORDINADOR"],
    )
    assert "id,materia,carrera,cohorte,dia,horario,estado,comentarios,creada_at,tutor" in csv_data


@pytest.mark.asyncio
async def test_exportar_csv_con_datos(db_session, tenant, audit_svc):
    a, m, c, coh = await create_asignacion_chain(db_session, tenant)
    g = Guardia(
        tenant_id=tenant.id, asignacion_id=a.id, materia_id=m.id,
        carrera_id=c.id, cohorte_id=coh.id,
        dia="Lunes", horario="14:00–14:45",
    )
    db_session.add(g)
    await db_session.commit()

    svc = GuardiaService(db_session, tenant.id, audit_svc)
    csv_data = await svc.exportar_guardias(
        {}, uuid.uuid4(), tenant.id, ["COORDINADOR"],
    )
    lines = csv_data.strip().split("\n")
    assert len(lines) >= 2
