"""TDD: SlotService tests."""

import uuid
from datetime import date, time

import pytest
from sqlalchemy import select

from app.models.slot_encuentro import SlotEncuentro
from app.models.instancia_encuentro import InstanciaEncuentro
from app.models.audit_log import AuditLog
from app.repositories.audit_repository import AuditLogRepository
from app.schemas.encuentros import DiaSemana, SlotRecurrenteCreateRequest, SlotUnicoCreateRequest
from app.services.audit_service import AuditService
from app.services.slot_service import SlotService, _calcular_fechas_instancias
from tests.helpers_encuentros import create_asignacion_chain


@pytest.fixture
def audit_svc(db_session, tenant):
    repo = AuditLogRepository(db_session, tenant.id)
    return AuditService(db_session, repo)


def test_calculo_fecha_inicio_lunes():
    fechas = _calcular_fechas_instancias("Lunes", date(2026, 6, 8), 4)
    assert len(fechas) == 4
    assert fechas[0] == date(2026, 6, 8)
    assert fechas[1] == date(2026, 6, 15)


def test_calculo_fecha_inicio_distinto_dia_semana():
    fechas = _calcular_fechas_instancias("Viernes", date(2026, 6, 8), 2)
    assert len(fechas) == 2
    assert fechas[0] == date(2026, 6, 12)


def test_cant_semanas_1_genera_1_instancia():
    fechas = _calcular_fechas_instancias("Lunes", date(2026, 6, 8), 1)
    assert len(fechas) == 1


@pytest.mark.asyncio
async def test_crear_slot_recurrente_genera_instancias(db_session, tenant, audit_svc):
    a, m, _, _ = await create_asignacion_chain(db_session, tenant)
    svc = SlotService(db_session, tenant.id, audit_svc)

    req = SlotRecurrenteCreateRequest(
        materia_id=m.id, asignacion_id=a.id,
        titulo="Clase", hora=time(14, 0),
        dia_semana=DiaSemana.LUNES,
        fecha_inicio=date(2026, 6, 8), cant_semanas=4,
    )
    slot = await svc.crear_slot_recurrente(req, a.usuario_id, ["PROFESOR"])
    assert slot is not None

    q = select(InstanciaEncuentro).where(InstanciaEncuentro.slot_id == slot.id)
    result = await db_session.execute(q)
    instancias = result.scalars().all()
    assert len(instancias) == 4
    for i in instancias:
        assert i.estado == "Programado"


@pytest.mark.asyncio
async def test_crear_slot_unico_genera_1_instancia(db_session, tenant, audit_svc):
    a, m, _, _ = await create_asignacion_chain(db_session, tenant)
    svc = SlotService(db_session, tenant.id, audit_svc)

    req = SlotUnicoCreateRequest(
        materia_id=m.id, asignacion_id=a.id,
        titulo="Clase única", hora=time(10, 0),
        fecha_unica=date(2026, 7, 1),
    )
    slot = await svc.crear_slot_unico(req, a.usuario_id, ["PROFESOR"])
    assert slot is not None

    q = select(InstanciaEncuentro).where(InstanciaEncuentro.slot_id == slot.id)
    result = await db_session.execute(q)
    instancias = result.scalars().all()
    assert len(instancias) == 1


@pytest.mark.asyncio
async def test_profesor_no_puede_usar_asignacion_ajena(db_session, tenant, audit_svc):
    a, m, _, _ = await create_asignacion_chain(db_session, tenant)
    svc = SlotService(db_session, tenant.id, audit_svc)

    req = SlotRecurrenteCreateRequest(
        materia_id=m.id, asignacion_id=a.id,
        titulo="Clase", hora=time(14, 0),
        dia_semana=DiaSemana.LUNES,
        fecha_inicio=date(2026, 6, 8), cant_semanas=2,
    )
    from fastapi import HTTPException
    with pytest.raises(HTTPException) as exc:
        await svc.crear_slot_recurrente(req, uuid.uuid4(), ["PROFESOR"])
    assert exc.value.status_code == 403


@pytest.mark.asyncio
async def test_soft_delete_no_borra_instancias(db_session, tenant, audit_svc):
    a, m, _, _ = await create_asignacion_chain(db_session, tenant)
    svc = SlotService(db_session, tenant.id, audit_svc)

    req = SlotUnicoCreateRequest(
        materia_id=m.id, asignacion_id=a.id,
        titulo="Delete test", hora=time(10, 0),
        fecha_unica=date(2026, 7, 1),
    )
    slot = await svc.crear_slot_unico(req, a.usuario_id, ["PROFESOR"])

    q_before = select(InstanciaEncuentro).where(InstanciaEncuentro.slot_id == slot.id)
    result_before = await db_session.execute(q_before)
    count_before = len(result_before.scalars().all())

    deleted = await svc.soft_delete_slot(slot.id, tenant.id, a.usuario_id)
    assert deleted is True

    q_after = select(InstanciaEncuentro).where(InstanciaEncuentro.slot_id == slot.id)
    result_after = await db_session.execute(q_after)
    count_after = len(result_after.scalars().all())
    assert count_after == count_before
