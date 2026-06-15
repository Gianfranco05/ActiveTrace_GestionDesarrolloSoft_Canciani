import uuid

import pytest
from pydantic import ValidationError

from app.schemas.tareas import (
    ComentarioCreateRequest,
    EstadoTarea,
    TareaCreateRequest,
    TareaDelegateRequest,
    TareaEstadoUpdateRequest,
    TareaUpdateRequest,
)


def test_tarea_create_rejects_missing_fields():
    with pytest.raises(ValidationError):
        TareaCreateRequest()


def test_tarea_create_rejects_extra_fields():
    with pytest.raises(ValidationError):
        TareaCreateRequest(
            asignado_a=uuid.uuid4(),
            descripcion="Test",
            campo_extra="no permitido",
        )


def test_descripcion_min_length():
    with pytest.raises(ValidationError):
        TareaCreateRequest(
            asignado_a=uuid.uuid4(),
            descripcion="",
        )


def test_descripcion_max_length():
    with pytest.raises(ValidationError):
        TareaCreateRequest(
            asignado_a=uuid.uuid4(),
            descripcion="a" * 2001,
        )


def test_estado_invalid_value():
    with pytest.raises(ValidationError):
        TareaEstadoUpdateRequest(estado="InvalidState")


def test_estado_valid_values():
    for val in ["Pendiente", "En progreso", "Resuelta", "Cancelada"]:
        req = TareaEstadoUpdateRequest(estado=val)
        assert req.estado.value == val


def test_comentario_create_rejects_empty():
    with pytest.raises(ValidationError):
        ComentarioCreateRequest(texto="")


def test_comentario_max_length():
    with pytest.raises(ValidationError):
        ComentarioCreateRequest(texto="a" * 5001)


def test_tarea_delegate_requires_asignado_a():
    with pytest.raises(ValidationError):
        TareaDelegateRequest()


def test_tarea_update_partial_fields():
    req = TareaUpdateRequest(descripcion="Nueva desc")
    assert req.descripcion == "Nueva desc"

    req2 = TareaUpdateRequest()
    assert req2.descripcion is None
