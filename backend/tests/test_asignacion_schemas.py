"""Tests for Asignacion schemas."""

import uuid
from datetime import date

import pytest
from pydantic import ValidationError

from app.schemas.asignaciones import (
    AsignacionCreate,
    AsignacionUpdate,
    AsignacionResponse,
)


def test_asignacion_create_valid():
    data = AsignacionCreate(
        usuario_id=uuid.uuid4(),
        rol_id=uuid.uuid4(),
        vig_desde=date(2026, 1, 1),
    )
    assert data.usuario_id is not None
    assert data.rol_id is not None
    assert data.vig_desde == date(2026, 1, 1)
    assert data.vig_hasta is None


def test_asignacion_create_rejects_extra():
    with pytest.raises(ValidationError):
        AsignacionCreate(
            usuario_id=uuid.uuid4(),
            rol_id=uuid.uuid4(),
            vig_desde=date(2026, 1, 1),
            extra_field="bad",
        )


def test_asignacion_response_includes_estado_vigencia():
    data = dict(
        id=uuid.uuid4(),
        tenant_id=uuid.uuid4(),
        usuario_id=uuid.uuid4(),
        rol_id=uuid.uuid4(),
        materia_id=None,
        carrera_id=None,
        cohorte_id=None,
        comisiones=None,
        responsable_id=None,
        vig_desde=date(2020, 1, 1),
        vig_hasta=None,
        estado_vigencia="Vigente",
        created_at="2026-01-01T00:00:00",
        updated_at="2026-01-01T00:00:00",
    )
    resp = AsignacionResponse(**data)
    assert resp.estado_vigencia == "Vigente"


def test_asignacion_response_vencida():
    from datetime import timedelta

    data = dict(
        id=uuid.uuid4(),
        tenant_id=uuid.uuid4(),
        usuario_id=uuid.uuid4(),
        rol_id=uuid.uuid4(),
        materia_id=None,
        carrera_id=None,
        cohorte_id=None,
        comisiones=None,
        responsable_id=None,
        vig_desde=date(2020, 1, 1),
        vig_hasta=date.today() - timedelta(days=1),
        estado_vigencia="Vencida",
        created_at="2026-01-01T00:00:00",
        updated_at="2026-01-01T00:00:00",
    )
    resp = AsignacionResponse(**data)
    assert resp.estado_vigencia == "Vencida"


def test_asignacion_update_all_optional():
    data = AsignacionUpdate()
    assert data.model_dump(exclude_unset=True) == {}


def test_asignacion_response_from_dict_rejects_extra():
    data = {
        "id": uuid.uuid4(),
        "tenant_id": uuid.uuid4(),
        "usuario_id": uuid.uuid4(),
        "rol_id": uuid.uuid4(),
        "materia_id": None,
        "carrera_id": None,
        "cohorte_id": None,
        "comisiones": None,
        "responsable_id": None,
        "vig_desde": date(2026, 1, 1),
        "vig_hasta": None,
        "estado_vigencia": "Vigente",
        "created_at": "2026-01-01T00:00:00",
        "updated_at": "2026-01-01T00:00:00",
        "extra_field": "bad",
    }
    with pytest.raises(ValidationError):
        AsignacionResponse(**data)
