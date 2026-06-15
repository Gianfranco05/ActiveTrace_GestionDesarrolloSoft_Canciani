"""TDD: Schema validation tests for encuentros."""

from datetime import date, time

import pytest
from pydantic import ValidationError

from app.schemas.encuentros import (
    DiaSemana,
    EstadoEncuentro,
    InstanciaUpdateRequest,
    InstanciaUnicaCreateRequest,
    SlotRecurrenteCreateRequest,
    SlotUnicoCreateRequest,
)


def test_slot_recurrente_rejects_missing_fields():
    with pytest.raises(ValidationError):
        SlotRecurrenteCreateRequest()


def test_slot_recurrente_rejects_extra_fields():
    with pytest.raises(ValidationError):
        SlotRecurrenteCreateRequest(
            materia_id="00000000-0000-0000-0000-000000000001",
            asignacion_id="00000000-0000-0000-0000-000000000002",
            titulo="Test",
            hora=time(14, 0),
            dia_semana=DiaSemana.LUNES,
            fecha_inicio=date(2026, 6, 8),
            cant_semanas=4,
            campo_inexistente="valor",
        )


def test_cant_semanas_min_1():
    with pytest.raises(ValidationError):
        SlotRecurrenteCreateRequest(
            materia_id="00000000-0000-0000-0000-000000000001",
            asignacion_id="00000000-0000-0000-0000-000000000002",
            titulo="Test",
            hora=time(14, 0),
            dia_semana=DiaSemana.LUNES,
            fecha_inicio=date(2026, 6, 8),
            cant_semanas=0,
        )


def test_cant_semanas_max_52():
    with pytest.raises(ValidationError):
        SlotRecurrenteCreateRequest(
            materia_id="00000000-0000-0000-0000-000000000001",
            asignacion_id="00000000-0000-0000-0000-000000000002",
            titulo="Test",
            hora=time(14, 0),
            dia_semana=DiaSemana.LUNES,
            fecha_inicio=date(2026, 6, 8),
            cant_semanas=53,
        )


def test_dia_semana_invalid():
    with pytest.raises(ValidationError):
        SlotRecurrenteCreateRequest(
            materia_id="00000000-0000-0000-0000-000000000001",
            asignacion_id="00000000-0000-0000-0000-000000000002",
            titulo="Test",
            hora=time(14, 0),
            dia_semana="InvalidDay",
            fecha_inicio=date(2026, 6, 8),
            cant_semanas=1,
        )


def test_instancia_update_partial():
    req = InstanciaUpdateRequest(estado=EstadoEncuentro.REALIZADO)
    assert req.estado == EstadoEncuentro.REALIZADO
    assert req.meet_url is None
    assert req.video_url is None


def test_instancia_update_rejects_invalid_estado():
    with pytest.raises(ValidationError):
        InstanciaUpdateRequest(estado="InvalidState")


def test_slot_unico_create_valid():
    req = SlotUnicoCreateRequest(
        materia_id="00000000-0000-0000-0000-000000000001",
        asignacion_id="00000000-0000-0000-0000-000000000002",
        titulo="Encuentro único",
        hora=time(10, 0),
        fecha_unica=date(2026, 7, 1),
        meet_url="https://meet.test.com/abc",
    )
    assert req.titulo == "Encuentro único"
    assert req.fecha_unica == date(2026, 7, 1)


def test_instancia_unica_create_optional_meet_url():
    req = InstanciaUnicaCreateRequest(
        materia_id="00000000-0000-0000-0000-000000000001",
        asignacion_id="00000000-0000-0000-0000-000000000002",
        titulo="Test",
        fecha=date(2026, 6, 8),
        hora=time(14, 0),
    )
    assert req.meet_url is None


def test_instancia_unica_create_rejects_extra_fields():
    with pytest.raises(ValidationError):
        InstanciaUnicaCreateRequest(
            materia_id="00000000-0000-0000-0000-000000000001",
            asignacion_id="00000000-0000-0000-0000-000000000002",
            titulo="Test",
            fecha=date(2026, 6, 8),
            hora=time(14, 0),
            extra_field=True,
        )
