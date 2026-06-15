"""TDD: Comunicacion schemas tests."""

import uuid
from datetime import datetime, timezone

import pytest
from pydantic import ValidationError

from app.schemas.comunicacion import (
    ApproveRequest,
    CancelRequest,
    ComunicacionFilterParams,
    ComunicacionResponse,
    EnqueueRequest,
    EnqueueResponse,
    PreviewRequest,
    PreviewResponse,
    SampleRecipient,
)


def test_preview_request_valid():
    req = PreviewRequest(
        materia_id=uuid.uuid4(),
        cohorte_id=uuid.uuid4(),
        template_body="Hola {{nombre}}",
        template_asunto="Nota",
    )
    assert req.template_body == "Hola {{nombre}}"


def test_preview_request_extra_forbidden():
    with pytest.raises(ValidationError):
        PreviewRequest(
            materia_id=uuid.uuid4(),
            cohorte_id=uuid.uuid4(),
            template_body="Test",
            extra_field="forbidden",
        )


def test_enqueue_request_valid():
    req = EnqueueRequest(
        preview_token="abc123",
        preview_token_timestamp=datetime.now(timezone.utc).isoformat(),
        materia_id=uuid.uuid4(),
        cohorte_id=uuid.uuid4(),
        template_body="Body",
        template_asunto="Subject",
    )
    assert req.template_body == "Body"


def test_enqueue_request_extra_forbidden():
    with pytest.raises(ValidationError):
        EnqueueRequest(
            preview_token="abc",
            preview_token_timestamp=datetime.now(timezone.utc).isoformat(),
            materia_id=uuid.uuid4(),
            cohorte_id=uuid.uuid4(),
            template_body="Body",
            template_asunto="Subject",
            bad_field="x",
        )


def test_sample_recipient():
    s = SampleRecipient(
        nombre="Ana", apellidos="Lopez",
        asunto="Hola", cuerpo="Mensaje",
    )
    assert s.nombre == "Ana"


def test_comunicacion_response_from_dict():
    now = datetime.now(timezone.utc)
    data = {
        "id": uuid.uuid4(),
        "tenant_id": uuid.uuid4(),
        "lote_id": uuid.uuid4(),
        "destinatario": "a@b.com",
        "asunto": "Test",
        "cuerpo": "Body",
        "estado": "Pendiente",
        "requiere_aprobacion": False,
        "created_at": now,
        "updated_at": now,
    }
    resp = ComunicacionResponse(**data)
    assert resp.estado == "Pendiente"


def test_comunicacion_response_extra_forbidden():
    now = datetime.now(timezone.utc)
    with pytest.raises(ValidationError):
        ComunicacionResponse(
            id=uuid.uuid4(),
            tenant_id=uuid.uuid4(),
            lote_id=uuid.uuid4(),
            destinatario="a@b.com",
            asunto="Test",
            cuerpo="Body",
            estado="Pendiente",
            requiere_aprobacion=False,
            created_at=now,
            updated_at=now,
            bad_extra="x",
        )


def test_filter_params_defaults():
    f = ComunicacionFilterParams()
    assert f.estado is None
    assert f.lote_id is None


def test_approve_request():
    req = ApproveRequest(lote_id=uuid.uuid4())
    assert req.lote_id is not None
    assert req.comunicacion_id is None


def test_cancel_request():
    req = CancelRequest(comunicacion_id=uuid.uuid4())
    assert req.comunicacion_id is not None


def test_enqueue_response():
    resp = EnqueueResponse(lote_id=str(uuid.uuid4()), creados=10)
    assert resp.creados == 10


def test_preview_response():
    resp = PreviewResponse(
        sample=[SampleRecipient(nombre="A", apellidos="B", asunto="S", cuerpo="C")],
        total_estimado=100,
        preview_token="tok123",
        preview_token_timestamp="2026-01-01T00:00:00",
    )
    assert resp.total_estimado == 100
