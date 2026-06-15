"""TDD: Schema validation tests for guardias."""

import pytest
from pydantic import ValidationError

from app.schemas.guardias import (
    DiaSemana,
    EstadoGuardia,
    GuardiaCreateRequest,
    GuardiaUpdateRequest,
)


def test_guardia_create_rejects_missing_fields():
    with pytest.raises(ValidationError):
        GuardiaCreateRequest()


def test_guardia_create_rejects_extra_fields():
    with pytest.raises(ValidationError):
        GuardiaCreateRequest(
            asignacion_id="00000000-0000-0000-0000-000000000001",
            materia_id="00000000-0000-0000-0000-000000000002",
            carrera_id="00000000-0000-0000-0000-000000000003",
            cohorte_id="00000000-0000-0000-0000-000000000004",
            dia=DiaSemana.LUNES,
            horario="14:00–14:45",
            campo_extra=True,
        )


def test_dia_invalid():
    with pytest.raises(ValidationError):
        GuardiaCreateRequest(
            asignacion_id="00000000-0000-0000-0000-000000000001",
            materia_id="00000000-0000-0000-0000-000000000002",
            carrera_id="00000000-0000-0000-0000-000000000003",
            cohorte_id="00000000-0000-0000-0000-000000000004",
            dia="InvalidDay",
            horario="14:00–14:45",
        )


def test_guardia_update_partial():
    req = GuardiaUpdateRequest(estado=EstadoGuardia.REALIZADA)
    assert req.estado == EstadoGuardia.REALIZADA
    assert req.comentarios is None


def test_guardia_update_optional_comentarios():
    req = GuardiaUpdateRequest(comentarios="Actualizado")
    assert req.estado is None
    assert req.comentarios == "Actualizado"


def test_guardia_create_with_optional_comentarios():
    req = GuardiaCreateRequest(
        asignacion_id="00000000-0000-0000-0000-000000000001",
        materia_id="00000000-0000-0000-0000-000000000002",
        carrera_id="00000000-0000-0000-0000-000000000003",
        cohorte_id="00000000-0000-0000-0000-000000000004",
        dia=DiaSemana.VIERNES,
        horario="16:00–17:00",
    )
    assert req.comentarios is None
